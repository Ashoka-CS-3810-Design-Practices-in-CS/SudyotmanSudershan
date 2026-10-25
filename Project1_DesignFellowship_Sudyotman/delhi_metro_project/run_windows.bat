@echo off
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (echo Python 3 is required. Install Python from https://www.python.org/downloads/ and retry.& pause & exit /b 1)
start "Delhi Metro Route Planner" http://127.0.0.1:5000
python backend\app.py
pause
