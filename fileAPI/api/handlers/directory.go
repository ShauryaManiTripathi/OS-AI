package handlers

import (
	"net/http"
	"strconv"

	"github.com/labstack/echo/v4"
	"fileAPI/services"
)

type DirectoryHandler struct {
	sessionManager *services.SessionManager
	dirService     *services.DirectoryService
}

func NewDirectoryHandler(sm *services.SessionManager) *DirectoryHandler {
	return &DirectoryHandler{
		sessionManager: sm,
		dirService:     services.NewDirectoryService(sm),
	}
}

func (h *DirectoryHandler) ListDirectories(c echo.Context) error {
	sessionID := c.Param("sessionId")
	path := c.QueryParam("path")
	if path == "" {
		path = "."
	}
	
	dirs, err := h.dirService.ListDirectories(sessionID, path)
	if err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{
			"error": err.Error(),
		})
	}
	
	return c.JSON(http.StatusOK, map[string]interface{}{
		"path":        path,
		"directories": dirs,
	})
}

func (h *DirectoryHandler) CreateDirectory(c echo.Context) error {
	sessionID := c.Param("sessionId")
	path := c.Param("*")
	
	if err := h.dirService.CreateDirectory(sessionID, path); err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{
			"error": err.Error(),
		})
	}
	
	return c.JSON(http.StatusCreated, map[string]string{
		"message": "Directory created successfully",
		"path":    path,
	})
}

func (h *DirectoryHandler) DeleteDirectory(c echo.Context) error {
	sessionID := c.Param("sessionId")
	path := c.Param("*")
	
	if err := h.dirService.DeleteDirectory(sessionID, path); err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{
			"error": err.Error(),
		})
	}
	
	return c.NoContent(http.StatusNoContent)
}

// New method to get directory tree
func (h *DirectoryHandler) GetDirectoryTree(c echo.Context) error {
	sessionID := c.Param("sessionId")
	path := c.QueryParam("path")
	if path == "" {
		path = "."
	}
	
	depthStr := c.QueryParam("depth")
	depth := 2 // Default
	if depthStr != "" {
		if val, err := strconv.Atoi(depthStr); err == nil {
			depth = val
		}
	}
	
	tree, err := h.dirService.GetDirectoryTree(sessionID, path, depth)
	if err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{
			"error": err.Error(),
		})
	}
	
	return c.JSON(http.StatusOK, map[string]interface{}{
		"path": path,
		"tree": tree,
	})
}

// New method to get directory size
func (h *DirectoryHandler) GetDirectorySize(c echo.Context) error {
	sessionID := c.Param("sessionId")
	path := c.Param("*")
	
	size, err := h.dirService.CalculateDirectorySize(sessionID, path)
	if err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{
			"error": err.Error(),
		})
	}
	
	return c.JSON(http.StatusOK, map[string]interface{}{
		"path": path,
		"size": size,
		"sizeFormatted": formatSize(size),
	})
}

// Helper function to format size
func formatSize(size int64) string {
	const (
		B  = 1
		KB = 1024 * B
		MB = 1024 * KB
		GB = 1024 * MB
	)
	
	switch {
	case size >= GB:
		return strconv.FormatFloat(float64(size)/float64(GB), 'f', 2, 64) + " GB"
	case size >= MB:
		return strconv.FormatFloat(float64(size)/float64(MB), 'f', 2, 64) + " MB"
	case size >= KB:
		return strconv.FormatFloat(float64(size)/float64(KB), 'f', 2, 64) + " KB"
	default:
		return strconv.FormatInt(size, 10) + " bytes"
	}
}
