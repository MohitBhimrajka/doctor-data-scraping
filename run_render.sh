#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

export NODE_ENV=production

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Installing Node.js dependencies..."
cd frontend && npm install && cd ..

echo "Starting deployment..."

# Log environment for debugging
echo "NODE_VERSION: $NODE_VERSION"
echo "PORT: $PORT"
echo "PYTHON_VERSION: $PYTHON_VERSION"

# Set default PORT if not provided by environment
export PORT=${PORT:-3000}
echo "Using PORT: $PORT"

# Start Python backend server
echo "Starting Python backend server..."
python server.py &
BACKEND_PID=$!

# Wait for backend to initialize
echo "Waiting for backend to initialize..."
sleep 5

# Set BACKEND_API_URL if not already set
export BACKEND_API_URL=${BACKEND_API_URL:-"http://localhost:8000"}
echo "Using BACKEND_API_URL: $BACKEND_API_URL"

# Start Node.js frontend server 
echo "Starting Node.js frontend server..."
cd frontend && NODE_ENV=production PORT=3000 node server.js &
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

# Keep the container running
wait 