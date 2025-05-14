package handlers

import (
	"bufio"
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"runtime"
	"strings"
	"time"

	"github.com/labstack/echo/v4"
	"terminalAPI/services"
)

type SystemHandler struct {
	sessionManager *services.SessionManager
}

type SystemInfo struct {
	Hostname      string    `json:"hostname"`
	OS            string    `json:"os"`
	Distribution  string    `json:"distribution"`
	Architecture  string    `json:"architecture"`
	NumCPU        int       `json:"numCPU"`
	CurrentTime   time.Time `json:"currentTime"`
	Timezone      string    `json:"timezone"`
}

func NewSystemHandler() *SystemHandler {
	return &SystemHandler{}
}

// Add new constructor that includes session manager
func NewSystemHandlerWithSessionManager(sm *services.SessionManager) *SystemHandler {
	return &SystemHandler{
		sessionManager: sm,
	}
}

func (h *SystemHandler) GetSystemInfo(c echo.Context) error {
	hostname, _ := os.Hostname()
	tz, _ := time.Now().Zone()
	
	distro := getDistributionName()
	
	info := SystemInfo{
		Hostname:     hostname,
		OS:           runtime.GOOS,
		Distribution: distro,
		Architecture: runtime.GOARCH,
		NumCPU:       runtime.NumCPU(),
		CurrentTime:  time.Now(),
		Timezone:     tz,
	}
	
	return c.JSON(http.StatusOK, info)
}

// getDistributionName attempts to get the Linux distribution name
func getDistributionName() string {
	distro := runtime.GOOS
	
	if runtime.GOOS != "linux" {
		return distro
	}
	
	if file, err := os.Open("/etc/os-release"); err == nil {
		defer file.Close()
		
		scanner := bufio.NewScanner(file)
		for scanner.Scan() {
			line := scanner.Text()
			if strings.HasPrefix(line, "NAME=") {
				value := strings.TrimPrefix(line, "NAME=")
				value = strings.Trim(value, "\"")
				if value != "" {
					return value
				}
			}
		}
	}
	
	if file, err := os.Open("/etc/lsb-release"); err == nil {
		defer file.Close()
		
		scanner := bufio.NewScanner(file)
		for scanner.Scan() {
			line := scanner.Text()
			if strings.HasPrefix(line, "DISTRIB_DESCRIPTION=") {
				value := strings.TrimPrefix(line, "DISTRIB_DESCRIPTION=")
				value = strings.Trim(value, "\"")
				if value != "" {
					return value
				}
			}
		}
	}
	
	return distro
}

func (h *SystemHandler) GetAvailableShells(c echo.Context) error {
	// Common shell paths to check across different distributions
	shellPaths := []string{
		// Standard shell paths
		"/bin/bash", "/bin/sh", "/bin/zsh", "/bin/fish", "/bin/dash",
		// Additional locations
		"/usr/bin/bash", "/usr/bin/zsh", "/usr/bin/fish", "/usr/bin/dash",
		"/usr/local/bin/bash", "/usr/local/bin/zsh", "/usr/local/bin/fish",
	}
	
	availableShells := make(map[string]bool)
	
	// Check which shells actually exist
	for _, shell := range shellPaths {
		_, err := os.Stat(shell)
		availableShells[shell] = err == nil
	}
	
	// Try using the "which" command to find additional shells
	possibleShells := []string{"bash", "zsh", "fish", "dash", "ksh", "csh", "tcsh"}
	for _, shellName := range possibleShells {
		cmd := exec.Command("which", shellName)
		output, err := cmd.Output()
		if err == nil && len(output) > 0 {
			path := strings.TrimSpace(string(output))
			if path != "" && !availableShells[path] {
				availableShells[path] = true
			}
		}
	}
	
	// Windows systems
	if runtime.GOOS == "windows" {
		availableShells["cmd.exe"] = true
		availableShells["powershell.exe"] = true
	}

	// Get the current shell from the session's environment variables
	sessionID := c.Param("sessionId")
	
	// Default to system shell only if we can't get a session-specific one
	currentShell := ""
	
	fmt.Printf("[DEBUG] GetAvailableShells: Session ID from path param: '%s'\n", sessionID)
	
	if sessionID == "" {
		sessionID = c.QueryParam("sessionId")
		fmt.Printf("[DEBUG] GetAvailableShells: Session ID from query param: '%s'\n", sessionID)
	}
	
	// First try to get the shell from the session
	shellFound := false
	if sessionID != "" && h.sessionManager != nil {
		fmt.Printf("[DEBUG] GetAvailableShells: Getting SHELL for session '%s'\n", sessionID)
		
		// Using direct session access for demonstration purposes only
		envVars, err := h.sessionManager.GetEnvVars(sessionID)
		if err == nil && envVars != nil {
			if shell, exists := envVars["SHELL"]; exists && shell != "" {
				currentShell = shell
				shellFound = true
				fmt.Printf("[DEBUG] GetAvailableShells: Found session SHELL: '%s'\n", currentShell)
			}
		}
	}
	
	// Only fall back to system shell if we couldn't get one from the session
	if !shellFound {
		currentShell = os.Getenv("SHELL")
		fmt.Printf("[DEBUG] GetAvailableShells: Using system SHELL: '%s'\n", currentShell)
	}
	
	// Include useful debug info in the response
	return c.JSON(http.StatusOK, map[string]interface{}{
		"availableShells": availableShells,
		"currentShell":    currentShell,
		"sessionId":       sessionID,
		"shellFoundInSession": shellFound,
		"systemShell":     os.Getenv("SHELL"),
	})
}
