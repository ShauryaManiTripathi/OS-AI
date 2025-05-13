package handlers

import (
	"net/http"

	"github.com/labstack/echo/v4"
	"terminalAPI/services"
)

type ProcessHandler struct {
	processService *services.ProcessService
}

type ProcessInputRequest struct {
	Input string `json:"input"`
}

type ProcessSignalRequest struct {
	Signal string `json:"signal"` // SIGTERM, SIGKILL, SIGINT, SIGHUP
}

func NewProcessHandler(ps *services.ProcessService) *ProcessHandler {
	return &ProcessHandler{
		processService: ps,
	}
}

func (h *ProcessHandler) StartProcess(c echo.Context) error {
	sessionID := c.Param("sessionId")
	
	var req services.CommandRequest
	if err := c.Bind(&req); err != nil {
		return c.JSON(http.StatusBadRequest, map[string]string{
			"error": "Invalid request body",
		})
	}
	
	processInfo, err := h.processService.StartProcess(sessionID, &req)
	if err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{
			"error": err.Error(),
		})
	}
	
	return c.JSON(http.StatusCreated, processInfo)
}

func (h *ProcessHandler) GetProcess(c echo.Context) error {
	sessionID := c.Param("sessionId")
	processID := c.Param("processId")
	
	processes, err := h.processService.ListProcesses(sessionID)
	if err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{
			"error": err.Error(),
		})
	}
	
	process, exists := processes[processID]
	if !exists {
		return c.JSON(http.StatusNotFound, map[string]string{
			"error": "Process not found",
		})
	}
	
	return c.JSON(http.StatusOK, process)
}

func (h *ProcessHandler) ListProcesses(c echo.Context) error {
	sessionID := c.Param("sessionId")
	
	processes, err := h.processService.ListProcesses(sessionID)
	if err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{
			"error": err.Error(),
		})
	}
	
	return c.JSON(http.StatusOK, map[string]interface{}{
		"processes": processes,
		"count":     len(processes),
	})
}

func (h *ProcessHandler) GetProcessOutput(c echo.Context) error {
	sessionID := c.Param("sessionId")
	processID := c.Param("processId")
	
	output, err := h.processService.GetOutput(sessionID, processID)
	if err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{
			"error": err.Error(),
		})
	}
	
	return c.JSON(http.StatusOK, map[string]interface{}{
		"stdout": output.Stdout,
		"stderr": output.Stderr,
	})
}

func (h *ProcessHandler) SendProcessInput(c echo.Context) error {
	sessionID := c.Param("sessionId")
	processID := c.Param("processId")
	
	var req ProcessInputRequest
	if err := c.Bind(&req); err != nil {
		return c.JSON(http.StatusBadRequest, map[string]string{
			"error": "Invalid request body",
		})
	}
	
	err := h.processService.SendInput(sessionID, processID, req.Input)
	if err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{
			"error": err.Error(),
		})
	}
	
	return c.JSON(http.StatusOK, map[string]string{
		"message": "Input sent to process",
	})
}

func (h *ProcessHandler) SignalProcess(c echo.Context) error {
	sessionID := c.Param("sessionId")
	processID := c.Param("processId")
	
	var req ProcessSignalRequest
	if err := c.Bind(&req); err != nil {
		return c.JSON(http.StatusBadRequest, map[string]string{
			"error": "Invalid request body",
		})
	}
	
	err := h.processService.SignalProcess(sessionID, processID, req.Signal)
	if err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{
			"error": err.Error(),
		})
	}
	
	return c.JSON(http.StatusOK, map[string]string{
		"message": "Signal sent to process",
	})
}
