@echo off
REM Installation and Setup Verification Script

echo.
echo ========================================
echo  Expense Tracker - Setup Verification
echo ========================================
echo.

REM Check Python
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo.
    echo Please install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('python --version') do echo [OK] %%i
)

echo.
echo Checking file structure...

REM Check required files
setlocal enabledelayedexpansion
set "files=backend\run.py backend\requirements.txt backend\app\__init__.py frontend\templates\index.html frontend\static\js\app.js frontend\static\css\style.css"

for %%f in (%files%) do (
    if exist "%%f" (
        echo [OK] %%f
    ) else (
        echo [ERROR] Missing file: %%f
        set "error=1"
    )
)

if defined error (
    echo.
    echo [ERROR] Some files are missing. Please ensure all files are in place.
    pause
    exit /b 1
)

echo.
echo All checks passed!
echo.
echo To start the application:
echo   - Windows: Double-click start.bat
echo   - macOS/Linux: Run ./start.sh
echo.
pause
