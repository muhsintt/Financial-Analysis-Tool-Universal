@echo off
REM Expense Tracker Startup Script for Windows

echo.
echo ========================================
echo  Expense Tracker Application
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

REM Navigate to backend directory
cd /d "%~dp0backend"

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install requirements
echo.
echo Installing dependencies...
pip install -q -r requirements.txt

if errorlevel 1 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)

REM Start the application
echo.
echo ========================================
echo  Starting Expense Tracker...
echo ========================================
echo.
echo Application will open in your browser at:
echo http://localhost:5000
echo.
echo Press Ctrl+C to stop the application
echo.

python run.py

pause
