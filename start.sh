#!/bin/bash
# start.sh

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install dependencies
pip install -r requirements.txt

# Start the FastAPI server
uvicorn server:app --host 0.0.0.0 --port $PORT 