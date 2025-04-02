#!/bin/bash

# Start the backend server in the background on port 8000
python server.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Start the frontend server on the PORT provided by Render
cd frontend && node server.js &
FRONTEND_PID=$!

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID 