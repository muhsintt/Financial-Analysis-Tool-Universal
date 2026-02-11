@echo off
REM User Isolation Setup Script for Windows
REM Run this script to enable user data isolation

echo Financial Analysis Tool - User Isolation Setup
echo ==============================================
echo.

REM Navigate to backend directory
cd /d "%~dp0backend"

REM Run Python setup script
python setup_user_isolation.py

echo.
echo Setup completed!
echo.
echo You can now run the application and each user will only see their own data:
echo - Transactions
echo - Categories (+ shared system categories)  
echo - Budgets
echo - Categorization rules
echo - File uploads
echo.
echo New users will automatically get default categories when created.
echo.

pause