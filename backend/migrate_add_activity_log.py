"""
Migration script to add activity_log table.
Run this script after the main application has been updated.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.activity_log import ActivityLog

def migrate():
    app = create_app()
    
    with app.app_context():
        # Create the activity_log table
        try:
            # Check if table exists
            result = db.session.execute(db.text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='activity_logs'"
            ))
            if not result.fetchone():
                # Create the table
                ActivityLog.__table__.create(db.engine)
                print("✓ Created activity_logs table")
                
                # Log the migration itself as first activity
                log = ActivityLog(
                    action=ActivityLog.ACTION_CREATE,
                    category=ActivityLog.CATEGORY_SYSTEM,
                    description='Activity logging system initialized',
                    username='system',
                    ip_address='127.0.0.1'
                )
                db.session.add(log)
                db.session.commit()
                print("✓ Added initial system log entry")
            else:
                print("✓ activity_logs table already exists")
                
        except Exception as e:
            print(f"✗ Error during migration: {e}")
            return False
    
    print("\n✓ Migration completed successfully!")
    return True

if __name__ == '__main__':
    migrate()
