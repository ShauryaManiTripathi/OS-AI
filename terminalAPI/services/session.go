package services

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"github.com/google/uuid"
)

type Session struct {
	ID              string            `json:"id"`
	CreatedAt       time.Time         `json:"createdAt"`
	LastActive      time.Time         `json:"lastActive"`
	WorkingDir      string            `json:"workingDir"`
	IsActive        bool              `json:"isActive"`
	ExpiresAt       time.Time         `json:"expiresAt"`
	ActivityLog     []string          `json:"activityLog,omitempty"`
	EnvVars         map[string]string `json:"envVars"`
	RunningProcesses map[string]*Process `json:"-"` // Don't expose in JSON
	Lock            sync.Mutex        `json:"-"`
}

type SessionManager struct {
	sessions      map[string]*Session
	mutex         sync.RWMutex
	sessionExpiry time.Duration
	cleanupTicker *time.Ticker
}

func NewSessionManager() *SessionManager {
	sm := &SessionManager{
		sessions:      make(map[string]*Session),
		sessionExpiry: 24 * time.Hour, // Default 24 hour expiry
	}
	
	// Start cleanup routine
	sm.cleanupTicker = time.NewTicker(10 * time.Minute)
	go sm.cleanupExpiredSessions()
	
	return sm
}

func (sm *SessionManager) cleanupExpiredSessions() {
	for range sm.cleanupTicker.C {
		sm.mutex.Lock()
		now := time.Now()
		for id, session := range sm.sessions {
			if session.ExpiresAt.Before(now) {
				// Terminate any running processes
				for _, proc := range session.RunningProcesses {
					if proc != nil && proc.Cmd != nil && proc.Cmd.Process != nil {
						proc.Terminate()
					}
				}
				delete(sm.sessions, id)
				fmt.Printf("[TERMINAL] Expired inactive session: %s\n", id)
			}
		}
		sm.mutex.Unlock()
	}
}

func (sm *SessionManager) CreateSession() (*Session, error) {
	sm.mutex.Lock()
	defer sm.mutex.Unlock()
	
	id := uuid.New().String()
	now := time.Now()
	
	// Get system default shell
	shell := os.Getenv("SHELL")
	if shell == "" {
		// Default to bash on Unix, cmd on Windows
		if os.PathSeparator == '/' {
			shell = "/bin/bash"
		} else {
			shell = "cmd.exe"
		}
	}
	
	session := &Session{
		ID:              id,
		CreatedAt:       now,
		LastActive:      now,
		WorkingDir:      "",
		IsActive:        true,
		ExpiresAt:       now.Add(sm.sessionExpiry),
		ActivityLog:     []string{fmt.Sprintf("%s: Session created", now.Format(time.RFC3339))},
		EnvVars:         map[string]string{"SHELL": shell},
		RunningProcesses: make(map[string]*Process),
	}
	
	sm.sessions[id] = session
	fmt.Printf("[TERMINAL] Created new session: %s\n", id)
	return session, nil
}

func (sm *SessionManager) GetSession(id string) (*Session, error) {
	sm.mutex.RLock()
	defer sm.mutex.RUnlock()
	
	session, exists := sm.sessions[id]
	if !exists || !session.IsActive {
		return nil, errors.New("session not found or inactive")
	}
	
	// Update last active time and extend expiry
	now := time.Now()
	session.LastActive = now
	session.ExpiresAt = now.Add(sm.sessionExpiry)
	return session, nil
}

func (sm *SessionManager) DeleteSession(id string) error {
	sm.mutex.Lock()
	defer sm.mutex.Unlock()
	
	session, exists := sm.sessions[id]
	if !exists {
		return errors.New("session not found")
	}
	
	// Terminate all running processes
	for _, proc := range session.RunningProcesses {
		if proc != nil && proc.Cmd != nil && proc.Cmd.Process != nil {
			proc.Terminate()
		}
	}
	
	delete(sm.sessions, id)
	fmt.Printf("[TERMINAL] Deleted session: %s\n", id)
	return nil
}

func (sm *SessionManager) SetWorkingDirectory(id string, dir string) error {
	sm.mutex.Lock()
	defer sm.mutex.Unlock()
	
	session, exists := sm.sessions[id]
	if (!exists || !session.IsActive) {
		return errors.New("session not found or inactive")
	}
	
	// Check if directory exists
	if _, err := os.Stat(dir); os.IsNotExist(err) {
		return errors.New("directory does not exist")
	}
	
	// Get absolute path
	absPath, err := filepath.Abs(dir)
	if err != nil {
		return err
	}
	
	now := time.Now()
	session.WorkingDir = absPath
	session.LastActive = now
	session.ExpiresAt = now.Add(sm.sessionExpiry)
	session.ActivityLog = append(session.ActivityLog, fmt.Sprintf("%s: Set working directory to %s", 
		now.Format(time.RFC3339), absPath))
	
	fmt.Printf("[TERMINAL] Session %s: Set working directory to %s\n", id, absPath)
	return nil
}

