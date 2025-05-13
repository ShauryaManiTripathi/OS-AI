package services

import (
	"fmt"
	"strings"
	"sync"
	"time"
)

type HistoryEntry struct {
	Command   string    `json:"command"`
	Timestamp time.Time `json:"timestamp"`
}

type HistoryService struct {
	history map[string][]HistoryEntry
	mutex   sync.RWMutex
	maxSize int
}

func NewHistoryService(maxSize int) *HistoryService {
	if maxSize <= 0 {
		maxSize = 1000 // Default history size
	}
	
	return &HistoryService{
		history: make(map[string][]HistoryEntry),
		maxSize: maxSize,
	}
}

func (hs *HistoryService) AddToHistory(sessionID string, command string) {
	hs.mutex.Lock()
	defer hs.mutex.Unlock()
	
	entry := HistoryEntry{
		Command:   command,
		Timestamp: time.Now(),
	}
	
	// Initialize history for this session if it doesn't exist
	if _, exists := hs.history[sessionID]; !exists {
		hs.history[sessionID] = make([]HistoryEntry, 0)
	}
	
	// Add entry to history
	hs.history[sessionID] = append(hs.history[sessionID], entry)
	
	// Trim history if it exceeds max size
	if len(hs.history[sessionID]) > hs.maxSize {
		hs.history[sessionID] = hs.history[sessionID][len(hs.history[sessionID])-hs.maxSize:]
	}
}

func (hs *HistoryService) GetHistory(sessionID string, limit int) ([]HistoryEntry, error) {
	hs.mutex.RLock()
	defer hs.mutex.RUnlock()
	
	sessionHistory, exists := hs.history[sessionID]
	if !exists {
		return []HistoryEntry{}, nil
	}
	
	// If limit is 0 or negative, return all history
	if limit <= 0 {
		// Return a copy to prevent modification
		result := make([]HistoryEntry, len(sessionHistory))
		copy(result, sessionHistory)
		return result, nil
	}
	
	// Apply limit
	start := 0
	if len(sessionHistory) > limit {
		start = len(sessionHistory) - limit
	}
	
	result := make([]HistoryEntry, len(sessionHistory[start:]))
	copy(result, sessionHistory[start:])
	
	fmt.Printf("[TERMINAL] Retrieved %d history entries for session %s\n", len(result), sessionID)
	return result, nil
}

func (hs *HistoryService) SearchHistory(sessionID string, query string) ([]HistoryEntry, error) {
	hs.mutex.RLock()
	defer hs.mutex.RUnlock()
	
	sessionHistory, exists := hs.history[sessionID]
	if !exists {
		return []HistoryEntry{}, nil
	}
	
	var results []HistoryEntry
	for _, entry := range sessionHistory {
		if strings.Contains(entry.Command, query) {
			results = append(results, entry)
		}
	}
	
	fmt.Printf("[TERMINAL] Found %d history entries matching '%s' for session %s\n", 
		len(results), query, sessionID)
	return results, nil
}

func (hs *HistoryService) ClearHistory(sessionID string) error {
	hs.mutex.Lock()
	defer hs.mutex.Unlock()
	
	hs.history[sessionID] = make([]HistoryEntry, 0)
	fmt.Printf("[TERMINAL] Cleared history for session %s\n", sessionID)
	return nil
}
