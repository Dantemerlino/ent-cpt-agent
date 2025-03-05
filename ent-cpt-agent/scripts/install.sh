#!/bin/bash
# Installation script for ENT CPT Code Agent

# Exit on error
set -e

echo "Installing ENT CPT Code Agent..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source venv/Scripts/activate
else
    # Unix-like
    source venv/bin/activate
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Initialize default configuration if it doesn't exist
if [ ! -f "config.json" ]; then
    echo "Initializing default configuration..."
    python main.py init
fi

# Create required directories
echo "Creating required directories..."
mkdir -p data conversations

# Check if CPT codes database exists
if [ ! -f "data/CPT codes for ENT.xlsx" ]; then
    echo "WARNING: CPT codes database file not found at 'data/CPT codes for ENT.xlsx'"
    echo "Please add the database file before running the application."
fi

# Install package in development mode
echo "Installing package in development mode..."
pip install -e .

echo "Installation complete!"
echo ""
echo "To start the interactive mode, run: python main.py interactive"
echo "To start the API server, run: python main.py server"
echo "To start the web UI, run: python web_ui.py"