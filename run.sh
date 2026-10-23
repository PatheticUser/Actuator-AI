#!/usr/bin/env bash
set -Eeuo pipefail

# Actuator AI Unified Run Script
# Starts both backend and frontend servers

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_PID=""
FRONTEND_PID=""
CLEANED_UP=0

cd "$ROOT_DIR"

echo "Starting Actuator AI..."

# Function to cleanup background processes on exit
cleanup() {
    if [[ "$CLEANED_UP" -eq 1 ]]; then
        return
    fi
    CLEANED_UP=1
    echo "Stopping servers..."
    if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
    if [[ -n "$FRONTEND_PID" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi
    wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}

trap cleanup EXIT INT TERM

# Start backend server
echo "Starting backend server on port 8000..."
uv run uvicorn backend.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

# Give the API a moment to bind before starting the Vite proxy.
sleep 3

# Start frontend server
echo "Starting frontend server on port 5173..."
(
    cd "$ROOT_DIR/frontend"
    npm run dev -- --host 127.0.0.1
) &
FRONTEND_PID=$!

# Wait for both processes
echo "Servers starting..."
echo "Landing page: http://127.0.0.1:5173/"
echo "Login:        http://127.0.0.1:5173/login"
echo "Workspace:    http://127.0.0.1:5173/app"
echo "Chat:         http://127.0.0.1:5173/app/chat"
echo "Backend:      http://127.0.0.1:8000"
echo "API Docs: http://127.0.0.1:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"

wait "$BACKEND_PID" "$FRONTEND_PID"