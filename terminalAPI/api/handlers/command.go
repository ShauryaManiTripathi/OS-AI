package handlers

import (
	"net/http"

	"github.com/labstack/echo/v4"
	"terminalAPI/services"
)

type CommandHandler struct {
	commandService *services.CommandService
}

func NewCommandHandler(cs *services.CommandService) *CommandHandler {
	return &CommandHandler{
		commandService: cs,
	}
}

func (h *CommandHandler) ExecuteCommand(c echo.Context) error {
	sessionID := c.Param("sessionId")
	
	var req services.CommandRequest
	if err := c.Bind(&req); err != nil {
		return c.JSON(http.StatusBadRequest, map[string]string{
			"error": "Invalid request body",
		})
	}
	
	output, err := h.commandService.ExecuteCommand(sessionID, &req)
	if err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{
			"error": err.Error(),
		})
	}
	
	return c.JSON(http.StatusOK, output)
}

func (h *CommandHandler) ExecuteBatchCommands(c echo.Context) error {
	sessionID := c.Param("sessionId")
	
	var req services.BatchCommandRequest
	if err := c.Bind(&req); err != nil {
		return c.JSON(http.StatusBadRequest, map[string]string{
			"error": "Invalid request body",
		})
	}
	
	outputs, err := h.commandService.ExecuteBatchCommands(sessionID, &req)
	if err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{
			"error": err.Error(),
		})
	}
	
	return c.JSON(http.StatusOK, map[string]interface{}{
		"results": outputs,
		"count":   len(outputs),
	})
}
