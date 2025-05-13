package services

import (
	"encoding/json"
	"fmt"
	"io/fs"
	"io/ioutil"
	"os"
	"path/filepath"
	"strings"
	"time"
)

type FileMetadata struct {
	Name         string    `json:"name"`
	Path         string    `json:"path"`
	Size         int64     `json:"size"`
	ModTime      time.Time `json:"modTime"`
	IsDir        bool      `json:"isDir"`
	ContentType  string    `json:"contentType,omitempty"`
	Permissions  string    `json:"permissions"`
}

type FileService struct {
	sessionManager *SessionManager
}

type BatchResult struct {
	Path    string      `json:"path"`
	Success bool        `json:"success"`
	Result  interface{} `json:"result,omitempty"`
	Error   string      `json:"error,omitempty"`
}

func NewFileService(sm *SessionManager) *FileService {
	return &FileService{
		sessionManager: sm,
	}
}

func (fs *FileService) GetFilePath(sessionID string, relativePath string) (string, error) {
	session, err := fs.sessionManager.GetSession(sessionID)
	if err != nil {
		return "", err
	}
	
	if session.WorkingDir == "" {
		return "", fmt.Errorf("working directory not set for session %s", sessionID)
	}
	
	return filepath.Join(session.WorkingDir, relativePath), nil
}

func (fs *FileService) ListFiles(sessionID string, relativePath string) ([]string, error) {
	fullPath, err := fs.GetFilePath(sessionID, relativePath)
	if err != nil {
		return nil, err
	}
	
	files, err := ioutil.ReadDir(fullPath)
	if err != nil {
		return nil, err
	}
	
	var fileNames []string
	for _, file := range files {
		if !file.IsDir() {
			fileNames = append(fileNames, file.Name())
		}
	}
	
	fs.sessionManager.LogActivity(sessionID, fmt.Sprintf("Listed %d files in %s", len(fileNames), relativePath))
	fmt.Printf("[TERMINAL] Session %s: Listed %d files in %s\n", sessionID, len(fileNames), relativePath)
	return fileNames, nil
}

func (fs *FileService) ListFilesWithMetadata(sessionID string, relativePath string) ([]FileMetadata, error) {
	fullPath, err := fs.GetFilePath(sessionID, relativePath)
	if err != nil {
		return nil, err
	}
	
	files, err := ioutil.ReadDir(fullPath)
	if err != nil {
		return nil, err
	}
	
	var fileMetadata []FileMetadata
	for _, file := range files {
		if !file.IsDir() {
			meta := FileMetadata{
				Name:     file.Name(),
				Path:     filepath.Join(relativePath, file.Name()),
				Size:     file.Size(),
				ModTime:  file.ModTime(),
				IsDir:    file.IsDir(),
				Permissions: fs.formatPermissions(file.Mode()),
			}
			
			// Try to determine content type (simple implementation)
			if ext := filepath.Ext(file.Name()); ext != "" {
				meta.ContentType = fs.getContentTypeByExt(ext)
			}
			
			fileMetadata = append(fileMetadata, meta)
		}
	}
	
	fs.sessionManager.LogActivity(sessionID, fmt.Sprintf("Listed %d files with metadata in %s", 
		len(fileMetadata), relativePath))
	fmt.Printf("[TERMINAL] Session %s: Listed %d files with metadata in %s\n", 
		sessionID, len(fileMetadata), relativePath)
	return fileMetadata, nil
}

func (fs *FileService) formatPermissions(mode fs.FileMode) string {
	return mode.String()
}

func (fs *FileService) getContentTypeByExt(ext string) string {
	ext = strings.ToLower(ext)
	switch ext {
	case ".txt":
		return "text/plain"
	case ".html", ".htm":
		return "text/html"
	case ".js":
		return "application/javascript"
	case ".json":
		return "application/json"
	case ".css":
		return "text/css"
	case ".go":
		return "text/x-go"
	case ".py":
		return "text/x-python"
	case ".md":
		return "text/markdown"
	// Add more types as needed
	default:
		return "application/octet-stream"
	}
}

