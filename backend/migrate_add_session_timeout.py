"""Migration: Add session_timeout column to users table"""
import sqlite3
import os
import sys

# Path to the database
data_dir = os.path.join(os.path.dirname(__file__), 'data')
db_path = os.path.join(data_dir, 'expense_tracker.db')

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    print("No migration needed — the table will be created fresh with the new column.")
    sys.exit(0)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if column already exists
cursor.execute("PRAGMA table_info(users)")
columns = [row[1] for row in cursor.fetchall()]

if 'session_timeout' in columns:
    print("Column 'session_timeout' already exists — migration not needed.")
else:
    cursor.execute("ALTER TABLE users ADD COLUMN session_timeout INTEGER NOT NULL DEFAULT 15")
    conn.commit()
    print("✓ Added 'session_timeout' column to users table (default: 15 minutes)")

conn.close()
