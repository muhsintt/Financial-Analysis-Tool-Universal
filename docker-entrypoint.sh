#!/bin/bash

# Docker Entrypoint Script for Financial Analysis Tool
# Ensures proper permissions and directory setup before starting the application

echo "============================================"
echo "Financial Analysis Tool - Starting Application"
echo "============================================"

# Ensure data directories exist and have correct permissions
echo "Setting up data directories..."
mkdir -p /app/backend/data /app/backend/uploads

# Check if we can write to the data directory
if [ ! -w "/app/backend/data" ]; then
    echo "ERROR: Cannot write to /app/backend/data directory"
    echo "This is likely a Docker volume permission issue"
    ls -la /app/backend/data
    exit 1
fi

if [ ! -w "/app/backend/uploads" ]; then
    echo "ERROR: Cannot write to /app/backend/uploads directory" 
    echo "This is likely a Docker volume permission issue"
    ls -la /app/backend/uploads
    exit 1
fi

echo "✓ Data directories are writable"

# Check if database exists, if not it will be created automatically
DATABASE_PATH="/app/backend/data/expense_tracker.db"
if [ -f "$DATABASE_PATH" ]; then
    echo "✓ Database found: $DATABASE_PATH"
    ls -la "$DATABASE_PATH"
else
    echo "Database will be created on first run: $DATABASE_PATH"
fi

echo "Starting application with gunicorn..."
echo "============================================"

# Execute the original command (gunicorn)
exec "$@"