func (fs *FileService) ReadFile(sessionID string, relativePath string) ([]byte, error) {
	fullPath, err := fs.GetFilePath(sessionID, relativePath)
	if err != nil {
		return nil, err
	}
	
	content, err := ioutil.ReadFile(fullPath)
	if err != nil {
		return nil, err
	}
	
	fs.sessionManager.LogActivity(sessionID, fmt.Sprintf("Read file %s", relativePath))
	fmt.Printf("[TERMINAL] Session %s: Read file %s\n", sessionID, relativePath)
	return content, nil
}

func (fs *FileService) GetFileMetadata(sessionID string, relativePath string) (*FileMetadata, error) {
	fullPath, err := fs.GetFilePath(sessionID, relativePath)
	if err != nil {
		return nil, err
	}
	
	fileInfo, err := os.Stat(fullPath)
	if err != nil {
		return nil, err
	}
	
	meta := &FileMetadata{
		Name:     fileInfo.Name(),
		Path:     relativePath,
		Size:     fileInfo.Size(),
		ModTime:  fileInfo.ModTime(),
		IsDir:    fileInfo.IsDir(),
		Permissions: fs.formatPermissions(fileInfo.Mode()),
	}
	
	if ext := filepath.Ext(fileInfo.Name()); ext != "" {
		meta.ContentType = fs.getContentTypeByExt(ext)
	}
	
	fs.sessionManager.LogActivity(sessionID, fmt.Sprintf("Retrieved metadata for %s", relativePath))
	fmt.Printf("[TERMINAL] Session %s: Retrieved metadata for %s\n", sessionID, relativePath)
	return meta, nil
}

func (fs *FileService) CreateFile(sessionID string, relativePath string, content []byte) error {
	fullPath, err := fs.GetFilePath(sessionID, relativePath)
	if err != nil {
		return err
	}
	
	// Make sure parent directory exists
	dir := filepath.Dir(fullPath)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return err
	}
	
	// Create the file
	if err := ioutil.WriteFile(fullPath, content, 0644); err != nil {
		return err
	}
	
	fs.sessionManager.LogActivity(sessionID, fmt.Sprintf("Created file %s", relativePath))
	fmt.Printf("[TERMINAL] Session %s: Created file %s\n", sessionID, relativePath)
	return nil
}

func (fs *FileService) UpdateFile(sessionID string, relativePath string, content []byte) error {
	fullPath, err := fs.GetFilePath(sessionID, relativePath)
	if err != nil {
		return err
	}
	
	if err := ioutil.WriteFile(fullPath, content, 0644); err != nil {
		return err
	}
	
	fs.sessionManager.LogActivity(sessionID, fmt.Sprintf("Updated file %s", relativePath))
	fmt.Printf("[TERMINAL] Session %s: Updated file %s\n", sessionID, relativePath)
	return nil
}

func (fs *FileService) DeleteFile(sessionID string, relativePath string) error {
	fullPath, err := fs.GetFilePath(sessionID, relativePath)
	if err != nil {
		return err
	}
	
	if err := os.Remove(fullPath); err != nil {
		return err
	}
	
	fs.sessionManager.LogActivity(sessionID, fmt.Sprintf("Deleted file %s", relativePath))
	fmt.Printf("[TERMINAL] Session %s: Deleted file %s\n", sessionID, relativePath)
	return nil
}

// Batch operations
func (fs *FileService) BatchReadFiles(sessionID string, relativePaths []string) []BatchResult {
	results := make([]BatchResult, 0, len(relativePaths))
	
	for _, path := range relativePaths {
		result := BatchResult{Path: path}
		
		content, err := fs.ReadFile(sessionID, path)
		if err != nil {
			result.Success = false
			result.Error = err.Error()
		} else {
			result.Success = true
			result.Result = string(content)
		}
		
		results = append(results, result)
	}
	
	fs.sessionManager.LogActivity(sessionID, fmt.Sprintf("Batch read %d files", len(relativePaths)))
	fmt.Printf("[TERMINAL] Session %s: Batch read %d files\n", sessionID, len(relativePaths))
	return results
}

