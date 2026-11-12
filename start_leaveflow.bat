@echo off
echo ========================================================
echo       Starting LeaveFlow EFCG Enterprise Platform
echo ========================================================
echo.
echo [1/2] Starting FastAPI Backend on http://127.0.0.1:8000 ...
start "LeaveFlow Backend (FastAPI)" cmd /k "backend\venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload"

echo [2/2] Starting Frontend Vite Server on http://localhost:5173 ...
start "LeaveFlow Frontend (Vite)" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================================
echo LeaveFlow is running!
echo Frontend: http://localhost:5173
echo Backend API Docs: http://127.0.0.1:8000/docs
echo ========================================================
pause
