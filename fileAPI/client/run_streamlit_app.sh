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

# Run the Streamlit application
echo "Starting FileAPI Streamlit app..."
streamlit run fileapi_streamlit_tester.py --server.port=8501
