package handlers

import (
	"net/http"
	"strconv"

	"github.com/labstack/echo/v4"
	"fileAPI/services"
)

type ProjectHandler struct {
	sessionManager *services.SessionManager
	projectService *services.ProjectService
	fileService    *services.FileService
	dirService     *services.DirectoryService
}

func NewProjectHandler(sm *services.SessionManager) *ProjectHandler {
	fs := services.NewFileService(sm)
	ds := services.NewDirectoryService(sm)
	return &ProjectHandler{
		sessionManager: sm,
		projectService: services.NewProjectService(sm, fs, ds),
		fileService:    fs,
		dirService:     ds,
	}
}

func (h *ProjectHandler) GetProjectSummary(c echo.Context) error {
	sessionID := c.Param("sessionId")
	
	summary, err := h.projectService.GetProjectSummary(sessionID)
	if err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{
			"error": err.Error(),
		})
	}
	
	return c.JSON(http.StatusOK, summary)
}

func (h *ProjectHandler) ExtractCodeContext(c echo.Context) error {
	sessionID := c.Param("sessionId")
	
	// Get max files param with default value
	maxFilesStr := c.QueryParam("maxFiles")
	maxFiles := 10 // Default
	if maxFilesStr != "" {
		if val, err := strconv.Atoi(maxFilesStr); err == nil {
			maxFiles = val
		}
	}
	
	context, err := h.projectService.ExtractCodeContext(sessionID, maxFiles)
	if err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{
			"error": err.Error(),
		})
	}
	
	return c.JSON(http.StatusOK, context)
}

func (h *ProjectHandler) ExportFileStructure(c echo.Context) error {
	sessionID := c.Param("sessionId")
	path := c.QueryParam("path")
	if path == "" {
		path = "."
	}
	
	depthStr := c.QueryParam("depth")
	depth := 3 // Default
	if depthStr != "" {
		if val, err := strconv.Atoi(depthStr); err == nil {
			depth = val
		}
	}
	
	structure, err := h.fileService.ExportFileStructure(sessionID, path, depth)
	if err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{
			"error": err.Error(),
		})
	}
	
	return c.JSON(http.StatusOK, map[string]interface{}{
		"path":      path,
		"depth":     depth,
		"structure": structure,
	})
}

func (h *ProjectHandler) GetDirectoryTree(c echo.Context) error {
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

func (h *ProjectHandler) BatchCreateFiles(c echo.Context) error {
	sessionID := c.Param("sessionId")
	
	type BatchFileRequest struct {
		Files map[string]string `json:"files"`
	}
	
	var req BatchFileRequest
	if err := c.Bind(&req); err != nil {
		return c.JSON(http.StatusBadRequest, map[string]string{
			"error": "Invalid request body",
		})
	}
	
	results := h.fileService.BatchCreateFiles(sessionID, req.Files)
	
	return c.JSON(http.StatusOK, map[string]interface{}{
		"results": results,
	})
}
