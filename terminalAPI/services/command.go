package services

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"strings"
	"time"
)

type CommandOutput struct {
	ExitCode   int    `json:"exitCode"`
	Stdout     string `json:"stdout"`
	Stderr     string `json:"stderr"`
	ExecutionTime float64 `json:"executionTime"` // In seconds
	Command    string `json:"command"`
}

type CommandService struct {
	sessionManager *SessionManager
	historyService *HistoryService
}

type CommandRequest struct {
	Command     string            `json:"command"`
	Timeout     int               `json:"timeout,omitempty"` // In seconds, 0 means no timeout
	Environment map[string]string `json:"environment,omitempty"`
}

type BatchCommandRequest struct {
	Commands     []string          `json:"commands"`
	ContinueOnError bool           `json:"continueOnError"`
	Timeout      int               `json:"timeout,omitempty"` // In seconds, per command
	Environment  map[string]string `json:"environment,omitempty"`
}

func NewCommandService(sm *SessionManager, hs *HistoryService) *CommandService {
	return &CommandService{
		sessionManager: sm,
		historyService: hs,
	}
}

func (cs *CommandService) ExecuteCommand(sessionID string, request *CommandRequest) (*CommandOutput, error) {
	session, err := cs.sessionManager.GetSession(sessionID)
	if err != nil {
		return nil, err
	}
	
	if session.WorkingDir == "" {
		return nil, errors.New("working directory not set for session")
	}
	
	// Record in history
	cs.historyService.AddToHistory(sessionID, request.Command)
	
	// Create command context
	ctx := context.Background()
	var cancel context.CancelFunc
	
	if request.Timeout > 0 {
		ctx, cancel = context.WithTimeout(ctx, time.Duration(request.Timeout)*time.Second)
		defer cancel()
	}
	
	// Determine which shell to use based on session environment
	shellPath := "/bin/bash"  // Default shell
	if shell, exists := session.EnvVars["SHELL"]; exists && shell != "" {
		shellPath = shell
	}
	
	// Start with system environment
	env := os.Environ()
	
	// Add session environment variables
	for k, v := range session.EnvVars {
		env = append(env, fmt.Sprintf("%s=%s", k, v))
	}
	
	// Add request-specific environment variables
	for k, v := range request.Environment {
		env = append(env, fmt.Sprintf("%s=%s", k, v))
	}
	
	// Create command
	cmd := exec.CommandContext(ctx, shellPath, "-c", request.Command)
	cmd.Dir = session.WorkingDir
	cmd.Env = env
	
	// Capture stdout and stderr
	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr
	
	// Execute command and measure time
	startTime := time.Now()
	err = cmd.Run()
	executionTime := time.Since(startTime).Seconds()
	
	// Create result
	result := &CommandOutput{
		Stdout:     stdout.String(),
		Stderr:     stderr.String(),
		Command:    request.Command,
		ExecutionTime: executionTime,
	}
	
	if err != nil {
		if exitError, ok := err.(*exec.ExitError); ok {
			result.ExitCode = exitError.ExitCode()
		} else {
			result.ExitCode = -1
			result.Stderr += "\n" + err.Error()
		}
	} else {
		result.ExitCode = 0
	}
	
	// Log activity
	cs.sessionManager.LogActivity(sessionID, fmt.Sprintf("Executed command: %s (exit code: %d)", 
		request.Command, result.ExitCode))
	
	fmt.Printf("[TERMINAL] Session %s: Command '%s' completed with exit code %d\n", 
		sessionID, request.Command, result.ExitCode)
	
	return result, nil
}

func (cs *CommandService) ExecuteBatchCommands(sessionID string, request *BatchCommandRequest) ([]*CommandOutput, error) {
	session, err := cs.sessionManager.GetSession(sessionID)
	if err != nil {
		return nil, err
	}
	
	if session.WorkingDir == "" {
		return nil, errors.New("working directory not set for session")
	}
	
	results := make([]*CommandOutput, 0, len(request.Commands))
	
	for _, cmd := range request.Commands {
		cmdReq := &CommandRequest{
			Command:     cmd,
			Timeout:     request.Timeout,
			Environment: request.Environment,
		}
		
		output, err := cs.ExecuteCommand(sessionID, cmdReq)
		if err != nil {
			if !request.ContinueOnError {
				return results, err
			}
		}
		
		results = append(results, output)
		
		// Stop batch execution if a command fails and continueOnError is false
		if output.ExitCode != 0 && !request.ContinueOnError {
			break
		}
	}
	
	return results, nil
}

// Parse a command string into command and arguments
func parseCommand(command string) []string {
	// This is a basic implementation. A more robust solution would handle
	// quotes, escapes, etc., but this works for simple cases.
	return strings.Fields(command)
}
