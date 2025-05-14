package services

import (
	"errors"
	"fmt"
)

type EnvService struct {
	sessionManager *SessionManager
}

func NewEnvService(sm *SessionManager) *EnvService {
	return &EnvService{
		sessionManager: sm,
	}
}

func (es *EnvService) SetEnvVar(sessionID string, key string, value string) error {
	// Direct access to session with minimal locking
	es.sessionManager.mutex.RLock()
	session, exists := es.sessionManager.sessions[sessionID]
	es.sessionManager.mutex.RUnlock()
	
	if (!exists) {
		return errors.New("session not found")
	}
	
	// Simple operation with minimal locking
	session.Lock.Lock()
	if session.EnvVars == nil {
		session.EnvVars = make(map[string]string)
	}
	session.EnvVars[key] = value
	session.Lock.Unlock()
	
	// Skip logging to avoid deadlocks
	fmt.Printf("[TERMINAL] Session %s: Set environment variable %s=%s\n", sessionID, key, value)
	return nil
}

func (es *EnvService) GetEnvVars(sessionID string) (map[string]string, error) {
	// Direct access with minimal locking
	es.sessionManager.mutex.RLock()
	session, exists := es.sessionManager.sessions[sessionID]
	es.sessionManager.mutex.RUnlock()
	
	if (!exists) {
		return nil, errors.New("session not found")
	}
	
	// Get a snapshot of environment variables
	session.Lock.Lock()
	result := make(map[string]string)
	for k, v := range session.EnvVars {
		result[k] = v
	}
	session.Lock.Unlock()
	
	fmt.Printf("[TERMINAL] Session %s: Retrieved environment variables\n", sessionID)
	return result, nil
}

func (es *EnvService) UnsetEnvVar(sessionID string, key string) error {
	// Very simple implementation that just removes the key directly
	es.sessionManager.mutex.RLock()
	session, exists := es.sessionManager.sessions[sessionID]
	es.sessionManager.mutex.RUnlock()
	
	if !exists {
		return errors.New("session not found")
	}
	
	// Just delete the key - no complex locking or checks
	session.Lock.Lock()
	if session.EnvVars != nil {
		// Delete regardless of whether key exists
		delete(session.EnvVars, key)
	}
	session.Lock.Unlock()
	
	fmt.Printf("[TERMINAL] Session %s: Unset environment variable %s\n", sessionID, key)
	return nil
}

func (es *EnvService) SetBatchEnvVars(sessionID string, envVars map[string]string) error {
	// Direct access with minimal locking
	es.sessionManager.mutex.RLock()
	session, exists := es.sessionManager.sessions[sessionID]
	es.sessionManager.mutex.RUnlock()
	
	if (!exists) {
		return errors.New("session not found")
	}
	
	// Single lock for the entire batch update
	session.Lock.Lock()
	if session.EnvVars == nil {
		session.EnvVars = make(map[string]string)
	}
	
	// Fix the syntax error in the range loop
	for key, value := range envVars {
		session.EnvVars[key] = value
	}
	session.Lock.Unlock()
	
	fmt.Printf("[TERMINAL] Session %s: Set %d environment variables\n", sessionID, len(envVars))
	return nil
}
