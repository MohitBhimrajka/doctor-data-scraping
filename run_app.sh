#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_message() {
    echo -e "${2}${1}${NC}"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    if command_exists python3; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        # Split version into major and minor
        MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
        
        if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 8 ]; then
            print_message "Python version $PYTHON_VERSION detected" "$GREEN"
            return 0
        else
            print_message "Python version $PYTHON_VERSION detected. Version 3.8 or higher is required." "$RED"
            return 1
        fi
    else
        print_message "Python 3 is not installed" "$RED"
        return 1
    fi
}

# Function to create and activate virtual environment
setup_virtual_env() {
    if [ ! -d "venv" ]; then
        print_message "Creating virtual environment..." "$YELLOW"
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    print_message "Upgrading pip..." "$YELLOW"
    pip install --upgrade pip
}

# Function to install dependencies
install_dependencies() {
    print_message "Installing dependencies..." "$YELLOW"
    
    # Install backend dependencies
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    fi
    
    # Install frontend dependencies
    if [ -f "frontend/app/requirements.txt" ]; then
        pip install -r frontend/app/requirements.txt
    fi
}

# Function to check environment variables
check_env_vars() {
    if [ ! -f ".env" ]; then
        print_message "Creating .env file from template..." "$YELLOW"
        cp .env.example .env
        print_message "Please update the .env file with your configuration" "$YELLOW"
        exit 1
    fi
}

# Function to run API validation tests
run_api_tests() {
    print_message "Running API validation tests..." "$YELLOW"
    # Set PYTHONPATH to include the project root
    export PYTHONPATH=$PYTHONPATH:$(pwd)
    
    # Run backend tests
    print_message "Running backend tests..." "$YELLOW"
    if python3 -m pytest backend/tests/ -v; then
        print_message "Backend tests passed!" "$GREEN"
    else
        print_message "Warning: Backend tests failed. The application may not work correctly." "$RED"
        print_message "Do you want to continue anyway? (y/n)" "$YELLOW"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            return 0
        else
            return 1
        fi
    fi
    
    # Run frontend tests
    print_message "Running frontend tests..." "$YELLOW"
    if python3 -m pytest frontend/app/tests/ -v; then
        print_message "Frontend tests passed!" "$GREEN"
    else
        print_message "Warning: Frontend tests failed. The application may not work correctly." "$RED"
        print_message "Do you want to continue anyway? (y/n)" "$YELLOW"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            return 0
        else
            return 1
        fi
    fi
}

# Function to start the backend server
start_backend() {
    print_message "Starting backend server..." "$YELLOW"
    cd backend
    uvicorn main:app --reload --port 8000 &
    BACKEND_PID=$!
    cd ..
}

# Function to start the frontend server
start_frontend() {
    print_message "Starting frontend server..." "$YELLOW"
    cd frontend/app
    streamlit run main.py --server.port 8501 &
    FRONTEND_PID=$!
    cd ../..
}

# Function to handle cleanup on exit
cleanup() {
    print_message "\nShutting down servers..." "$YELLOW"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    deactivate
    print_message "Servers stopped" "$GREEN"
    exit 0
}

# Set up trap for cleanup
trap cleanup SIGINT SIGTERM

# Main script
print_message "Starting Doctor Discovery Application..." "$GREEN"

# Check Python version
if ! check_python_version; then
    exit 1
fi

# Setup virtual environment
setup_virtual_env

# Install dependencies
install_dependencies

# Check environment variables
check_env_vars

# Run API validation tests
if ! run_api_tests; then
    print_message "Exiting due to API validation test failure" "$RED"
    exit 1
fi

# Start servers
start_backend
start_frontend

print_message "\nApplication started successfully!" "$GREEN"
print_message "Backend running at: http://localhost:8000" "$GREEN"
print_message "Frontend running at: http://localhost:8501" "$GREEN"
print_message "\nPress Ctrl+C to stop the servers" "$YELLOW"

# Wait for user input
wait 