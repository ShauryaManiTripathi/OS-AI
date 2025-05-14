package services

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

// CommandRunner provides functionality to run commands via the proper shell
type CommandRunner struct {
	// Cache of valid shells to avoid repeated filesystem checks
	validShells map[string]bool
}

// NewCommandRunner creates a new command runner instance
func NewCommandRunner() *CommandRunner {
	return &CommandRunner{
		validShells: make(map[string]bool),
	}
}

// GetDefaultShell returns the default shell to use
func (cr *CommandRunner) GetDefaultShell() string {
	// Try to get system default shell from SHELL environment variable
	if shell := os.Getenv("SHELL"); shell != "" {
		return shell
	}
	
	// Fallback to bash on Unix systems
	return "/bin/bash"
}

// IsValidShell checks if a shell path exists and is executable
func (cr *CommandRunner) IsValidShell(shellPath string) bool {
	// Check cache first
	if valid, exists := cr.validShells[shellPath]; exists {
		return valid
	}
	
	// Validate shell path
	if shellPath == "" || !strings.HasPrefix(shellPath, "/") {
		cr.validShells[shellPath] = false
		return false
	}
	
	// Common valid shells
	commonShells := []string{
		"/bin/bash", "/bin/sh", "/bin/zsh", 
		"/usr/bin/bash", "/usr/bin/zsh", 
		"/usr/local/bin/bash", "/usr/local/bin/zsh",
	}
	
	for _, shell := range commonShells {
		if shellPath == shell {
			cr.validShells[shellPath] = true
			return true
		}
	}
	
	// For other paths, check if they exist and are executable
	info, err := os.Stat(shellPath)
	if err != nil {
		cr.validShells[shellPath] = false
		return false
	}
	
	// Check if it's executable and a regular file
	valid := (info.Mode().IsRegular() && info.Mode()&0111 != 0)
	cr.validShells[shellPath] = valid
	return valid
}

// GetShellCommand returns the appropriate shell command to run a command string
func (cr *CommandRunner) GetShellCommand(shellPath string, command string) (*exec.Cmd, error) {
	if !cr.IsValidShell(shellPath) {
		return nil, fmt.Errorf("invalid shell: %s", shellPath)
	}
	
	// Get shell name for determining args
	shellName := filepath.Base(shellPath)
	
	var cmd *exec.Cmd
	switch shellName {
	case "bash", "sh", "zsh":
		cmd = exec.Command(shellPath, "-c", command)
	default:
		return nil, fmt.Errorf("unsupported shell: %s", shellName)
	}
	
	return cmd, nil
}

// PrepareCommand creates and configures a command with proper shell, environment, and working directory
func (cr *CommandRunner) PrepareCommand(command string, shellPath string, workingDir string, env map[string]string) (*exec.Cmd, error) {
	if shellPath == "" {
		shellPath = cr.GetDefaultShell()
	}
	
	cmd, err := cr.GetShellCommand(shellPath, command)
	if err != nil {
		return nil, err
	}
	
	// Set working directory
	if workingDir != "" {
		cmd.Dir = workingDir
	}
	
	// Start with system environment
	systemEnv := os.Environ()
	
	// Add custom environment variables
	if len(env) > 0 {
		for k, v := range env {
			systemEnv = append(systemEnv, fmt.Sprintf("%s=%s", k, v))
		}
	}
	
	cmd.Env = systemEnv
	
	return cmd, nil
}
