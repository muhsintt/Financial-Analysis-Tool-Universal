"""
Migration script to add log_settings table.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.log_settings import LogSettings

def migrate():
    app = create_app()
    
    with app.app_context():
        try:
            result = db.session.execute(db.text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='log_settings'"
            ))
            if not result.fetchone():
                LogSettings.__table__.create(db.engine)
                print("✓ Created log_settings table")
                
                # Create default settings
                settings = LogSettings()
                db.session.add(settings)
                db.session.commit()
                print("✓ Created default log settings")
            else:
                print("✓ log_settings table already exists")
                
        except Exception as e:
            print(f"✗ Error during migration: {e}")
            return False
    
    print("\n✓ Migration completed successfully!")
    return True

if __name__ == '__main__':
    migrate()
