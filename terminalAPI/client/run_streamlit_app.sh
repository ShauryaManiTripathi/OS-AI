#!/bin/bash

# Check if we're in a virtual environment, if not try to activate it
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -d ".venv" ]; then
        echo "Activating virtual environment..."
        source .venv/bin/activate
    elif [ -d "../.venv" ]; then
        echo "Activating virtual environment..."
        source ../.venv/bin/activate
    elif [ -d "venv" ]; then
        echo "Activating virtual environment..."
        source venv/bin/activate
    elif [ -d "../venv" ]; then
        echo "Activating virtual environment..."
        source ../venv/bin/activate
    else
        echo "No virtual environment found. Running without activation."
    fi
fi

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "Streamlit not found. Installing required packages..."
    pip install streamlit pandas requests
fi

# Run the Streamlit application
echo "Starting TerminalAPI Streamlit app..."
streamlit run terminal_streamlit_tester.py --server.port=8502
