package handlers

import (
	"net/http"
	"strconv"

	"github.com/labstack/echo/v4"
	"terminalAPI/services"
)

type HistoryHandler struct {
	historyService *services.HistoryService
}

func NewHistoryHandler(hs *services.HistoryService) *HistoryHandler {
	return &HistoryHandler{
		historyService: hs,
	}
}

func (h *HistoryHandler) GetHistory(c echo.Context) error {
	sessionID := c.Param("sessionId")
	
	// Parse limit parameter
	limitStr := c.QueryParam("limit")
	limit := 0
	if limitStr != "" {
		var err error
		limit, err = strconv.Atoi(limitStr)
		if err != nil {
			return c.JSON(http.StatusBadRequest, map[string]string{
				"error": "Invalid limit parameter",
			})
		}
	}
	
	history, err := h.historyService.GetHistory(sessionID, limit)
	if err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{
			"error": err.Error(),
		})
	}
	
	return c.JSON(http.StatusOK, map[string]interface{}{
		"history": history,
		"count":   len(history),
	})
}

func (h *HistoryHandler) SearchHistory(c echo.Context) error {
	sessionID := c.Param("sessionId")
	query := c.QueryParam("query")
	
	if query == "" {
		return c.JSON(http.StatusBadRequest, map[string]string{
			"error": "Query parameter is required",
		})
	}
	
	history, err := h.historyService.SearchHistory(sessionID, query)
	if err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{
			"error": err.Error(),
		})
	}
	
	return c.JSON(http.StatusOK, map[string]interface{}{
		"history": history,
		"count":   len(history),
		"query":   query,
	})
}

func (h *HistoryHandler) ClearHistory(c echo.Context) error {
	sessionID := c.Param("sessionId")
	
	if err := h.historyService.ClearHistory(sessionID); err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{
			"error": err.Error(),
		})
	}
	
	return c.JSON(http.StatusOK, map[string]string{
		"message": "Command history cleared",
	})
}
