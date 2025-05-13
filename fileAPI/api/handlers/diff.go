package handlers

import (
	"net/http"

	"github.com/labstack/echo/v4"
	"fileAPI/services"
)

type DiffHandler struct {
	sessionManager *services.SessionManager
	diffService    *services.DiffService
	fileService    *services.FileService
}

func NewDiffHandler(sm *services.SessionManager) *DiffHandler {
	fs := services.NewFileService(sm)
	return &DiffHandler{
		sessionManager: sm,
		fileService:    fs,
		diffService:    services.NewDiffService(sm, fs),
	}
}

func (h *DiffHandler) GenerateDiff(c echo.Context) error {
	sessionID := c.Param("sessionId")
	
	var req services.DiffRequest
	if err := c.Bind(&req); err != nil {
		return c.JSON(http.StatusBadRequest, map[string]string{
			"error": "Invalid request body",
		})
	}
	
	response, err := h.diffService.GenerateDiff(sessionID, &req)
	if err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{
			"error": err.Error(),
		})
	}
	
	return c.JSON(http.StatusOK, response)
}

func (h *DiffHandler) ApplyPatch(c echo.Context) error {
	sessionID := c.Param("sessionId")
	
	var req services.PatchRequest
	if err := c.Bind(&req); err != nil {
		return c.JSON(http.StatusBadRequest, map[string]string{
			"error": "Invalid request body",
		})
	}
	
	result, err := h.diffService.ApplyPatch(sessionID, &req)
	if err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{
			"error": err.Error(),
		})
	}
	
	return c.JSON(http.StatusOK, map[string]string{
		"result": result,
		"path":   req.FilePath,
	})
}
