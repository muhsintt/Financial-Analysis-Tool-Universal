#!/bin/bash
# Script to delete the SQLite database and restart Docker containers

DB_PATH="backend/data/expense_tracker.db"

if [ -f "$DB_PATH" ]; then
    echo "Deleting database: $DB_PATH"
    rm "$DB_PATH"
else
    echo "Database file not found: $DB_PATH"
fi

echo "Restarting Docker containers..."
docker-compose down
sleep 2
docker-compose up -d

echo "Done. Database deleted and containers restarted."
