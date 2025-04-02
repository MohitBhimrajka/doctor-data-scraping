#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

echo "Starting deployment..."

# Log environment for debugging
echo "NODE_VERSION: $NODE_VERSION"
echo "PORT: $PORT"
echo "PYTHON_VERSION: $PYTHON_VERSION"

# Set default PORT if not provided by environment
export PORT=${PORT:-8000}
echo "Using PORT: $PORT"

# Start the backend server in the background
echo "Starting Python backend server..."
python server.py &
BACKEND_PID=$!

# Wait for backend to initialize
echo "Waiting for backend to initialize..."
sleep 10

# Set BACKEND_API_URL if not already set
export BACKEND_API_URL=${BACKEND_API_URL:-"http://localhost:8000"}
echo "Using BACKEND_API_URL: $BACKEND_API_URL"

# Start the frontend server
echo "Starting Node.js frontend server..."
cd frontend && node server.js &
FRONTEND_PID=$!

echo "Both servers started. Backend PID: $BACKEND_PID, Frontend PID: $FRONTEND_PID"

# Function to cleanup child processes on exit
cleanup() {
    echo "Shutting down servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    echo "Shutdown complete."
}

# Register the cleanup function for various signals
trap cleanup SIGINT SIGTERM EXIT

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID 