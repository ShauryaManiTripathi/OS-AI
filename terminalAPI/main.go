package main

import (
	"github.com/labstack/echo/v4"
	"github.com/labstack/echo/v4/middleware"
	"log"
	"terminalAPI/api"
	"terminalAPI/services"
)

func main() {
	// Initialize session manager
	sessionManager := services.NewSessionManager()
	
	// Initialize the Echo instance
	e := echo.New()
	
	// Middleware
	e.Use(middleware.Logger())
	e.Use(middleware.Recover())
	e.Use(middleware.CORS())
	
	// Setup routes
	api.SetupRoutes(e, sessionManager)
	
	// Start server
	log.Println("Starting Terminal API server on port 8081...")
	e.Logger.Fatal(e.Start(":8081"))
}
