package handlers

import (
	"net/http"

	"github.com/labstack/echo/v4"
	"fileAPI/services"
)

type SessionRequest struct {
	WorkingDirectory string `json:"workingDirectory"`
}

type SessionHandler struct {
	sessionManager *services.SessionManager
}

func NewSessionHandler(sm *services.SessionManager) *SessionHandler {
	return &SessionHandler{
		sessionManager: sm,
	}
}

func (h *SessionHandler) CreateSession(c echo.Context) error {
	session, err := h.sessionManager.CreateSession()
	if err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{
			"error": err.Error(),
		})
	}
	
	return c.JSON(http.StatusCreated, session)
}

func (h *SessionHandler) GetSession(c echo.Context) error {
	sessionID := c.Param("sessionId")
	
	session, err := h.sessionManager.GetSession(sessionID)
	if (err != nil) {
		return c.JSON(http.StatusNotFound, map[string]string{
			"error": err.Error(),
		})
	}
	
	return c.JSON(http.StatusOK, session)
}

func (h *SessionHandler) DeleteSession(c echo.Context) error {
	sessionID := c.Param("sessionId")
	
	if err := h.sessionManager.DeleteSession(sessionID); err != nil {
		return c.JSON(http.StatusNotFound, map[string]string{
			"error": err.Error(),
		})
	}
	
	return c.NoContent(http.StatusNoContent)
}

func (h *SessionHandler) SetWorkingDirectory(c echo.Context) error {
	sessionID := c.Param("sessionId")
	
	var req SessionRequest
	if err := c.Bind(&req); err != nil {
		return c.JSON(http.StatusBadRequest, map[string]string{
			"error": "Invalid request body",
		})
	}
	
	if err := h.sessionManager.SetWorkingDirectory(sessionID, req.WorkingDirectory); err != nil {
		return c.JSON(http.StatusBadRequest, map[string]string{
			"error": err.Error(),
		})
	}
	
	session, _ := h.sessionManager.GetSession(sessionID)
	return c.JSON(http.StatusOK, session)
}

// New method to list all sessions
func (h *SessionHandler) ListSessions(c echo.Context) error {
	sessions := h.sessionManager.GetAllSessions()
	return c.JSON(http.StatusOK, map[string]interface{}{
		"sessions": sessions,
		"count":    len(sessions),
	})
}
