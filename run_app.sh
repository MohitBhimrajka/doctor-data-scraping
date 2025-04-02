#!/bin/bash

# ANSI color codes for formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to display section headers
function section() {
    echo -e "\n${BLUE}=============================================${NC}"
    echo -e "${BLUE}   $1${NC}"
    echo -e "${BLUE}=============================================${NC}\n"
}

# Function to display success messages
function success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Function to display warning messages
function warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Function to display error messages
function error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to display info messages
function info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

# Function to display step messages
function step() {
    echo -e "${MAGENTA}▶️  $1${NC}"
}

# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    error "Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null
then
    error "Node.js is not installed. Please install Node.js and try again."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null
then
    error "npm is not installed. Please install npm and try again."
    exit 1
fi

section "DOCTOR SEARCH APPLICATION STARTUP"

info "Environment setup in progress..."

# Load environment variables
if [ -f .env ]; then
    step "Loading environment variables from .env file"
    source .env
else
    warning "No .env file found in the root directory"
    
    # Check if GEMINI_API_KEY is set
    if [ -z "$GEMINI_API_KEY" ]; then
        error "GEMINI_API_KEY environment variable is not set."
        echo "Please create a .env file in the root directory with the following content:"
        echo "GEMINI_API_KEY=your_gemini_api_key_here"
        echo "You can get an API key from https://ai.google.dev/"
        exit 1
    fi
fi

# Delete the database file if it exists to ensure schema consistency
if [ -f doctors.db ]; then
    step "Removing old database file"
    rm doctors.db
    success "Old database removed successfully"
fi

# Install backend dependencies
section "SETTING UP BACKEND"
step "Installing backend dependencies"
pip install -r requirements.txt
success "Backend dependencies installed successfully"

# Install frontend dependencies
section "SETTING UP FRONTEND"
step "Installing frontend dependencies"
cd frontend && npm install
success "Frontend dependencies installed successfully"
cd ..

# Start the backend server in the background
section "STARTING BACKEND SERVER"
step "Starting backend server on http://localhost:8000"
python server.py &
BACKEND_PID=$!

# Wait for the backend to start
sleep 3

# Start the frontend server in the foreground
section "STARTING FRONTEND SERVER"
step "Starting frontend server on http://localhost:3000"
cd frontend && npm run dev &
FRONTEND_PID=$!

# Print helpful message
section "APPLICATION STARTUP COMPLETE"
success "Doctor Search App is running!"
echo -e "⭐ Backend API: ${GREEN}http://localhost:8000${NC}"
echo -e "⭐ Frontend UI: ${GREEN}http://localhost:3000${NC}"
echo
info "Press Ctrl+C to stop both servers"

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID 