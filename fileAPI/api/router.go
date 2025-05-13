package api

import (
	"github.com/labstack/echo/v4"
	"fileAPI/api/handlers"
	"fileAPI/services"
)

func SetupRoutes(e *echo.Echo, sm *services.SessionManager) {
	// Create handlers
	sessionHandler := handlers.NewSessionHandler(sm)
	fileHandler := handlers.NewFileHandler(sm)
	dirHandler := handlers.NewDirectoryHandler(sm)
	diffHandler := handlers.NewDiffHandler(sm)
	projectHandler := handlers.NewProjectHandler(sm)
	
	// Session routes
	e.POST("/sessions", sessionHandler.CreateSession)
	e.GET("/sessions/:sessionId", sessionHandler.GetSession)
	e.DELETE("/sessions/:sessionId", sessionHandler.DeleteSession)
	e.PUT("/sessions/:sessionId/cwd", sessionHandler.SetWorkingDirectory)
	e.GET("/sessions", sessionHandler.ListSessions) // New endpoint for listing all sessions
	
	// File routes
	e.GET("/sessions/:sessionId/files", fileHandler.ListFiles)
	e.GET("/sessions/:sessionId/files/*", fileHandler.GetFile)
	e.POST("/sessions/:sessionId/files/*", fileHandler.CreateFile)
	e.PUT("/sessions/:sessionId/files/*", fileHandler.UpdateFile)
	e.DELETE("/sessions/:sessionId/files/*", fileHandler.DeleteFile)
	e.GET("/sessions/:sessionId/files-metadata", fileHandler.ListFilesWithMetadata) // New endpoint for metadata
	e.GET("/sessions/:sessionId/file-metadata/*", fileHandler.GetFileMetadata) // New endpoint for single file metadata
	
	// Directory routes
	e.GET("/sessions/:sessionId/directories", dirHandler.ListDirectories)
	e.POST("/sessions/:sessionId/directories/*", dirHandler.CreateDirectory)
	e.DELETE("/sessions/:sessionId/directories/*", dirHandler.DeleteDirectory)
	e.GET("/sessions/:sessionId/directory-tree", dirHandler.GetDirectoryTree) // New endpoint for directory tree
	e.GET("/sessions/:sessionId/directory-size/*", dirHandler.GetDirectorySize) // New endpoint for directory size
	
	// Diff and patch routes
	e.POST("/sessions/:sessionId/diff", diffHandler.GenerateDiff)
	e.POST("/sessions/:sessionId/patch", diffHandler.ApplyPatch)
	
	// Project routes (new)
	e.GET("/sessions/:sessionId/project", projectHandler.GetProjectSummary)
	e.GET("/sessions/:sessionId/project/context", projectHandler.ExtractCodeContext)
	e.GET("/sessions/:sessionId/project/structure", projectHandler.ExportFileStructure)
	e.POST("/sessions/:sessionId/project/batch-create", projectHandler.BatchCreateFiles)
	
	// Utility endpoints for LLMs
	e.POST("/sessions/:sessionId/extract", fileHandler.ExtractContent)
	e.POST("/sessions/:sessionId/search", fileHandler.SearchContent)
	e.POST("/sessions/:sessionId/batch-read", fileHandler.BatchReadFiles) // New endpoint for reading multiple files
}
