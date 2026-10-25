@echo off
setlocal
cd /d "%~dp0"
echo ============================================
echo Delhi Metro Route Planner - EXE Builder
echo ============================================
where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install Python 3 from https://www.python.org/downloads/
  pause
  exit /b 1
)
echo Installing PyInstaller...
python -m pip install --user pyinstaller
if errorlevel 1 (
  echo PyInstaller installation failed.
  pause
  exit /b 1
)
echo Building the standalone application...
python -m PyInstaller --noconfirm --clean --onedir --name DelhiMetroPlanner --add-data "frontend;frontend" --add-data "data;data" backend\app.py
if errorlevel 1 (
  echo Build failed. Read the error above.
  pause
  exit /b 1
)
echo.
echo Build complete.
echo The distributable folder is: dist\DelhiMetroPlanner
 echo Zip the ENTIRE DelhiMetroPlanner folder, not just the EXE.
echo Test dist\DelhiMetroPlanner\DelhiMetroPlanner.exe before sharing.
pause
