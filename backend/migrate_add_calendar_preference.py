"""
Migration script to add calendar_preference column to users table
Run this once to update existing database
"""

import os
import sys
import sqlite3

def migrate():
    # Get the database path
    db_path = os.path.join(os.path.dirname(__file__), 'expense_tracker.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        print("The column will be created automatically when the app starts.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'calendar_preference' in columns:
            print("Column 'calendar_preference' already exists in users table.")
            return
        
        # Add the new column with default value 'both'
        print("Adding 'calendar_preference' column to users table...")
        cursor.execute("""
            ALTER TABLE users 
            ADD COLUMN calendar_preference VARCHAR(20) DEFAULT 'both' NOT NULL
        """)
        
        conn.commit()
        print("Migration completed successfully!")
        print("All existing users now have calendar_preference set to 'both'")
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
