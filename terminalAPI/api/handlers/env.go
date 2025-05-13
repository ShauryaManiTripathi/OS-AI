package handlers

import (
	"net/http"

	"github.com/labstack/echo/v4"
	"terminalAPI/services"
)

type EnvHandler struct {
	envService *services.EnvService
}

type EnvVarRequest struct {
	Value string `json:"value"`
}

type BatchEnvVarsRequest struct {
	Variables map[string]string `json:"variables"`
}

func NewEnvHandler(es *services.EnvService) *EnvHandler {
	return &EnvHandler{
		envService: es,
	}
}

func (h *EnvHandler) GetEnvVars(c echo.Context) error {
	sessionID := c.Param("sessionId")
	
	envVars, err := h.envService.GetEnvVars(sessionID)
	if err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{
			"error": err.Error(),
		})
	}
	
	return c.JSON(http.StatusOK, envVars)
}

func (h *EnvHandler) SetEnvVar(c echo.Context) error {
	sessionID := c.Param("sessionId")
	key := c.Param("key")
	
	var req EnvVarRequest
	if err := c.Bind(&req); err != nil {
		return c.JSON(http.StatusBadRequest, map[string]string{
			"error": "Invalid request body",
		})
	}
	
	if err := h.envService.SetEnvVar(sessionID, key, req.Value); err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{
			"error": err.Error(),
		})
	}
	
	return c.JSON(http.StatusOK, map[string]string{
		"message": "Environment variable set",
	})
}

func (h *EnvHandler) UnsetEnvVar(c echo.Context) error {
	sessionID := c.Param("sessionId")
	key := c.Param("key")
	
	if err := h.envService.UnsetEnvVar(sessionID, key); err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{
			"error": err.Error(),
		})
	}
	
	return c.JSON(http.StatusOK, map[string]string{
		"message": "Environment variable unset",
	})
}

func (h *EnvHandler) SetBatchEnvVars(c echo.Context) error {
	sessionID := c.Param("sessionId")
	
	var req BatchEnvVarsRequest
	if err := c.Bind(&req); err != nil {
		return c.JSON(http.StatusBadRequest, map[string]string{
			"error": "Invalid request body",
		})
	}
	
	if err := h.envService.SetBatchEnvVars(sessionID, req.Variables); err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{
			"error": err.Error(),
		})
	}
	
	return c.JSON(http.StatusOK, map[string]string{
		"message": "Environment variables set",
	})
}
