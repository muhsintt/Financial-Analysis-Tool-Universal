"""
Migration script to add is_default column to categories table
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

if 'is_default' not in columns:
    print("Adding is_default column to categories table...")
    cursor.execute('ALTER TABLE categories ADD COLUMN is_default BOOLEAN DEFAULT 0')
    
    # Set "Other" categories as default (both expense and income if they exist)
    cursor.execute("UPDATE categories SET is_default = 1 WHERE name = 'Other'")
    
    conn.commit()
    print("Migration completed successfully!")
else:
    print("Column is_default already exists, skipping migration.")

conn.close()
