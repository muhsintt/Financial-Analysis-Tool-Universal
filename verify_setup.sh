#!/bin/bash

# Installation and Setup Verification Script

echo ""
echo "========================================"
echo " Expense Tracker - Setup Verification"
echo "========================================"
echo ""

# Check Python
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed"
    echo ""
    echo "Please install Python from: https://www.python.org/downloads/"
    exit 1
else
    python3 --version
fi

echo ""
echo "Checking file structure..."

# Check required files
files=("backend/run.py" "backend/requirements.txt" "backend/app/__init__.py" "frontend/templates/index.html" "frontend/static/js/app.js" "frontend/static/css/style.css")

error=0
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "[OK] $file"
    else
        echo "[ERROR] Missing file: $file"
        error=1
    fi
done

if [ $error -eq 1 ]; then
    echo ""
    echo "[ERROR] Some files are missing. Please ensure all files are in place."
    exit 1
fi

echo ""
echo "All checks passed!"
echo ""
echo "To start the application:"
echo "  Run: ./start.sh"
echo ""
