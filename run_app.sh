#!/bin/bash

# Function to handle process cleanup on exit
cleanup() {
    echo "Stopping backend and frontend processes..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set up trap to catch signals
trap cleanup SIGINT SIGTERM

# Load environment variables
source .env 2>/dev/null

# Check if GEMINI_API_KEY is set
if [ -z "$GEMINI_API_KEY" ] || [ "$GEMINI_API_KEY" = "your_gemini_api_key_here" ]; then
    echo "ERROR: GEMINI_API_KEY is not properly set in your .env file."
    echo "Please edit the .env file and set a valid Gemini API key."
    echo "You can get an API key from https://ai.google.dev/"
    exit 1
fi

# Check if backend URL is specified
BACKEND_URL=${1:-http://localhost:8000}
echo "Using backend URL: $BACKEND_URL"

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Start the backend server
echo "Starting FastAPI backend..."
python server.py &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 5

# Start the frontend
echo "Starting Streamlit frontend..."
cd streamlit-frontend && BACKEND_API_URL=$BACKEND_URL streamlit run app_streamlit.py &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

echo "Application is running!"
echo "Backend: $BACKEND_URL"
echo "Frontend: http://localhost:8501"
echo "Press Ctrl+C to stop both services"

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID 