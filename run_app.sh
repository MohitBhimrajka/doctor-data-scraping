#!/bin/bash

# Define colors for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print styled message
print_message() {
    color_var=$1
    message=$2
    
    case "$color_var" in
        "GREEN") echo -e "${GREEN}${message}${NC}" ;;
        "BLUE") echo -e "${BLUE}${message}${NC}" ;;
        "RED") echo -e "${RED}${message}${NC}" ;;
        "YELLOW") echo -e "${YELLOW}${message}${NC}" ;;
        *) echo -e "${message}" ;;
    esac
}

# Function to handle process cleanup on exit
cleanup() {
    print_message "YELLOW" "\nStopping backend and frontend processes..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set up trap to catch signals
trap cleanup SIGINT SIGTERM

# Define virtual environment directory
VENV_DIR="venv"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    print_message "BLUE" "Creating virtual environment in $VENV_DIR directory..."
    python -m venv $VENV_DIR
    if [ $? -ne 0 ]; then
        print_message "RED" "Failed to create virtual environment. Please make sure Python is installed."
        exit 1
    fi
    print_message "GREEN" "Virtual environment created successfully!"
fi

# Activate virtual environment
print_message "BLUE" "Activating virtual environment..."
source "$VENV_DIR/bin/activate"
if [ $? -ne 0 ]; then
    print_message "RED" "Failed to activate virtual environment."
    exit 1
fi
print_message "GREEN" "Virtual environment activated successfully!"

# Load environment variables
source .env 2>/dev/null

# Check if GEMINI_API_KEY is set
if [ -z "$GEMINI_API_KEY" ] || [ "$GEMINI_API_KEY" = "your_gemini_api_key_here" ]; then
    print_message "RED" "ERROR: GEMINI_API_KEY is not properly set in your .env file."
    print_message "YELLOW" "Please edit the .env file and set a valid Gemini API key."
    print_message "YELLOW" "You can get an API key from https://ai.google.dev/"
    exit 1
fi

# Check if backend URL is specified
BACKEND_URL=${1:-http://localhost:8000}
print_message "BLUE" "Using backend URL: $BACKEND_URL"

# Install dependencies
print_message "BLUE" "Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    print_message "RED" "Failed to install dependencies."
    exit 1
fi
print_message "GREEN" "Dependencies installed successfully!"

# Start the backend server
print_message "BLUE" "Starting FastAPI backend..."
python server.py &
BACKEND_PID=$!
print_message "GREEN" "Backend started with PID: $BACKEND_PID"

# Wait for backend to start
print_message "YELLOW" "Waiting for backend to start..."
sleep 5

# Start the frontend
print_message "BLUE" "Starting Streamlit frontend..."
cd streamlit-frontend && BACKEND_API_URL=$BACKEND_URL streamlit run app_streamlit.py &
FRONTEND_PID=$!
print_message "GREEN" "Frontend started with PID: $FRONTEND_PID"

print_message "GREEN" "====================================================="
print_message "GREEN" "Application is running!"
print_message "GREEN" "Backend: $BACKEND_URL"
print_message "GREEN" "Frontend: http://localhost:8501"
print_message "YELLOW" "Press Ctrl+C to stop both services"
print_message "GREEN" "====================================================="

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID 