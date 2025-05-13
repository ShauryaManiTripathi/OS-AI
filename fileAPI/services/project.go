package services

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
)

// ProjectService provides high-level operations for managing code projects
type ProjectService struct {
	sessionManager *SessionManager
	fileService    *FileService
	dirService     *DirectoryService
}

// ProjectSummary represents an overview of a project
type ProjectSummary struct {
	Name           string            `json:"name"`
	RootPath       string            `json:"rootPath"`
	FileCount      int               `json:"fileCount"`
	DirCount       int               `json:"dirCount"`
	TotalSize      int64             `json:"totalSize"`
	FileTypes      map[string]int    `json:"fileTypes"`
	KeyFiles       []string          `json:"keyFiles"`
	RecentFiles    []FileMetadata    `json:"recentFiles"`
}

// CodeContext represents contextual information for LLMs about a codebase
type CodeContext struct {
	ProjectName    string            `json:"projectName"`
	MainFiles      map[string]string `json:"mainFiles"`
	Dependencies   []string          `json:"dependencies"`
	FileStructure  interface{}       `json:"fileStructure"`
}

func NewProjectService(sm *SessionManager, fs *FileService, ds *DirectoryService) *ProjectService {
	return &ProjectService{
		sessionManager: sm,
		fileService:    fs,
		dirService:     ds,
	}
}

// GetProjectSummary generates a summary of the project in the current working directory
func (ps *ProjectService) GetProjectSummary(sessionID string) (*ProjectSummary, error) {
	session, err := ps.sessionManager.GetSession(sessionID)
	if err != nil {
		return nil, err
	}
	
	// Initialize summary
	summary := &ProjectSummary{
		Name:      filepath.Base(session.WorkingDir),
		RootPath:  session.WorkingDir,
		FileTypes: make(map[string]int),
	}
	
	// Walk through directory
	err = filepath.Walk(session.WorkingDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return nil // Skip files with errors
		}
		
		// Get relative path
		relPath, err := filepath.Rel(session.WorkingDir, path)
		if err != nil {
			return nil
		}
		
		// Skip hidden files and directories
		if strings.HasPrefix(filepath.Base(path), ".") {
			if info.IsDir() && path != session.WorkingDir {
				return filepath.SkipDir
			}
			return nil
		}
		
		if info.IsDir() {
			if path != session.WorkingDir {
				summary.DirCount++
			}
		} else {
			summary.FileCount++
			summary.TotalSize += info.Size()
			
			// Count file types
			ext := strings.ToLower(filepath.Ext(path))
			summary.FileTypes[ext]++
			
			// Add to recent files (if recent)
			if len(summary.RecentFiles) < 5 {
				meta := FileMetadata{
					Name:        info.Name(),
					Path:        relPath,
					Size:        info.Size(),
					ModTime:     info.ModTime(),
					IsDir:       info.IsDir(),
					Permissions: ps.fileService.formatPermissions(info.Mode()), // Make sure to set permissions
				}
				summary.RecentFiles = append(summary.RecentFiles, meta)
			}
			
			// Identify key files
			if ps.isKeyFile(relPath) {
				summary.KeyFiles = append(summary.KeyFiles, relPath)
			}
		}
		
		return nil
	})
	
	if err != nil {
		return nil, err
	}
	
	ps.sessionManager.LogActivity(sessionID, fmt.Sprintf("Generated project summary for %s", summary.Name))
	fmt.Printf("[TERMINAL] Session %s: Generated project summary for %s\n", sessionID, summary.Name)
	
	return summary, nil
}

// isKeyFile determines if a file is likely important in the project
func (ps *ProjectService) isKeyFile(path string) bool {
	filename := filepath.Base(path)
	lowerName := strings.ToLower(filename)
	
	// Config and definition files
	keyFiles := []string{
		"go.mod", "go.sum", "package.json", "package-lock.json", 
		"dockerfile", "docker-compose.yml", "makefile", "readme.md",
		"main.go", "app.js", "index.js", "index.ts", "index.html",
	}
	
	for _, key := range keyFiles {
		if lowerName == key {
			return true
		}
	}
	
	// Main source files by pattern
	mainPatterns := []string{
		`^main\..*`, `^app\..*`, `^index\..*`, `^server\..*`,
	}
	
	for _, pattern := range mainPatterns {
		if matched, _ := regexp.MatchString(pattern, lowerName); matched {
			return true
		}
	}
	
	return false
}

