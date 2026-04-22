@echo off
echo Starting Actuator AI...

REM Start backend server in new window
echo Starting backend server on port 8000...
start "Actuator Backend" python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend server in new window
echo Starting frontend server on port 5173...
cd frontend
start "Actuator Frontend" npm run dev

cd ..
echo.
echo Servers started:
echo Backend: http://127.0.0.1:8000
echo Frontend: http://localhost:5173
echo API Docs: http://127.0.0.1:8000/docs
echo.
echo Close windows to stop servers