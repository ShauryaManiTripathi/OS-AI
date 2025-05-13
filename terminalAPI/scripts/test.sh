#!/bin/bash

# This script runs the test suite for terminalAPI

# Check if Go is installed
if ! command -v go &> /dev/null; then
    echo "Error: Go is not installed. Please install Go first."
    exit 1
fi

# Navigate to the project directory
cd "$(dirname "$0")/.."

# Run tests with coverage
echo "Running tests with coverage..."
go test -v -cover ./...

# Generate coverage report
if [ "$1" == "--html" ]; then
    echo "Generating HTML coverage report..."
    go test -coverprofile=coverage.out ./...
    go tool cover -html=coverage.out -o coverage.html
    echo "Coverage report generated: coverage.html"
    
    # Open coverage report in browser if possible
    if command -v xdg-open &> /dev/null; then
        xdg-open coverage.html
    elif command -v open &> /dev/null; then
        open coverage.html
    else
        echo "Open coverage.html in your browser to view the report"
    fi
fi
