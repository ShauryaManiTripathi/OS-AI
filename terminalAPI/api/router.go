package api

import (
	"github.com/labstack/echo/v4"
	"terminalAPI/api/handlers"
	"terminalAPI/services"
)

func SetupRoutes(e *echo.Echo, sm *services.SessionManager) {
	// Create services
	hs := services.NewHistoryService(1000)
	cs := services.NewCommandService(sm, hs)
	ps := services.NewProcessService(sm, hs)
	es := services.NewEnvService(sm)
	
	// Create handlers
	sessionHandler := handlers.NewSessionHandler(sm)
	commandHandler := handlers.NewCommandHandler(cs)
	processHandler := handlers.NewProcessHandler(ps)
	envHandler := handlers.NewEnvHandler(es)
	historyHandler := handlers.NewHistoryHandler(hs)
	systemHandler := handlers.NewSystemHandler()
	
	// Session routes
	e.POST("/sessions", sessionHandler.CreateSession)
	e.GET("/sessions/:sessionId", sessionHandler.GetSession)
	e.DELETE("/sessions/:sessionId", sessionHandler.DeleteSession)
	e.PUT("/sessions/:sessionId/cwd", sessionHandler.SetWorkingDirectory)
	e.GET("/sessions", sessionHandler.ListSessions)
	
	// Command routes
	e.POST("/sessions/:sessionId/commands", commandHandler.ExecuteCommand)
	e.POST("/sessions/:sessionId/commands/batch", commandHandler.ExecuteBatchCommands)
	
	// Process routes
	e.POST("/sessions/:sessionId/processes", processHandler.StartProcess)
	e.GET("/sessions/:sessionId/processes", processHandler.ListProcesses)
	e.GET("/sessions/:sessionId/processes/:processId", processHandler.GetProcess)
	e.GET("/sessions/:sessionId/processes/:processId/output", processHandler.GetProcessOutput)
	e.POST("/sessions/:sessionId/processes/:processId/input", processHandler.SendProcessInput)
	e.POST("/sessions/:sessionId/processes/:processId/signal", processHandler.SignalProcess)
	
	// Environment routes
	e.GET("/sessions/:sessionId/env", envHandler.GetEnvVars)
	e.PUT("/sessions/:sessionId/env", envHandler.SetBatchEnvVars)
	e.PUT("/sessions/:sessionId/env/:key", envHandler.SetEnvVar)
	e.DELETE("/sessions/:sessionId/env/:key", envHandler.UnsetEnvVar)
	
	// History routes
	e.GET("/sessions/:sessionId/history", historyHandler.GetHistory)
	e.GET("/sessions/:sessionId/history/search", historyHandler.SearchHistory)
	e.DELETE("/sessions/:sessionId/history", historyHandler.ClearHistory)
	
	// System routes
	e.GET("/system/info", systemHandler.GetSystemInfo)
	e.GET("/system/shells", systemHandler.GetAvailableShells)
}