func (sm *SessionManager) LogActivity(id string, activity string) error {
	// Use separate locks to avoid deadlocks
	sm.mutex.RLock()
	session, exists := sm.sessions[id]
	sm.mutex.RUnlock()
	
	if !exists || !session.IsActive {
		return errors.New("session not found or inactive")
	}
	
	now := time.Now()
	logEntry := fmt.Sprintf("%s: %s", now.Format(time.RFC3339), activity)
	
	// Lock only while updating activity log
	session.Lock.Lock()
	session.ActivityLog = append(session.ActivityLog, logEntry)
	
	// Maintain a reasonable log size
	if len(session.ActivityLog) > 100 {
		session.ActivityLog = session.ActivityLog[len(session.ActivityLog)-100:]
	}
	session.Lock.Unlock()
	
	return nil
}

func (sm *SessionManager) GetAllSessions() []*Session {
	sm.mutex.RLock()
	defer sm.mutex.RUnlock()
	
	sessions := make([]*Session, 0, len(sm.sessions))
	for _, session := range sm.sessions {
		sessionCopy := *session // Create a copy to avoid exposing running processes
		sessionCopy.RunningProcesses = nil
		sessions = append(sessions, &sessionCopy)
	}
	
	return sessions
}

func (sm *SessionManager) SetEnvVar(id string, key string, value string) error {
	sm.mutex.Lock()
	defer sm.mutex.Unlock()
	
	session, exists := sm.sessions[id]
	if !exists || !session.IsActive {
		return errors.New("session not found or inactive")
	}
	
	session.EnvVars[key] = value
	sm.LogActivity(id, fmt.Sprintf("Set environment variable: %s=%s", key, value))
	return nil
}

func (sm *SessionManager) GetEnvVars(id string) (map[string]string, error) {
	sm.mutex.RLock()
	defer sm.mutex.RUnlock()
	
	session, exists := sm.sessions[id]
	if !exists || !session.IsActive {
		return nil, errors.New("session not found or inactive")
	}
	
	// Return a copy to prevent modification
	envVars := make(map[string]string)
	for k, v := range session.EnvVars {
		envVars[k] = v
	}
	
	return envVars, nil
}

func (sm *SessionManager) UnsetEnvVar(id string, key string) error {
	sm.mutex.Lock()
	defer sm.mutex.Unlock()
	
	session, exists := sm.sessions[id]
	if !exists || !session.IsActive {
		return errors.New("session not found or inactive")
	}
	
	if _, exists := session.EnvVars[key]; exists {
		delete(session.EnvVars, key)
		sm.LogActivity(id, fmt.Sprintf("Unset environment variable: %s", key))
	}
	
	return nil
}

// Register a running process with the session
func (sm *SessionManager) RegisterProcess(sessionID string, processID string, process *Process) error {
	sm.mutex.Lock()
	defer sm.mutex.Unlock()
	
	session, exists := sm.sessions[sessionID]
	if !exists || !session.IsActive {
		return errors.New("session not found or inactive")
	}
	
	session.RunningProcesses[processID] = process
	return nil
}

// Unregister a process when it completes
func (sm *SessionManager) UnregisterProcess(sessionID string, processID string) error {
	sm.mutex.Lock()
	defer sm.mutex.Unlock()
	
	session, exists := sm.sessions[sessionID]
	if !exists {
		return errors.New("session not found")
	}
	
	delete(session.RunningProcesses, processID)
	return nil
}

// Get a process by ID
func (sm *SessionManager) GetProcess(sessionID string, processID string) (*Process, error) {
	sm.mutex.RLock()
	defer sm.mutex.RUnlock()
	
	session, exists := sm.sessions[sessionID]
	if !exists || !session.IsActive {
		return nil, errors.New("session not found or inactive")
	}
	
	process, exists := session.RunningProcesses[processID]
	if !exists {
		return nil, errors.New("process not found")
	}
	
	return process, nil
}

// List all running processes
func (sm *SessionManager) ListProcesses(sessionID string) (map[string]*ProcessInfo, error) {
	sm.mutex.RLock()
	defer sm.mutex.RUnlock()
	
	session, exists := sm.sessions[sessionID]
	if !exists || !session.IsActive {
		return nil, errors.New("session not found or inactive")
	}
	
	processInfos := make(map[string]*ProcessInfo)
	for id, process := range session.RunningProcesses {
		if process != nil {
			processInfos[id] = &ProcessInfo{
				ID:         id,
				Command:    process.Command,
				StartTime:  process.StartTime,
				IsRunning:  process.IsRunning(),
				ExitCode:   process.ExitCode,
				PID:        process.PID,
			}
		}
	}
	
	return processInfos, nil
}

// Helper function to validate shell paths
func isValidShellPath(path string) bool {
    // Basic path validation
    if path == "" || !strings.HasPrefix(path, "/") {
        return false
    }
    
    // Check if common valid shells
    commonShells := []string{
        "/bin/bash", "/bin/sh", "/bin/zsh", 
        "/usr/bin/bash", "/usr/bin/zsh", 
        "/usr/local/bin/bash", "/usr/local/bin/zsh",
    }
    
    for _, shell := range commonShells {
        if path == shell {
            return true
        }
    }
    
    // For other paths, check if they exist and are executable
    info, err := os.Stat(path)
    if err != nil {
        return false
    }
    
    // Check if it's executable
    return info.Mode()&0111 != 0
}
