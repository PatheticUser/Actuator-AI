#!/bin/bash

# Actuator AI Unified Run Script
# Starts both backend and frontend servers

echo "Starting Actuator AI..."

# Function to cleanup background processes on exit
cleanup() {
    echo "Stopping servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend server
echo "Starting backend server on port 8000..."
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend server
echo "Starting frontend server on port 5173..."
cd frontend && npm run dev &
FRONTEND_PID=$!

# Wait for both processes
echo "Servers starting..."
echo "Backend: http://127.0.0.1:8000"
echo "Frontend: http://localhost:5173"
echo "API Docs: http://127.0.0.1:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"

wait $BACKEND_PID $FRONTEND_PID