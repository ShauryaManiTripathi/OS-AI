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
	"time"
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

// FileInfo represents file details with dependencies
type FileInfo struct {
	Content      string   `json:"content"`
	Dependencies []string `json:"dependencies,omitempty"`
	Size         int64    `json:"size"`
	ModTime      string   `json:"modTime,omitempty"`
	Language     string   `json:"language,omitempty"`
}

// CodeContext represents contextual information for LLMs about a codebase
type CodeContext struct {
	ProjectName    string                `json:"projectName"`
	MainFiles      map[string]*FileInfo   `json:"mainFiles"`
	Dependencies   []string              `json:"projectDependencies,omitempty"`
	FileStructure  interface{}           `json:"fileStructure"`
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
		MainFiles:   make(map[string]*FileInfo),
		Dependencies: []string{},
	}
	
	// Get file structure
	structure := make(map[string]interface{})
	ps.fileService.buildFileStructure(session.WorkingDir, structure, 0, 3) // Depth of 3
	context.FileStructure = structure
	
	// Process project-level dependency files first
	context.Dependencies = ps.extractProjectDependencies(sessionID)
	
	// Read key files content and extract their dependencies
	filesAdded := 0
	for _, keyFile := range summary.KeyFiles {
		if filesAdded >= maxFiles {
			break
		}
		
		content, err := ps.fileService.ReadFile(sessionID, keyFile)
		if err == nil {
			fileInfo, err := ps.createFileInfo(sessionID, keyFile, content)
			if err == nil {
				context.MainFiles[keyFile] = fileInfo
				filesAdded++
			}
		}
	}
	
	// If no key files were detected or read, try to read some files from the directory
	if filesAdded == 0 {
		// Get a list of files in the root directory
		files, err := ps.fileService.ListFilesWithMetadata(sessionID, ".")
		if err == nil && len(files) > 0 {
			// Sort files by size (smaller files first, as they're likely config files)
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
					fileInfo, err := ps.createFileInfo(sessionID, file.Path, content)
					if err == nil {
						context.MainFiles[file.Path] = fileInfo
						filesAdded++
					}
				}
			}
		}
	}
	
	ps.sessionManager.LogActivity(sessionID, fmt.Sprintf("Extracted code context with %d main files", len(context.MainFiles)))
	fmt.Printf("[TERMINAL] Session %s: Extracted code context with %d main files\n", sessionID, len(context.MainFiles))
	
	return context, nil
}

// createFileInfo creates a FileInfo object with content and dependencies
func (ps *ProjectService) createFileInfo(sessionID string, path string, content []byte) (*FileInfo, error) {
	fileInfo := &FileInfo{
		Content: string(content),
		Size:    int64(len(content)),
		ModTime: time.Now().Format(time.RFC3339),
	}
	
	// Detect language based on file extension
	ext := strings.ToLower(filepath.Ext(path))
	fileInfo.Language = ps.detectLanguage(ext)
	
	// Extract dependencies based on file type
	deps := ps.extractFileDependencies(string(content), ext)
	if len(deps) > 0 {
		fileInfo.Dependencies = deps
	}
	
	return fileInfo, nil
}

// detectLanguage detects the programming language from file extension
func (ps *ProjectService) detectLanguage(ext string) string {
	switch ext {
	case ".go":
		return "Go"
	case ".js":
		return "JavaScript"
	case ".ts", ".tsx":
		return "TypeScript"
	case ".jsx":
		return "JSX"
	case ".py":
		return "Python"
	case ".java":
		return "Java"
	case ".rb":
		return "Ruby"
	case ".php":
		return "PHP"
	case ".rs":
		return "Rust"
	case ".cs":
		return "C#"
	case ".c", ".h":
		return "C"
	case ".cpp", ".cc", ".cxx", ".hpp":
		return "C++"
	case ".swift":
		return "Swift"
	case ".kt", ".kts":
		return "Kotlin"
	case ".scala":
		return "Scala"
	case ".dart":
		return "Dart"
	case ".r":
		return "R"
	case ".sh", ".bash":
		return "Shell"
	case ".pl":
		return "Perl"
	case ".ex", ".exs":
		return "Elixir"
	case ".hs":
		return "Haskell"
	case ".clj":
		return "Clojure"
	case ".lua":
		return "Lua"
	case ".sql":
		return "SQL"
	case ".html", ".htm":
		return "HTML"
	case ".css":
		return "CSS"
	case ".scss":
		return "SCSS"
	case ".less":
		return "Less"
	case ".json":
		return "JSON"
	case ".xml":
		return "XML"
	case ".yaml", ".yml":
		return "YAML"
	case ".md":
		return "Markdown"
	case ".txt":
		return "Text"
	default:
		return "Unknown"
	}
}

// extractFileDependencies extracts dependencies from a file based on its type
func (ps *ProjectService) extractFileDependencies(content string, ext string) []string {
	var deps []string
	
	// Handle different file types
	switch ext {
	case ".go":
		deps = ps.extractGoDependencies(content)
	case ".js", ".jsx", ".ts", ".tsx":
		deps = ps.extractJSDependencies(content)
	case ".py":
		deps = ps.extractPythonDependencies(content)
	case ".java":
		deps = ps.extractJavaDependencies(content)
	case ".rb":
		deps = ps.extractRubyDependencies(content)
	case ".php":
		deps = ps.extractPHPDependencies(content)
	case ".rs":
		deps = ps.extractRustDependencies(content)
	case ".cs":
		deps = ps.extractCSharpDependencies(content)
	case ".c", ".cpp", ".cc", ".h", ".hpp":
		deps = ps.extractCDependencies(content)
	}
	
	return deps
}

// extractGoDependencies extracts dependencies from Go files
func (ps *ProjectService) extractGoDependencies(content string) []string {
	var deps []string
	
	// Regular expression for Go imports
	importRegex := regexp.MustCompile(`(?m)^\s*import\s+\(\s*((?:.|\n)*?)\s*\)|^\s*import\s+"(.*?)"`)
	matches := importRegex.FindAllStringSubmatch(content, -1)
	
	for _, match := range matches {
		if match[1] != "" {
			// Multi-line import
			multiImportRegex := regexp.MustCompile(`"([^"]+)"`)
			multiMatches := multiImportRegex.FindAllStringSubmatch(match[1], -1)
			for _, multiMatch := range multiMatches {
				if multiMatch[1] != "" {
					deps = append(deps, multiMatch[1])
				}
			}
		} else if match[2] != "" {
			// Single import
			deps = append(deps, match[2])
		}
	}
	
	return deps
}

// extractJSDependencies extracts dependencies from JavaScript/TypeScript files
func (ps *ProjectService) extractJSDependencies(content string) []string {
	var deps []string
	
	// Regex for ES6 imports
	es6Regex := regexp.MustCompile(`(?m)import\s+(?:(?:\{[^}]*\})|(?:[\w*]+))\s+from\s+['"]([^'"]+)['"]`)
	es6Matches := es6Regex.FindAllStringSubmatch(content, -1)
	for _, match := range es6Matches {
		if match[1] != "" {
			deps = append(deps, match[1])
		}
	}
	
	// Regex for CommonJS requires
	cjsRegex := regexp.MustCompile(`(?m)(?:const|let|var)\s+(?:\{[^}]*\}|\w+)\s*=\s*require\(['"]([^'"]+)['"]\)`)
	cjsMatches := cjsRegex.FindAllStringSubmatch(content, -1)
	for _, match := range cjsMatches {
		if match[1] != "" {
			deps = append(deps, match[1])
		}
	}
	
	return deps
}

// extractPythonDependencies extracts dependencies from Python files
func (ps *ProjectService) extractPythonDependencies(content string) []string {
	var deps []string
	
	// Import statements
	importRegex := regexp.MustCompile(`(?m)^\s*import\s+([\w.]+)(?:\s+as\s+\w+)?|^\s*from\s+([\w.]+)\s+import`)
	matches := importRegex.FindAllStringSubmatch(content, -1)
	
	for _, match := range matches {
		if match[1] != "" {
			baseModule := strings.Split(match[1], ".")[0]
			if baseModule != "" && !contains(deps, baseModule) {
				deps = append(deps, baseModule)
			}
		} else if match[2] != "" {
			baseModule := strings.Split(match[2], ".")[0]
			if baseModule != "" && !contains(deps, baseModule) {
				deps = append(deps, baseModule)
			}
		}
	}
	
	return deps
}

// extractJavaDependencies extracts dependencies from Java files
func (ps *ProjectService) extractJavaDependencies(content string) []string {
	var deps []string
	
	// Import statements
	importRegex := regexp.MustCompile(`(?m)^\s*import\s+(static\s+)?([\w.]+)(?:\.\*)?;`)
	matches := importRegex.FindAllStringSubmatch(content, -1)
	
	for _, match := range matches {
		if match[2] != "" {
			// Get the package name (first part of the import)
			parts := strings.Split(match[2], ".")
			if len(parts) > 0 {
				basePackage := parts[0]
				if !contains(deps, basePackage) {
					deps = append(deps, basePackage)
				}
			}
		}
	}
	
	return deps
}

// extractRubyDependencies extracts dependencies from Ruby files
func (ps *ProjectService) extractRubyDependencies(content string) []string {
	var deps []string
	
	// Require statements
	requireRegex := regexp.MustCompile(`(?m)^\s*require\s+['"]([\w\-/]+)['"]`)
	matches := requireRegex.FindAllStringSubmatch(content, -1)
	
	for _, match := range matches {
		if match[1] != "" && !contains(deps, match[1]) {
			deps = append(deps, match[1])
		}
	}
	
	// Gem statements
	gemRegex := regexp.MustCompile(`(?m)^\s*gem\s+['"]([\w\-]+)['"]`)
	gemMatches := gemRegex.FindAllStringSubmatch(content, -1)
	
	for _, match := range gemMatches {
		if match[1] != "" && !contains(deps, match[1]) {
			deps = append(deps, match[1])
		}
	}
	
	return deps
}

// extractPHPDependencies extracts dependencies from PHP files
func (ps *ProjectService) extractPHPDependencies(content string) []string {
	var deps []string
	
	// Use statements
	useRegex := regexp.MustCompile(`(?m)^\s*use\s+([\w\\]+)`)
	matches := useRegex.FindAllStringSubmatch(content, -1)
	
	for _, match := range matches {
		if match[1] != "" {
			// Get the top-level namespace
			parts := strings.Split(match[1], "\\")
			if len(parts) > 0 {
				baseNs := parts[0]
				if baseNs != "" && !contains(deps, baseNs) {
					deps = append(deps, baseNs)
				}
			}
		}
	}
	
	// Require/include statements
	requireRegex := regexp.MustCompile(`(?:require|include)(?:_once)?\s*\(\s*['"]([\w\-./]+)['"]`)
	reqMatches := requireRegex.FindAllStringSubmatch(content, -1)
	
	for _, match := range reqMatches {
		if match[1] != "" && !contains(deps, match[1]) {
			deps = append(deps, match[1])
		}
	}
	
	return deps
}

// extractRustDependencies extracts dependencies from Rust files
func (ps *ProjectService) extractRustDependencies(content string) []string {
	var deps []string
	
	// Use statements
	useRegex := regexp.MustCompile(`(?m)^\s*use\s+([\w:]+)`)
	matches := useRegex.FindAllStringSubmatch(content, -1)
	
	for _, match := range matches {
		if match[1] != "" {
			// Get the crate name (first part before ::)
			parts := strings.Split(match[1], "::")
			if len(parts) > 0 {
				baseCrate := parts[0]
				if baseCrate != "" && baseCrate != "std" && baseCrate != "core" && !contains(deps, baseCrate) {
					deps = append(deps, baseCrate)
				}
			}
		}
	}
	
	// External crate statements
	crateRegex := regexp.MustCompile(`(?m)^\s*extern\s+crate\s+([\w_]+)`)
	crateMatches := crateRegex.FindAllStringSubmatch(content, -1)
	
	for _, match := range crateMatches {
		if match[1] != "" && !contains(deps, match[1]) {
			deps = append(deps, match[1])
		}
	}
	
	return deps
}

// extractCSharpDependencies extracts dependencies from C# files
func (ps *ProjectService) extractCSharpDependencies(content string) []string {
	var deps []string
	
	// Using statements
	usingRegex := regexp.MustCompile(`(?m)^\s*using\s+([\w.]+);`)
	matches := usingRegex.FindAllStringSubmatch(content, -1)
	
	for _, match := range matches {
		if match[1] != "" {
			// Get the top-level namespace
			parts := strings.Split(match[1], ".")
			if len(parts) > 0 {
				baseNs := parts[0]
				if baseNs != "" && !contains(deps, baseNs) {
					deps = append(deps, baseNs)
				}
			}
		}
	}
	
	return deps
}

// extractCDependencies extracts dependencies from C/C++ files
func (ps *ProjectService) extractCDependencies(content string) []string {
	var deps []string
	
	// Include statements
	includeRegex := regexp.MustCompile(`(?m)#\s*include\s*[<"]([^>"]+)[>"]`)
	matches := includeRegex.FindAllStringSubmatch(content, -1)
	
	for _, match := range matches {
		if match[1] != "" && !contains(deps, match[1]) {
			deps = append(deps, match[1])
		}
	}
	
	return deps
}

// extractProjectDependencies extracts project-level dependencies
func (ps *ProjectService) extractProjectDependencies(sessionID string) []string {
	var dependencies []string
	session, err := ps.sessionManager.GetSession(sessionID)
	if err != nil {
		return dependencies
	}
	
	// Map of common dependency files and extraction functions
	depFiles := map[string]func(string, string) []string{
		"go.mod":         ps.extractGoModDependencies,
		"package.json":   ps.extractPackageJsonDependencies,
		"requirements.txt": ps.extractRequirementsTxtDependencies,
		"Gemfile":        ps.extractGemfileDependencies,
		"composer.json":  ps.extractComposerJsonDependencies,
		"Cargo.toml":     ps.extractCargoTomlDependencies,
		"pom.xml":        ps.extractPomXmlDependencies,
		"build.gradle":   ps.extractGradleDependencies,
	}
	
	// Check each dependency file
	for filename, extractFunc := range depFiles {
		filePath := filepath.Join(session.WorkingDir, filename)
		if _, err := os.Stat(filePath); err == nil {
			content, err := ioutil.ReadFile(filePath)
			if err == nil {
				deps := extractFunc(string(content), filename)
				dependencies = append(dependencies, deps...)
			}
		}
	}
	
	return dependencies
}

// extractGoModDependencies extracts dependencies from go.mod file
func (ps *ProjectService) extractGoModDependencies(content, _ string) []string {
	var deps []string
	
	// Regular expression for Go module dependencies
	depsRegex := regexp.MustCompile(`(?m)^\s*require\s+\(\s*((?:.|\n)*?)\s*\)|^\s*require\s+([\w./\-@]+)\s+(v[\w.]+)`)
	matches := depsRegex.FindAllStringSubmatch(content, -1)
	
	for _, match := range matches {
		if match[1] != "" {
			// Multi-line require block
			lineRegex := regexp.MustCompile(`(?m)^\s*([\w./\-@]+)\s+(v[\w.]+)`)
			lineMatches := lineRegex.FindAllStringSubmatch(match[1], -1)
			for _, lineMatch := range lineMatches {
				if lineMatch[1] != "" && lineMatch[2] != "" {
					deps = append(deps, lineMatch[1]+" "+lineMatch[2])
				}
			}
		} else if match[2] != "" && match[3] != "" {
			// Single require line
			deps = append(deps, match[2]+" "+match[3])
		}
	}
	
	return deps
}

// extractPackageJsonDependencies extracts dependencies from package.json
func (ps *ProjectService) extractPackageJsonDependencies(content, _ string) []string {
	var deps []string
	
	var pkg map[string]interface{}
	if err := json.Unmarshal([]byte(content), &pkg); err == nil {
		// Regular dependencies
		if depMap, ok := pkg["dependencies"].(map[string]interface{}); ok {
			for dep, ver := range depMap {
				deps = append(deps, fmt.Sprintf("%s: %v", dep, ver))
			}
		}
		
		// Dev dependencies
		if devDepMap, ok := pkg["devDependencies"].(map[string]interface{}); ok {
			for dep, ver := range devDepMap {
				deps = append(deps, fmt.Sprintf("%s (dev): %v", dep, ver))
			}
		}
	}
	
	return deps
}

// extractRequirementsTxtDependencies extracts dependencies from Python requirements.txt
func (ps *ProjectService) extractRequirementsTxtDependencies(content, _ string) []string {
	var deps []string
	
	lines := strings.Split(content, "\n")
	for _, line := range lines {
		line = strings.TrimSpace(line)
		
		// Skip comments and empty lines
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		
		// Handle requirements lines
		deps = append(deps, line)
	}
	
	return deps
}

// extractGemfileDependencies extracts dependencies from Ruby Gemfile
func (ps *ProjectService) extractGemfileDependencies(content, _ string) []string {
	var deps []string
	
	// Regex for gem declarations
	gemRegex := regexp.MustCompile(`(?m)^\s*gem\s+['"]([^'"]+)['"](?:\s*,\s*['"]([^'"]+)['"])?`)
	matches := gemRegex.FindAllStringSubmatch(content, -1)
	
	for _, match := range matches {
		if match[1] != "" {
			if match[2] != "" {
				deps = append(deps, fmt.Sprintf("%s: %s", match[1], match[2]))
			} else {
				deps = append(deps, match[1])
			}
		}
	}
	
	return deps
}

// extractComposerJsonDependencies extracts dependencies from PHP composer.json
func (ps *ProjectService) extractComposerJsonDependencies(content, _ string) []string {
	var deps []string
	
	var composerData map[string]interface{}
	if err := json.Unmarshal([]byte(content), &composerData); err == nil {
		// Regular dependencies
		if depMap, ok := composerData["require"].(map[string]interface{}); ok {
			for dep, ver := range depMap {
				deps = append(deps, fmt.Sprintf("%s: %v", dep, ver))
			}
		}
		
		// Dev dependencies
		if devDepMap, ok := composerData["require-dev"].(map[string]interface{}); ok {
			for dep, ver := range devDepMap {
				deps = append(deps, fmt.Sprintf("%s (dev): %v", dep, ver))
			}
		}
	}
	
	return deps
}

// extractCargoTomlDependencies extracts dependencies from Rust Cargo.toml
func (ps *ProjectService) extractCargoTomlDependencies(content, _ string) []string {
	var deps []string
	
	// Very simple TOML parsing for dependencies section
	depRegex := regexp.MustCompile(`(?m)^\[dependencies\]\s*((?:.|\n)*?)(?:^\[|\z)`)
	matches := depRegex.FindStringSubmatch(content)
	
	if len(matches) > 1 {
		// Parse individual dependencies
		lines := strings.Split(matches[1], "\n")
		for _, line := range lines {
			line = strings.TrimSpace(line)
			if line != "" && !strings.HasPrefix(line, "#") {
				parts := strings.SplitN(line, "=", 2)
				if len(parts) == 2 {
					name := strings.TrimSpace(parts[0])
					version := strings.TrimSpace(parts[1])
					deps = append(deps, fmt.Sprintf("%s = %s", name, version))
				}
			}
		}
	}
	
	return deps
}

// extractPomXmlDependencies extracts dependencies from Java pom.xml
func (ps *ProjectService) extractPomXmlDependencies(content, _ string) []string {
	var deps []string
	
	// Simple regex for Maven dependencies
	depRegex := regexp.MustCompile(`<dependency>[\s\S]*?<groupId>(.*?)</groupId>[\s\S]*?<artifactId>(.*?)</artifactId>[\s\S]*?<version>(.*?)</version>[\s\S]*?</dependency>`)
	matches := depRegex.FindAllStringSubmatch(content, -1)
	
	for _, match := range matches {
		if len(match) >= 4 {
			groupId := match[1]
			artifactId := match[2]
			version := match[3]
			deps = append(deps, fmt.Sprintf("%s:%s:%s", groupId, artifactId, version))
		}
	}
	
	return deps
}

// extractGradleDependencies extracts dependencies from build.gradle
func (ps *ProjectService) extractGradleDependencies(content, _ string) []string {
	var deps []string
	
	// Gradle dependencies
	depRegex := regexp.MustCompile(`(?m)implementation\s+['"]([^'"]+)['"]`)
	matches := depRegex.FindAllStringSubmatch(content, -1)
	
	for _, match := range matches {
		if match[1] != "" {
			deps = append(deps, match[1])
		}
	}
	
	return deps
}

// Helper function to check if a slice contains a string
func contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}
