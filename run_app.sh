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

# Create test files directory
TEST_DIR="tests"
mkdir -p $TEST_DIR

# Check if doctors.db exists and prompt for deletion
if [ -f "doctors.db" ]; then
    print_message "YELLOW" "WARNING: An existing doctors.db file was detected."
    print_message "YELLOW" "If you've updated the application code and the database schema has changed,"
    print_message "YELLOW" "you should delete this file to avoid database schema errors."
    
    read -p "Do you want to delete the existing doctors.db file? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm doctors.db
        print_message "GREEN" "doctors.db has been deleted. A new database will be created when you run the application."
    else
        print_message "YELLOW" "Keeping existing doctors.db file. Note that this may cause errors if the schema has changed."
    fi
fi

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

# Create test scripts for API validation
print_message "BLUE" "Creating API validation tests..."

# Create simple Gemini test
cat > $TEST_DIR/test_gemini_simple.py << 'EOF'
import os
import sys
import asyncio
from dotenv import load_dotenv

# Add the parent directory to sys.path to allow direct import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from doctor_search_enhanced import GeminiClient

async def test_simple_prompt():
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment variables")
        return False
    
    # Create client
    client = GeminiClient(api_key, "gemini-2.0-flash")
    
    # Test generate_content
    try:
        print("Testing basic prompt...")
        response = await client.generate_content("Say hello")
        if response and len(response) > 0:
            print(f"Response received: {response[:50]}...")
            return True
        else:
            print("Empty response received")
            return False
    except Exception as e:
        print(f"Error: {type(e).__name__}: {str(e)}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_simple_prompt())
    exit(0 if result else 1)
EOF

# Create doctor search prompt test
cat > $TEST_DIR/test_doctor_prompt.py << 'EOF'
import os
import sys
import asyncio
import json
from dotenv import load_dotenv

# Add the parent directory to sys.path to allow direct import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from doctor_search_enhanced import GeminiClient, PromptManager, DataProcessor

async def test_doctor_prompt():
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment variables")
        return False
    
    # Create client
    client = GeminiClient(api_key, "gemini-2.0-flash")
    
    # Create a simple search prompt
    prompt = PromptManager._add_json_instruction(
        "site:practo.com Dermatologist doctor in Mumbai rating reviews phone number address"
    )
    
    print(f"Testing doctor search prompt...")
    
    # Test generate_content with the prompt
    try:
        response = await client.generate_content(prompt)
        print("Response received!")
        
        # Try to extract JSON data
        extracted_data = DataProcessor.extract_json_from_response(response)
        if extracted_data:
            print(f"Successfully extracted {len(extracted_data)} doctors")
            return True
        else:
            print("Could not extract JSON data from response")
            print("Raw response sample:", response[:200])
            return False
    except Exception as e:
        print(f"Error: {type(e).__name__}: {str(e)}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_doctor_prompt())
    exit(0 if result else 1)
EOF

# Create batch processing test
cat > $TEST_DIR/test_batch_processing.py << 'EOF'
import os
import sys
import asyncio
from dotenv import load_dotenv

# Add the parent directory to sys.path to allow direct import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from doctor_search_enhanced import GeminiClient

async def test_batch_processing():
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment variables")
        return False
    
    # Create client
    client = GeminiClient(api_key, "gemini-2.0-flash")
    
    # Create sample prompts
    prompts = [
        "Say hello",
        "What is 2+2?"
    ]
    
    print(f"Testing batch processing with {len(prompts)} prompts...")
    
    # Test generate_content_batch
    try:
        responses = await client.generate_content_batch(prompts)
        
        if len(responses) != len(prompts):
            print(f"Expected {len(prompts)} responses, got {len(responses)}")
            return False
            
        success = all(response is not None and len(response) > 0 for response in responses)
        if success:
            print("All batch prompts returned valid responses")
            return True
        else:
            print("Some prompts did not return valid responses")
            return False
    except Exception as e:
        print(f"Error: {type(e).__name__}: {str(e)}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_batch_processing())
    exit(0 if result else 1)
EOF

# Run API validation tests
print_message "BLUE" "Running API validation tests..."

# Test 1: Simple Gemini API test
print_message "BLUE" "Test 1: Basic Gemini API functionality"
python $TEST_DIR/test_gemini_simple.py
if [ $? -ne 0 ]; then
    print_message "RED" "ERROR: Basic Gemini API test failed. Please check your API key and internet connection."
    print_message "YELLOW" "Do you want to continue anyway? (y/n)"
    read -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    print_message "GREEN" "Basic Gemini API test passed!"
fi

# Test 2: Doctor search prompt test
print_message "BLUE" "Test 2: Doctor search prompt functionality"
python $TEST_DIR/test_doctor_prompt.py
if [ $? -ne 0 ]; then
    print_message "RED" "WARNING: Doctor search prompt test failed. Application may not return proper search results."
    print_message "YELLOW" "Continuing anyway, but expect potential issues with search functionality."
else
    print_message "GREEN" "Doctor search prompt test passed!"
fi

# Test 3: Batch processing test
print_message "BLUE" "Test 3: Batch processing functionality"
python $TEST_DIR/test_batch_processing.py
if [ $? -ne 0 ]; then
    print_message "RED" "WARNING: Batch processing test failed. Search performance may be degraded."
    print_message "YELLOW" "Continuing anyway, but expect slower search times."
else
    print_message "GREEN" "Batch processing test passed!"
fi

print_message "GREEN" "API validation tests completed!"

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