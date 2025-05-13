#!/bin/bash

# This script builds the terminalAPI application

# Check if Go is installed
if ! command -v go &> /dev/null; then
    echo "Error: Go is not installed. Please install Go first."
    exit 1
fi

# Navigate to the project directory
cd "$(dirname "$0")/.."

# Download dependencies
echo "Downloading dependencies..."
go mod download

# Build the project with version info
echo "Building terminalAPI..."
GOOS=$(go env GOOS)
GOARCH=$(go env GOARCH)
VERSION="0.1.0"
BUILD_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

go build -o terminalAPI \
  -ldflags "-X main.Version=$VERSION -X main.BuildTime=$BUILD_TIME -X main.GOOS=$GOOS -X main.GOARCH=$GOARCH" \
  main.go

if [ $? -eq 0 ]; then
    echo "Build successful!"
    echo "You can run the server with: ./terminalAPI"
else
    echo "Build failed!"
    exit 1
fi
