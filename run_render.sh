#!/bin/bash

# Start the backend server in the background on port 8000
python server.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Start the frontend on the PORT provided by Render
cd streamlit-frontend && streamlit run app_streamlit.py --server.port $PORT --server.address 0.0.0.0 --browser.serverAddress 0.0.0.0 --browser.serverPort $PORT
FRONTEND_PID=$!

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID 