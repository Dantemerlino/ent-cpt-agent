#!/bin/bash
# Script to run the ENT CPT Code Agent API and Web UI servers

# Exit on error
set -e

# Default ports
API_PORT=8000
WEB_PORT=5000
HOST="localhost"
DEBUG=false

# Process command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --api-port)
        API_PORT="$2"
        shift
        shift
        ;;
        --web-port)
        WEB_PORT="$2"
        shift
        shift
        ;;
        --host)
        HOST="$2"
        shift
        shift
        ;;
        --debug)
        DEBUG=true
        shift
        ;;
        *)
        echo "Unknown option: $key"
        echo "Usage: $0 [--api-port PORT] [--web-port PORT] [--host HOST] [--debug]"
        exit 1
        ;;
    esac
done

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source venv/Scripts/activate
else
    # Unix-like
    source venv/bin/activate
fi

# Start API server in the background
echo "Starting API server on $HOST:$API_PORT..."
python main.py server --host $HOST --port $API_PORT &
API_PID=$!

# Wait for API server to start
echo "Waiting for API server to start..."
sleep 3

# Start Web UI server
echo "Starting Web UI on $HOST:$WEB_PORT..."
export API_HOST=$HOST
export API_PORT=$API_PORT
export WEB_PORT=$WEB_PORT
export DEBUG=$DEBUG
python web_ui.py

# Clean up when Web UI is terminated
kill $API_PID