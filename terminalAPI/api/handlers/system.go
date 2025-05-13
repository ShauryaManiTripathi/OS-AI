package handlers

import (
	"net/http"
	"os"
	"runtime"
	"time"

	"github.com/labstack/echo/v4"
)

type SystemHandler struct {
}

type SystemInfo struct {
	Hostname      string    `json:"hostname"`
	OS            string    `json:"os"`
	Architecture  string    `json:"architecture"`
	NumCPU        int       `json:"numCPU"`
	GoVersion     string    `json:"goVersion"`
	CurrentTime   time.Time `json:"currentTime"`
	Timezone      string    `json:"timezone"`
	WorkingDir    string    `json:"workingDir"`
}

func NewSystemHandler() *SystemHandler {
	return &SystemHandler{}
}

func (h *SystemHandler) GetSystemInfo(c echo.Context) error {
	hostname, _ := os.Hostname()
	wd, _ := os.Getwd()
	tz, _ := time.Now().Zone()
	
	info := SystemInfo{
		Hostname:     hostname,
		OS:           runtime.GOOS,
		Architecture: runtime.GOARCH,
		NumCPU:       runtime.NumCPU(),
		GoVersion:    runtime.Version(),
		CurrentTime:  time.Now(),
		Timezone:     tz,
		WorkingDir:   wd,
	}
	
	return c.JSON(http.StatusOK, info)
}

func (h *SystemHandler) GetAvailableShells(c echo.Context) error {
	shells := []string{"/bin/bash", "/bin/sh", "/bin/zsh", "/usr/bin/fish"}
	availableShells := make(map[string]bool)
	
	// Check which shells actually exist
	for _, shell := range shells {
		_, err := os.Stat(shell)
		availableShells[shell] = err == nil
	}
	
	// Windows systems
	if runtime.GOOS == "windows" {
		availableShells["cmd.exe"] = true
		availableShells["powershell.exe"] = true
	}
	
	return c.JSON(http.StatusOK, map[string]interface{}{
		"availableShells": availableShells,
		"currentShell":    os.Getenv("SHELL"),
	})
}