// ExtractCodeContext extracts relevant context for LLM code understanding
func (ps *ProjectService) ExtractCodeContext(sessionID string, maxFiles int) (*CodeContext, error) {
	session, err := ps.sessionManager.GetSession(sessionID)
	if err != nil {
		return nil, err
	}
	
	// Get project summary
	summary, err := ps.GetProjectSummary(sessionID)
	if err != nil {
		return nil, err
	}
	
	context := &CodeContext{
		ProjectName: summary.Name,
		MainFiles:   make(map[string]string),
		Dependencies: []string{},
	}
	
	// Get file structure
	structure := make(map[string]interface{})
	ps.fileService.buildFileStructure(session.WorkingDir, structure, 0, 3) // Depth of 3
	context.FileStructure = structure
	
	// Read key files content
	filesAdded := 0
	for _, keyFile := range summary.KeyFiles {
		if filesAdded >= maxFiles {
			break
		}
		
		// Fix: Actually read and add the file content
		content, err := ps.fileService.ReadFile(sessionID, keyFile)
		if err == nil {
			context.MainFiles[keyFile] = string(content)
			filesAdded++
		}
	}
	
	// If no key files were detected or read, try to read some files from the directory
	if filesAdded == 0 {
		// Get a list of files in the root directory
		files, err := ps.fileService.ListFilesWithMetadata(sessionID, ".")
		if err == nil && len(files) > 0 {
			// Sort files by size (smaller files first, as they're likely config files)
			// This is a simple heuristic that might need improvement
			sort.Slice(files, func(i, j int) bool {
				return files[i].Size < files[j].Size
			})
			
			// Add up to maxFiles files
			for _, file := range files {
				if filesAdded >= maxFiles {
					break
				}
				
				// Skip directories and very large files
				if file.IsDir || file.Size > 1024*1024 { // Skip files over 1MB
					continue
				}
				
				content, err := ps.fileService.ReadFile(sessionID, file.Path)
				if err == nil {
					context.MainFiles[file.Path] = string(content)
					filesAdded++
				}
			}
		}
	}
	
	// Try to extract dependencies
	context.Dependencies = ps.extractDependencies(sessionID)
	
	ps.sessionManager.LogActivity(sessionID, fmt.Sprintf("Extracted code context with %d main files", len(context.MainFiles)))
	fmt.Printf("[TERMINAL] Session %s: Extracted code context with %d main files\n", sessionID, len(context.MainFiles))
	
	return context, nil
}

// extractDependencies attempts to find project dependencies
func (ps *ProjectService) extractDependencies(sessionID string) []string {
	session, err := ps.sessionManager.GetSession(sessionID)
	if err != nil {
		return []string{}
	}
	
	var dependencies []string
	
	// Check for go.mod
	goModPath := filepath.Join(session.WorkingDir, "go.mod")
	if _, err := os.Stat(goModPath); err == nil {
		content, err := ioutil.ReadFile(goModPath)
		if err == nil {
			// Very simple parsing - in real implementation would be more robust
			lines := strings.Split(string(content), "\n")
			for _, line := range lines {
				line = strings.TrimSpace(line)
				if strings.HasPrefix(line, "require") || strings.Contains(line, " v") {
					dependencies = append(dependencies, line)
				}
			}
		}
	}
	
	// Check for package.json
	packagePath := filepath.Join(session.WorkingDir, "package.json")
	if _, err := os.Stat(packagePath); err == nil {
		content, err := ioutil.ReadFile(packagePath)
		if err == nil {
			var pkg map[string]interface{}
			if err := json.Unmarshal(content, &pkg); err == nil {
				if deps, ok := pkg["dependencies"].(map[string]interface{}); ok {
					for dep, ver := range deps {
						dependencies = append(dependencies, fmt.Sprintf("%s: %v", dep, ver))
					}
				}
			}
		}
	}
	
	return dependencies
}
