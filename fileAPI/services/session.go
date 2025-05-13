package services

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"time"

	"github.com/google/uuid"
)

type Session struct {
	ID           string    `json:"id"`
	CreatedAt    time.Time `json:"createdAt"`
	LastActive   time.Time `json:"lastActive"`
	WorkingDir   string    `json:"workingDir"`
	IsActive     bool      `json:"isActive"`
	ExpiresAt    time.Time `json:"expiresAt"`
	ActivityLog  []string  `json:"activityLog,omitempty"`
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
	session := &Session{
		ID:           id,
		CreatedAt:    now,
		LastActive:   now,
		WorkingDir:   "",
		IsActive:     true,
		ExpiresAt:    now.Add(sm.sessionExpiry),
		ActivityLog:  []string{fmt.Sprintf("%s: Session created", now.Format(time.RFC3339))},
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
	
	if _, exists := sm.sessions[id]; !exists {
		return errors.New("session not found")
	}
	
	delete(sm.sessions, id)
	fmt.Printf("[TERMINAL] Deleted session: %s\n", id)
	return nil
}

func (sm *SessionManager) SetWorkingDirectory(id string, dir string) error {
	sm.mutex.Lock()
	defer sm.mutex.Unlock()
	
	session, exists := sm.sessions[id]
	if !exists || !session.IsActive {
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
	sm.mutex.Lock()
	defer sm.mutex.Unlock()
	
	session, exists := sm.sessions[id]
	if !exists || !session.IsActive {
		return errors.New("session not found or inactive")
	}
	
	now := time.Now()
	logEntry := fmt.Sprintf("%s: %s", now.Format(time.RFC3339), activity)
	session.ActivityLog = append(session.ActivityLog, logEntry)
	
	// Maintain a reasonable log size
	if len(session.ActivityLog) > 100 {
		session.ActivityLog = session.ActivityLog[len(session.ActivityLog)-100:]
	}
	
	return nil
}

func (sm *SessionManager) GetAllSessions() []*Session {
	sm.mutex.RLock()
	defer sm.mutex.RUnlock()
	
	sessions := make([]*Session, 0, len(sm.sessions))
	for _, session := range sm.sessions {
		sessions = append(sessions, session)
	}
	
	return sessions
}
