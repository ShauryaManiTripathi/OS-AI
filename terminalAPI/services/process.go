package services

import (
	"bufio"
	"context"
	"errors"
	"fmt"
	"io"
	"os"
	"os/exec"
	"strings"
	"sync"
	"syscall"
	"time"

	"github.com/google/uuid"
)

type Process struct {
	ID          string       `json:"id"`
	Command     string       `json:"command"`
	StartTime   time.Time    `json:"startTime"`
	Cmd         *exec.Cmd    `json:"-"`
	StdinPipe   io.WriteCloser `json:"-"`
	StdoutPipe  io.ReadCloser  `json:"-"`
	StderrPipe  io.ReadCloser  `json:"-"`
	OutputBuffer *OutputBuffer `json:"-"`
	PID         int          `json:"pid"`
	ExitCode    int          `json:"exitCode"`
	Completed   bool         `json:"completed"`
	Lock        sync.Mutex   `json:"-"`
	Done        chan struct{} `json:"-"`
}

type ProcessInfo struct {
	ID         string    `json:"id"`
	Command    string    `json:"command"`
	StartTime  time.Time `json:"startTime"`
	IsRunning  bool      `json:"isRunning"`
	ExitCode   int       `json:"exitCode,omitempty"`
	PID        int       `json:"pid,omitempty"`
}

type OutputBuffer struct {
	Stdout     []string `json:"stdout"`
	Stderr     []string `json:"stderr"`
	MaxLines   int      `json:"-"`
	Lock       sync.Mutex `json:"-"`
	// For real-time streaming
	StdoutChan  chan string  `json:"-"`
	StderrChan  chan string  `json:"-"`
}

type ProcessService struct {
	sessionManager *SessionManager
	historyService *HistoryService
}

func NewProcessService(sm *SessionManager, hs *HistoryService) *ProcessService {
	return &ProcessService{
		sessionManager: sm,
		historyService: hs,
	}
}

