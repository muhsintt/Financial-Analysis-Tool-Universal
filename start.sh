#!/bin/bash

# Expense Tracker Startup Script for macOS/Linux

echo ""
echo "========================================"
echo " Expense Tracker Application"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.8+ from https://www.python.org/"
    exit 1
fi

# Navigate to backend directory
cd "$(dirname "$0")/backend"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo ""
echo "Installing dependencies..."
pip install -q -r requirements.txt

if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies"
    exit 1
fi

# Start the application
echo ""
echo "========================================"
echo " Starting Expense Tracker..."
echo "========================================"
echo ""
echo "Application will open in your browser at:"
echo "http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the application"
echo ""

python3 run.py
