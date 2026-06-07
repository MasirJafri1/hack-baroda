@echo off
title Hindsight Docker Builder
echo =======================================================================
echo              Hindsight DevOps Pipeline Agent Docker Builder            
echo =======================================================================
echo.

echo [*] Building Docker image 'hindsight-agent:latest'...
docker build -t hindsight-agent:latest .

echo.
echo =======================================================================
echo [OK] Docker image built successfully!
echo.
echo      To run the container locally with your env configuration:
echo      docker run -d -p 8000:8000 --env-file Backend/.env --name hindsight-container hindsight-agent:latest
echo.
echo      You can access the full app at: http://localhost:8000
echo =======================================================================
echo.
pause
