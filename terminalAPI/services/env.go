package services

import (
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
	err := es.sessionManager.SetEnvVar(sessionID, key, value)
	if err != nil {
		return err
	}
	
	fmt.Printf("[TERMINAL] Session %s: Set environment variable %s=%s\n", sessionID, key, value)
	return nil
}

func (es *EnvService) GetEnvVars(sessionID string) (map[string]string, error) {
	envVars, err := es.sessionManager.GetEnvVars(sessionID)
	if err != nil {
		return nil, err
	}
	
	fmt.Printf("[TERMINAL] Session %s: Retrieved environment variables\n", sessionID)
	return envVars, nil
}

func (es *EnvService) UnsetEnvVar(sessionID string, key string) error {
	err := es.sessionManager.UnsetEnvVar(sessionID, key)
	if err != nil {
		return err
	}
	
	fmt.Printf("[TERMINAL] Session %s: Unset environment variable %s\n", sessionID, key)
	return nil
}

func (es *EnvService) SetBatchEnvVars(sessionID string, envVars map[string]string) error {
	for key, value := range envVars {
		if err := es.sessionManager.SetEnvVar(sessionID, key, value); err != nil {
			return err
		}
	}
	
	fmt.Printf("[TERMINAL] Session %s: Set %d environment variables\n", sessionID, len(envVars))
	return nil
}