func (ps *ProcessService) StartProcess(sessionID string, request *CommandRequest) (*ProcessInfo, error) {
	session, err := ps.sessionManager.GetSession(sessionID)
	if err != nil {
		return nil, err
	}
	
	if session.WorkingDir == "" {
		return nil, errors.New("working directory not set for session")
	}
	
	// Record in history
	ps.historyService.AddToHistory(sessionID, request.Command)
	
	// Create command context
	var ctx context.Context
	var cancel context.CancelFunc
	
	if request.Timeout > 0 {
		ctx, cancel = context.WithTimeout(context.Background(), time.Duration(request.Timeout)*time.Second)
	} else {
		ctx, cancel = context.WithCancel(context.Background())
	}
	
	// Determine which shell to use based on session environment
	shellPath := "/bin/bash"  // Default shell
	if shell, exists := session.EnvVars["SHELL"]; exists && shell != "" {
		// Verify the shell exists and is executable
		if _, err := os.Stat(shell); err == nil {
			shellPath = shell
		} else {
			// Log warning but continue with default shell
			fmt.Printf("[WARNING] Session %s: Shell %s not found, using %s instead\n", 
				sessionID, shell, shellPath)
		}
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
	
	// Get pipes for stdin, stdout, stderr
	stdinPipe, err := cmd.StdinPipe()
	if err != nil {
		cancel()
		return nil, err
	}
	
	stdoutPipe, err := cmd.StdoutPipe()
	if err != nil {
		cancel()
		return nil, err
	}
	
	stderrPipe, err := cmd.StderrPipe()
	if err != nil {
		cancel()
		return nil, err
	}
	
	// Create output buffer
	outputBuffer := &OutputBuffer{
		MaxLines:   10000, // Maximum lines to keep in buffer
		StdoutChan: make(chan string, 100),
		StderrChan: make(chan string, 100),
	}
	
	// Create process object
	processID := uuid.New().String()
	process := &Process{
		ID:          processID,
		Command:     request.Command,
		StartTime:   time.Now(),
		Cmd:         cmd,
		StdinPipe:   stdinPipe,
		StdoutPipe:  stdoutPipe,
		StderrPipe:  stderrPipe,
		OutputBuffer: outputBuffer,
		Completed:   false,
		Done:        make(chan struct{}),
	}
	
	// Start the command
	if err := cmd.Start(); err != nil {
		cancel()
		return nil, err
	}
	
	process.PID = cmd.Process.Pid
	
	// Register process with session
	if err := ps.sessionManager.RegisterProcess(sessionID, processID, process); err != nil {
		cmd.Process.Kill()
		cancel()
		return nil, err
	}
	
	// Start goroutines to collect output
	go ps.collectOutput(stdoutPipe, outputBuffer.StdoutChan, &outputBuffer.Stdout, outputBuffer)
	go ps.collectOutput(stderrPipe, outputBuffer.StderrChan, &outputBuffer.Stderr, outputBuffer)
	
	// Wait for process to complete
	go func() {
		defer close(process.Done)
		defer cancel()
		
		err := cmd.Wait()
		process.Lock.Lock()
		process.Completed = true
		if err != nil {
			if exitErr, ok := err.(*exec.ExitError); ok {
				process.ExitCode = exitErr.ExitCode()
			} else {
				process.ExitCode = -1
			}
		} else {
			process.ExitCode = 0
		}
		process.Lock.Unlock()
		
		ps.sessionManager.LogActivity(sessionID, fmt.Sprintf("Process completed: %s (exit code: %d)", 
			request.Command, process.ExitCode))
		fmt.Printf("[TERMINAL] Session %s: Process '%s' (ID: %s) completed with exit code %d\n", 
			sessionID, request.Command, processID, process.ExitCode)
			
			// Give some time for any remaining output to be processed before closing channels
			time.Sleep(100 * time.Millisecond)
			
			// Close output channels
			close(outputBuffer.StdoutChan)
			close(outputBuffer.StderrChan)
	}()
	
	ps.sessionManager.LogActivity(sessionID, fmt.Sprintf("Started process: %s (PID: %d, ID: %s)", 
		request.Command, process.PID, processID))
	fmt.Printf("[TERMINAL] Session %s: Started process '%s' with PID %d (ID: %s)\n", 
		sessionID, request.Command, process.PID, processID)
	
	return &ProcessInfo{
		ID:        processID,
		Command:   request.Command,
		StartTime: process.StartTime,
		IsRunning: true,
		PID:       process.PID,
	}, nil
}

func (ps *ProcessService) collectOutput(pipe io.ReadCloser, channel chan string, buffer *[]string, outputBuffer *OutputBuffer) {
	scanner := bufio.NewScanner(pipe)
	for scanner.Scan() {
		line := scanner.Text()
		
		// Send line to channel for real-time consumers - safely handle closed channel
		select {
		case channel <- line:
			// Successfully sent
		default:
			// Channel is either full or closed, just continue without sending
		}
		
		// Add to buffer for later retrieval
		outputBuffer.Lock.Lock()
		*buffer = append(*buffer, line)
		
		// Trim buffer if it exceeds max lines
		if len(*buffer) > outputBuffer.MaxLines {
			*buffer = (*buffer)[len(*buffer)-outputBuffer.MaxLines:]
		}
		outputBuffer.Lock.Unlock()
	}
}

func (ps *ProcessService) SendInput(sessionID string, processID string, input string) error {
	process, err := ps.sessionManager.GetProcess(sessionID, processID)
	if err != nil {
		return err
	}
	
	if process.StdinPipe == nil {
		return errors.New("process stdin pipe is not available")
	}
	
	// Add a newline if not present
	if !strings.HasSuffix(input, "\n") {
		input += "\n"
	}
	
	_, err = io.WriteString(process.StdinPipe, input)
	if err != nil {
		return err
	}
	
	ps.sessionManager.LogActivity(sessionID, fmt.Sprintf("Sent input to process %s", processID))
	fmt.Printf("[TERMINAL] Session %s: Sent input to process %s\n", sessionID, processID)
	
	return nil
}

func (ps *ProcessService) GetOutput(sessionID string, processID string) (*OutputBuffer, error) {
	process, err := ps.sessionManager.GetProcess(sessionID, processID)
	if err != nil {
		return nil, err
	}
	
	if process.OutputBuffer == nil {
		return nil, errors.New("output buffer not available")
	}
	
	// Return a copy of the output buffer
	process.OutputBuffer.Lock.Lock()
	outputCopy := &OutputBuffer{
		Stdout: make([]string, len(process.OutputBuffer.Stdout)),
		Stderr: make([]string, len(process.OutputBuffer.Stderr)),
	}
	copy(outputCopy.Stdout, process.OutputBuffer.Stdout)
	copy(outputCopy.Stderr, process.OutputBuffer.Stderr)
	process.OutputBuffer.Lock.Unlock()
	
	ps.sessionManager.LogActivity(sessionID, fmt.Sprintf("Retrieved output from process %s", processID))
	fmt.Printf("[TERMINAL] Session %s: Retrieved output from process %s\n", sessionID, processID)
	
	return outputCopy, nil
}

func (ps *ProcessService) SignalProcess(sessionID string, processID string, signal string) error {
	process, err := ps.sessionManager.GetProcess(sessionID, processID)
	if err != nil {
		return err
	}
	
	if process.Cmd == nil || process.Cmd.Process == nil {
		return errors.New("process is not running")
	}
	
	var sig syscall.Signal
	switch signal {
	case "SIGTERM":
		sig = syscall.SIGTERM
	case "SIGKILL":
		sig = syscall.SIGKILL
	case "SIGINT":
		sig = syscall.SIGINT
	case "SIGHUP":
		sig = syscall.SIGHUP
	default:
		return fmt.Errorf("unsupported signal: %s", signal)
	}
	
	err = process.Cmd.Process.Signal(sig)
	if err != nil {
		return err
	}
	
	ps.sessionManager.LogActivity(sessionID, fmt.Sprintf("Sent signal %s to process %s", signal, processID))
	fmt.Printf("[TERMINAL] Session %s: Sent signal %s to process %s\n", sessionID, signal, processID)
	
	return nil
}

func (ps *ProcessService) ListProcesses(sessionID string) (map[string]*ProcessInfo, error) {
	return ps.sessionManager.ListProcesses(sessionID)
}

// IsRunning checks if a process is still running
func (p *Process) IsRunning() bool {
	p.Lock.Lock()
	defer p.Lock.Unlock()
	return !p.Completed
}

// Terminate kills the process
func (p *Process) Terminate() error {
	p.Lock.Lock()
	if p.Completed {
		p.Lock.Unlock()
		return nil // Already completed
	}
	p.Lock.Unlock()
	
	if p.Cmd != nil && p.Cmd.Process != nil {
		return p.Cmd.Process.Kill()
	}
	return nil
}

// WaitForCompletion waits for the process to complete
func (p *Process) WaitForCompletion(timeout time.Duration) (int, error) {
	if p.Completed {
		return p.ExitCode, nil
	}
	
	timer := time.NewTimer(timeout)
	defer timer.Stop()
	
	select {
	case <-p.Done:
		return p.ExitCode, nil
	case <-timer.C:
		return 0, errors.New("timeout waiting for process to complete")
	}
}
