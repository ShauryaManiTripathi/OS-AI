package services

import (
	"fmt"
	"io/ioutil"
	"os"
	"path/filepath"
	"strings"
)

type DirectoryEntry struct {
	Name      string    `json:"name"`
	Path      string    `json:"path"`
	Size      int64     `json:"size,omitempty"`
	IsDir     bool      `json:"isDir"`
	Children  []DirectoryEntry `json:"children,omitempty"`
}

type DirectoryService struct {
	sessionManager *SessionManager
}

func NewDirectoryService(sm *SessionManager) *DirectoryService {
	return &DirectoryService{
		sessionManager: sm,
	}
}

func (ds *DirectoryService) ListDirectories(sessionID string, relativePath string) ([]string, error) {
	session, err := ds.sessionManager.GetSession(sessionID)
	if err != nil {
		return nil, err
	}
	
	fullPath := filepath.Join(session.WorkingDir, relativePath)
	
	files, err := ioutil.ReadDir(fullPath)
	if err != nil {
		return nil, err
	}
	
	var dirs []string
	for _, file := range files {
		if file.IsDir() {
			dirs = append(dirs, file.Name())
		}
	}
	
	ds.sessionManager.LogActivity(sessionID, fmt.Sprintf("Listed %d directories in %s", len(dirs), relativePath))
	fmt.Printf("[TERMINAL] Session %s: Listed %d directories in %s\n", sessionID, len(dirs), relativePath)
	return dirs, nil
}

func (ds *DirectoryService) CreateDirectory(sessionID string, relativePath string) error {
	session, err := ds.sessionManager.GetSession(sessionID)
	if err != nil {
		return err
	}
	
	fullPath := filepath.Join(session.WorkingDir, relativePath)
	
	if err := os.MkdirAll(fullPath, 0755); err != nil {
		return err
	}
	
	ds.sessionManager.LogActivity(sessionID, fmt.Sprintf("Created directory %s", relativePath))
	fmt.Printf("[TERMINAL] Session %s: Created directory %s\n", sessionID, relativePath)
	return nil
}

func (ds *DirectoryService) DeleteDirectory(sessionID string, relativePath string) error {
	session, err := ds.sessionManager.GetSession(sessionID)
	if err != nil {
		return err
	}
	
	fullPath := filepath.Join(session.WorkingDir, relativePath)
	
	if err := os.RemoveAll(fullPath); err != nil {
		return err
	}
	
	ds.sessionManager.LogActivity(sessionID, fmt.Sprintf("Deleted directory %s", relativePath))
	fmt.Printf("[TERMINAL] Session %s: Deleted directory %s\n", sessionID, relativePath)
	return nil
}

func (ds *DirectoryService) GetDirectoryTree(sessionID string, relativePath string, maxDepth int) ([]DirectoryEntry, error) {
	session, err := ds.sessionManager.GetSession(sessionID)
	if err != nil {
		return nil, err
	}
	
	fullPath := filepath.Join(session.WorkingDir, relativePath)
	
	entries, err := ds.buildDirectoryTree(fullPath, relativePath, 0, maxDepth)
	if err != nil {
		return nil, err
	}
	
	ds.sessionManager.LogActivity(sessionID, fmt.Sprintf("Generated directory tree for %s", relativePath))
	fmt.Printf("[TERMINAL] Session %s: Generated directory tree for %s\n", sessionID, relativePath)
	return entries, nil
}

func (ds *DirectoryService) buildDirectoryTree(fullPath, relativePath string, currentDepth, maxDepth int) ([]DirectoryEntry, error) {
	if maxDepth > 0 && currentDepth >= maxDepth {
		return nil, nil
	}
	
	files, err := ioutil.ReadDir(fullPath)
	if err != nil {
		return nil, err
	}
	
	entries := make([]DirectoryEntry, 0, len(files))
	for _, file := range files {
		entry := DirectoryEntry{
			Name:  file.Name(),
			Path:  filepath.Join(relativePath, file.Name()),
			IsDir: file.IsDir(),
		}
		
		if !file.IsDir() {
			entry.Size = file.Size()
		} else if currentDepth+1 < maxDepth || maxDepth <= 0 {
			// Recursively build children for directories if within depth limit
			childPath := filepath.Join(fullPath, file.Name())
			childRelPath := filepath.Join(relativePath, file.Name())
			children, err := ds.buildDirectoryTree(childPath, childRelPath, currentDepth+1, maxDepth)
			if err != nil {
				return nil, err
			}
			entry.Children = children
		}
		
		entries = append(entries, entry)
	}
	
	return entries, nil
}

func (ds *DirectoryService) CalculateDirectorySize(sessionID string, relativePath string) (int64, error) {
	session, err := ds.sessionManager.GetSession(sessionID)
	if err != nil {
		return 0, err
	}
	
	fullPath := filepath.Join(session.WorkingDir, relativePath)
	
	var size int64
	err = filepath.Walk(fullPath, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		if !info.IsDir() {
			size += info.Size()
		}
		return nil
	})
	
	if err != nil {
		return 0, err
	}
	
	ds.sessionManager.LogActivity(sessionID, fmt.Sprintf("Calculated size for directory %s: %d bytes", relativePath, size))
	fmt.Printf("[TERMINAL] Session %s: Calculated size for directory %s: %d bytes\n", sessionID, relativePath, size)
	return size, nil
}

func (ds *DirectoryService) FindDirectories(sessionID string, baseDir, pattern string, recursive bool) ([]string, error) {
	session, err := ds.sessionManager.GetSession(sessionID)
	if err != nil {
		return nil, err
	}
	
	fullPath := filepath.Join(session.WorkingDir, baseDir)
	
	var matches []string
	
	err = filepath.Walk(fullPath, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		
		// Skip non-directories
		if !info.IsDir() {
			return nil
		}
		
		// If not recursive and not the root dir, skip subdirectories
		if !recursive && path != fullPath && filepath.Dir(path) != fullPath {
			return filepath.SkipDir
		}
		
		// Check if name matches pattern
		if strings.Contains(info.Name(), pattern) {
			// Get relative path from working directory
			relPath, err := filepath.Rel(session.WorkingDir, path)
			if err != nil {
				return err
			}
			matches = append(matches, relPath)
		}
		
		return nil
	})
	
	ds.sessionManager.LogActivity(sessionID, fmt.Sprintf("Found %d directories matching '%s' in %s", len(matches), pattern, baseDir))
	fmt.Printf("[TERMINAL] Session %s: Found %d directories matching '%s' in %s\n", sessionID, len(matches), pattern, baseDir)
	
	if err != nil {
		return nil, err
	}
	
	return matches, nil
}