func (fs *FileService) BatchCreateFiles(sessionID string, files map[string]string) []BatchResult {
	results := make([]BatchResult, 0, len(files))
	
	for path, content := range files {
		result := BatchResult{Path: path}
		
		err := fs.CreateFile(sessionID, path, []byte(content))
		if err != nil {
			result.Success = false
			result.Error = err.Error()
		} else {
			result.Success = true
		}
		
		results = append(results, result)
	}
	
	fs.sessionManager.LogActivity(sessionID, fmt.Sprintf("Batch created %d files", len(files)))
	fmt.Printf("[TERMINAL] Session %s: Batch created %d files\n", sessionID, len(files))
	return results
}

func (fs *FileService) SearchInFiles(sessionID string, dir string, pattern string, recursive bool) (map[string][]string, error) {
	fullPath, err := fs.GetFilePath(sessionID, dir)
	if err != nil {
		return nil, err
	}
	
	results := make(map[string][]string)
	
	err = filepath.Walk(fullPath, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		
		// Skip directories
		if info.IsDir() {
			// If not recursive and not the root dir, skip
			if (!recursive && path != fullPath) {
				return filepath.SkipDir
			}
			return nil
		}
		
		// Get relative path
		relPath, err := filepath.Rel(fullPath, path)
		if err != nil {
			return err
		}
		
		// Read and search in file
		content, err := ioutil.ReadFile(path)
		if err != nil {
			return nil // Skip files we can't read
		}
		
		if strings.Contains(string(content), pattern) {
			// Found match - add lines containing the pattern
			lines := strings.Split(string(content), "\n")
			var matches []string
			
			for _, line := range lines {
				if strings.Contains(line, pattern) {
					matches = append(matches, line)
				}
			}
			
			// Store in relative path
			results[relPath] = matches
		}
		
		return nil
	})
	
	fs.sessionManager.LogActivity(sessionID, fmt.Sprintf("Searched for pattern '%s' in %s", pattern, dir))
	fmt.Printf("[TERMINAL] Session %s: Searched for pattern '%s' in %s\n", sessionID, pattern, dir)
	
	if err != nil {
		return nil, err
	}
	
	return results, nil
}

// Export file structure as JSON
func (fs *FileService) ExportFileStructure(sessionID string, dir string, depth int) (string, error) {
	fullPath, err := fs.GetFilePath(sessionID, dir)
	if err != nil {
		return "", err
	}
	
	structure := make(map[string]interface{})
	
	err = fs.buildFileStructure(fullPath, structure, 0, depth)
	if err != nil {
		return "", err
	}
	
	jsonData, err := json.MarshalIndent(structure, "", "  ")
	if err != nil {
		return "", err
	}
	
	fs.sessionManager.LogActivity(sessionID, fmt.Sprintf("Exported file structure for %s", dir))
	fmt.Printf("[TERMINAL] Session %s: Exported file structure for %s\n", sessionID, dir)
	
	return string(jsonData), nil
}

func (fs *FileService) buildFileStructure(path string, structure map[string]interface{}, currentDepth, maxDepth int) error {
	if maxDepth > 0 && currentDepth >= maxDepth {
		return nil
	}
	
	files, err := ioutil.ReadDir(path)
	if err != nil {
		return err
	}
	
	for _, file := range files {
		name := file.Name()
		
		if file.IsDir() {
			subDir := make(map[string]interface{})
			structure[name] = subDir
			
			// Recurse for subdirectories
			fullSubPath := filepath.Join(path, name)
			if err := fs.buildFileStructure(fullSubPath, subDir, currentDepth+1, maxDepth); err != nil {
				return err
			}
		} else {
			meta := map[string]interface{}{
				"size":    file.Size(),
				"modTime": file.ModTime(),
			}
			structure[name] = meta
		}
	}
	
	return nil
}
