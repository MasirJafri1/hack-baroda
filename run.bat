@echo off
title Hindsight DevOps Pipeline Agent Starter
echo =======================================================================
echo               Hindsight DevOps Pipeline Agent Starter                  
echo =======================================================================
echo.

echo [*] Starting Backend Server (FastAPI/uvicorn)...
start "Hindsight Backend" cmd /k "cd Backend && ..\venv\Scripts\python.exe -m uvicorn server:app --reload --host 0.0.0.0 --port 8000"

echo [*] Starting Frontend Server (Vite/React)...
start "Hindsight Frontend" cmd /k "cd Frontend && npm run dev"

echo.
echo =======================================================================
echo [OK] Both servers started in separate terminal windows!
echo      - Backend running at:  http://localhost:8000
echo      - Frontend running at: http://localhost:5173
echo =======================================================================
echo.
pause
