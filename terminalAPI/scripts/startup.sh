#!/bin/bash

# Check if Go is installed
if ! command -v go &> /dev/null; then
    echo "Go is not installed. Please install Go first."
    exit 1
fi

# Navigate to the project directory
cd "$(dirname "$0")/.."

# Download dependencies
echo "Downloading dependencies..."
go mod download

# Build the project
echo "Building project..."
go build -o terminalAPI main.go

# Verify the binary was created
if [ ! -f "./terminalAPI" ]; then
    echo "Error: Build failed to produce the terminalAPI binary"
    exit 1
fi

# Start the server
echo "Starting terminalAPI server on port 8081..."
./terminalAPI

# You can also use this to start without building:
# go run main.go
