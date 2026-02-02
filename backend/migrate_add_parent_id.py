"""
Migration script to add parent_id column to categories table for subcategories support
"""
import sqlite3
import os

# The main database is in the backend folder directly
db_path = os.path.join(os.path.dirname(__file__), 'expense_tracker.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if column already exists
cursor.execute("PRAGMA table_info(categories)")
columns = [col[1] for col in cursor.fetchall()]

if 'parent_id' not in columns:
    print("Adding parent_id column to categories table...")
    cursor.execute('ALTER TABLE categories ADD COLUMN parent_id INTEGER REFERENCES categories(id)')
    conn.commit()
    print("Migration completed successfully!")
else:
    print("Column parent_id already exists, skipping migration.")

conn.close()
