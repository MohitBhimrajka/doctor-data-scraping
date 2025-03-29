#!/bin/bash

# Start the backend server in the background
python server.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Start the frontend
cd streamlit-frontend && streamlit run app_streamlit.py --server.port $PORT --server.address 0.0.0.0
FRONTEND_PID=$!

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID 