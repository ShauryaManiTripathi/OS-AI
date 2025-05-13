package handlers

import (
	"net/http"
	"github.com/labstack/echo/v4"
	"fileAPI/services"
)

type FileRequest struct {
	Content string `json:"content"`
}

type BatchReadRequest struct {
	Files []string `json:"files"`
}

type BatchFilesRequest struct {
	Files map[string]string `json:"files"`
}

type SearchRequest struct {
	Pattern   string `json:"pattern"`
	Path      string `json:"path"`
	Recursive bool   `json:"recursive"`
}

type FileHandler struct {
	sessionManager *services.SessionManager
	fileService    *services.FileService
}

func NewFileHandler(sm *services.SessionManager) *FileHandler {
	return &FileHandler{
		sessionManager: sm,
		fileService:    services.NewFileService(sm),
	}
}

func (h *FileHandler) GetFile(c echo.Context) error {
	sessionID := c.Param("sessionId")
	path := c.Param("*")
	
	content, err := h.fileService.ReadFile(sessionID, path)
	if err != nil {
		return c.JSON(http.StatusNotFound, map[string]string{
			"error": err.Error(),
		})
	}
	
	return c.JSON(http.StatusOK, map[string]string{
		"path":    path,
		"content": string(content),
	})
}

func (h *FileHandler) ListFiles(c echo.Context) error {
	sessionID := c.Param("sessionId")
	path := c.QueryParam("path")
	if path == "" {
		path = "."
	}
	
	files, err := h.fileService.ListFiles(sessionID, path)
	if err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{
			"error": err.Error(),
		})
	}
	
	return c.JSON(http.StatusOK, map[string]interface{}{
		"path":  path,
		"files": files,
	})
}

func (h *FileHandler) CreateFile(c echo.Context) error {
	sessionID := c.Param("sessionId")
	path := c.Param("*")
	
	var req FileRequest
	if err := c.Bind(&req); err != nil {
		return c.JSON(http.StatusBadRequest, map[string]string{
			"error": "Invalid request body",
		})
	}
	
	if err := h.fileService.CreateFile(sessionID, path, []byte(req.Content)); err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{
			"error": err.Error(),
		})
	}
	
	return c.JSON(http.StatusCreated, map[string]string{
		"message": "File created successfully",
		"path":    path,
	})
}

func (h *FileHandler) UpdateFile(c echo.Context) error {
	sessionID := c.Param("sessionId")
	path := c.Param("*")
	
	var req FileRequest
	if err := c.Bind(&req); err != nil {
		return c.JSON(http.StatusBadRequest, map[string]string{
			"error": "Invalid request body",
		})
	}
	
	if err := h.fileService.UpdateFile(sessionID, path, []byte(req.Content)); err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{
			"error": err.Error(),
		})
	}
	
	return c.JSON(http.StatusOK, map[string]string{
		"message": "File updated successfully",
		"path":    path,
	})
}

func (h *FileHandler) DeleteFile(c echo.Context) error {
	sessionID := c.Param("sessionId")
	path := c.Param("*")
	
	if err := h.fileService.DeleteFile(sessionID, path); err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{
			"error": err.Error(),
		})
	}
	
	return c.NoContent(http.StatusNoContent)
}

// Utility specifically for LLM assistance
func (h *FileHandler) ExtractContent(c echo.Context) error {
	sessionID := c.Param("sessionId")
	
	type ExtractRequest struct {
		Files []string `json:"files"`
	}
	
	var req ExtractRequest
	if err := c.Bind(&req); err != nil {
		return c.JSON(http.StatusBadRequest, map[string]string{
			"error": "Invalid request body",
		})
	}
	
	result := make(map[string]string)
	for _, path := range req.Files {
		content, err := h.fileService.ReadFile(sessionID, path)
		if err != nil {
			result[path] = "ERROR: " + err.Error()
		} else {
			result[path] = string(content)
		}
	}
	
	return c.JSON(http.StatusOK, result)
}

// Search for content in files
func (h *FileHandler) SearchContent(c echo.Context) error {
	sessionID := c.Param("sessionId")
	
	var req SearchRequest
	if err := c.Bind(&req); err != nil {
		return c.JSON(http.StatusBadRequest, map[string]string{
			"error": "Invalid request body",
		})
	}
	
	if req.Path == "" {
		req.Path = "."
	}
	
	results, err := h.fileService.SearchInFiles(sessionID, req.Path, req.Pattern, req.Recursive)
	if err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{
			"error": err.Error(),
		})
	}
	
	return c.JSON(http.StatusOK, map[string]interface{}{
		"pattern":       req.Pattern,
		"path":          req.Path,
		"recursive":     req.Recursive,
		"matchedFiles":  len(results),
		"results":       results,
	})
}

// New method to list files with metadata
func (h *FileHandler) ListFilesWithMetadata(c echo.Context) error {
	sessionID := c.Param("sessionId")
	path := c.QueryParam("path")
	if path == "" {
		path = "."
	}
	
	files, err := h.fileService.ListFilesWithMetadata(sessionID, path)
	if err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{
			"error": err.Error(),
		})
	}
	
	return c.JSON(http.StatusOK, map[string]interface{}{
		"path":  path,
		"files": files,
	})
}

// New method to get file metadata
func (h *FileHandler) GetFileMetadata(c echo.Context) error {
	sessionID := c.Param("sessionId")
	path := c.Param("*")
	
	metadata, err := h.fileService.GetFileMetadata(sessionID, path)
	if err != nil {
		return c.JSON(http.StatusNotFound, map[string]string{
			"error": err.Error(),
		})
	}
	
	return c.JSON(http.StatusOK, metadata)
}

// New method for batch reading files
func (h *FileHandler) BatchReadFiles(c echo.Context) error {
	sessionID := c.Param("sessionId")
	
	var req BatchReadRequest
	if err := c.Bind(&req); err != nil {
		return c.JSON(http.StatusBadRequest, map[string]string{
			"error": "Invalid request body",
		})
	}
	
	results := h.fileService.BatchReadFiles(sessionID, req.Files)
	
	return c.JSON(http.StatusOK, map[string]interface{}{
		"results": results,
	})
}
