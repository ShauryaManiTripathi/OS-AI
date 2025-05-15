#!/bin/bash

# Check if Go is installed
if ! command -v go &> /dev/null; then
    echo "Go is not installed. Please install Go first."
    exit 1
fi

# Navigate to the project directory
cd "$(dirname "$0")/.."

# Check for --with-ui flag
WITH_UI=false
for arg in "$@"; do
    if [ "$arg" == "--with-ui" ]; then
        WITH_UI=true
    fi
done

# Download dependencies
echo "Downloading dependencies..."
go mod download

# Build the project
echo "Building project..."
go build -o fileAPI main.go

# Start the server in the background if UI requested
if [ "$WITH_UI" = true ]; then
    echo "Starting fileAPI API server on port 8080 in the background..."
    ./fileAPI &
    SERVER_PID=$!
    
    # Make sure Python requirements are installed
    if command -v pip &> /dev/null; then
        echo "Installing Python requirements..."
        pip install streamlit pandas plotly
    else
        echo "Warning: pip not found, Streamlit dependencies may not be installed."
    fi
    
    # Start the Streamlit UI
    echo "Starting Streamlit UI on port 8501..."
    cd client
    chmod +x run_streamlit_app.sh
    ./run_streamlit_app.sh
    
    # When Streamlit exits, kill the server
    kill $SERVER_PID
else
    # Start the server normally
    echo "Starting fileAPI API server on port 8080..."
    ./fileAPI
fi

# You can also use this to start without building:
# go run main.go
