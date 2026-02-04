"""
Migration script to add upload_id column to transactions table.
Run this script to update existing database schema.
"""

import sqlite3
import os

def migrate():
    # Get the database path
    db_path = os.path.join(os.path.dirname(__file__), 'expense_tracker.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if uploads table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='uploads'")
        if not cursor.fetchone():
            print("Creating uploads table...")
            cursor.execute('''
                CREATE TABLE uploads (
                    id INTEGER PRIMARY KEY,
                    filename VARCHAR(255) NOT NULL,
                    original_filename VARCHAR(255) NOT NULL,
                    file_size INTEGER DEFAULT 0,
                    file_type VARCHAR(50),
                    transaction_count INTEGER DEFAULT 0,
                    uploaded_by VARCHAR(100) DEFAULT 'system',
                    status VARCHAR(50) DEFAULT 'completed',
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            print("Uploads table created successfully")
        else:
            print("Uploads table already exists")
        
        # Check if upload_id column exists in transactions table
        cursor.execute("PRAGMA table_info(transactions)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'upload_id' not in columns:
            print("Adding upload_id column to transactions table...")
            cursor.execute('ALTER TABLE transactions ADD COLUMN upload_id INTEGER REFERENCES uploads(id)')
            print("upload_id column added successfully")
        else:
            print("upload_id column already exists")
        
        conn.commit()
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Migration error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
