"""
Migration script to add user_id to tables for user data isolation
Run this script to add user foreign keys to existing tables
"""

from app import db
from app.models.user import User
from sqlalchemy import text
import sys

def add_user_isolation():
    """Add user_id foreign keys to isolate user data"""
    
    print("Starting user data isolation migration...")
    
    try:
        # Get the default/first user to assign existing data to
        default_user = User.query.first()
        if not default_user:
            print("ERROR: No users found. Please create a user first.")
            return False
        
        print(f"Assigning existing data to user: {default_user.username}")
        
        # Add user_id column to transactions table
        print("Adding user_id to transactions...")
        db.session.execute(text("ALTER TABLE transactions ADD COLUMN user_id INTEGER"))
        db.session.execute(text("UPDATE transactions SET user_id = :user_id"), {"user_id": default_user.id})
        db.session.execute(text("ALTER TABLE transactions ADD CONSTRAINT fk_transactions_user_id FOREIGN KEY (user_id) REFERENCES users (id)"))
        
        # Add user_id column to categories table
        print("Adding user_id to categories...")  
        db.session.execute(text("ALTER TABLE categories ADD COLUMN user_id INTEGER"))
        # Keep default categories (is_default=True) without user_id (shared across users)
        # Assign user-created categories to default user
        db.session.execute(text("UPDATE categories SET user_id = :user_id WHERE is_default = 0 OR is_default IS NULL"), {"user_id": default_user.id})
        db.session.execute(text("ALTER TABLE categories ADD CONSTRAINT fk_categories_user_id FOREIGN KEY (user_id) REFERENCES users (id)"))
        
        # Add user_id column to budgets table
        print("Adding user_id to budgets...")
        db.session.execute(text("ALTER TABLE budgets ADD COLUMN user_id INTEGER"))
        db.session.execute(text("UPDATE budgets SET user_id = :user_id"), {"user_id": default_user.id})
        db.session.execute(text("ALTER TABLE budgets ADD CONSTRAINT fk_budgets_user_id FOREIGN KEY (user_id) REFERENCES users (id)"))
        
        # Add user_id column to categorization_rules table
        print("Adding user_id to categorization_rules...")
        db.session.execute(text("ALTER TABLE categorization_rules ADD COLUMN user_id INTEGER"))
        db.session.execute(text("UPDATE categorization_rules SET user_id = :user_id"), {"user_id": default_user.id})
        db.session.execute(text("ALTER TABLE categorization_rules ADD CONSTRAINT fk_categorization_rules_user_id FOREIGN KEY (user_id) REFERENCES users (id)"))
        
        # Update uploads table - change uploaded_by to user_id
        print("Updating uploads table...")
        db.session.execute(text("ALTER TABLE uploads ADD COLUMN user_id INTEGER"))
        db.session.execute(text("UPDATE uploads SET user_id = :user_id"), {"user_id": default_user.id})
        db.session.execute(text("ALTER TABLE uploads ADD CONSTRAINT fk_uploads_user_id FOREIGN KEY (user_id) REFERENCES users (id)"))
        
        # Add user_id to excluded_expenses if it exists
        try:
            db.session.execute(text("ALTER TABLE excluded_expenses ADD COLUMN user_id INTEGER"))
            db.session.execute(text("UPDATE excluded_expenses SET user_id = :user_id"), {"user_id": default_user.id})
            db.session.execute(text("ALTER TABLE excluded_expenses ADD CONSTRAINT fk_excluded_expenses_user_id FOREIGN KEY (user_id) REFERENCES users (id)"))
            print("Added user_id to excluded_expenses...")
        except:
            print("excluded_expenses table not found or already updated")
        
        db.session.commit()
        print("Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"Migration failed: {str(e)}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    from app import create_app
    app = create_app()
    with app.app_context():
        success = add_user_isolation()
        sys.exit(0 if success else 1)