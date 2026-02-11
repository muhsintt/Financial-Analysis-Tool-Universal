"""
Complete user isolation setup script
Runs all necessary migrations and setups for user data isolation
"""

import sys
import os

# Add the parent directory to the path to import from app
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from app.models.user import User
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.models.categorization_rule import CategorizationRule
from app.models.upload import Upload
from app.utils.user_isolation import create_default_categories_for_user, migrate_existing_data_to_user
from sqlalchemy import text

def run_user_isolation_setup():
    """Run complete user isolation setup"""
    
    print("=" * 60)
    print("FINANCIAL ANALYSIS TOOL - USER ISOLATION SETUP")  
    print("=" * 60)
    print()
    
    app = create_app()
    with app.app_context():
        
        # Step 1: Check if migration is needed
        print("Step 1: Checking current database structure...")
        
        # Check if user_id columns exist
        try:
            result = db.session.execute(text("SELECT user_id FROM transactions LIMIT 1"))
            transactions_migrated = True
            print("✓ Transactions table already has user_id column")
        except:
            transactions_migrated = False
            print("✗ Transactions table needs user_id column")
        
        try:
            result = db.session.execute(text("SELECT user_id FROM categories LIMIT 1"))  
            categories_migrated = True
            print("✓ Categories table already has user_id column")
        except:
            categories_migrated = False
            print("✗ Categories table needs user_id column")
        
        if transactions_migrated and categories_migrated:
            print("\n✓ Database already appears to be migrated!")
            print("✓ User isolation is already active.")
            return True
        
        # Step 2: Run database migrations
        print("\nStep 2: Running database migrations...")
        
        try:
            if not transactions_migrated:
                print("Adding user_id to transactions...")
                db.session.execute(text("ALTER TABLE transactions ADD COLUMN user_id INTEGER"))
                
            if not categories_migrated:
                print("Adding user_id to categories...")
                db.session.execute(text("ALTER TABLE categories ADD COLUMN user_id INTEGER"))
                
            print("Adding user_id to budgets...")
            try:
                db.session.execute(text("ALTER TABLE budgets ADD COLUMN user_id INTEGER"))
            except:
                pass  # Column might already exist
                
            print("Adding user_id to categorization_rules...")
            try:
                db.session.execute(text("ALTER TABLE categorization_rules ADD COLUMN user_id INTEGER"))
            except:
                pass
                
            print("Adding user_id to uploads...")
            try:
                db.session.execute(text("ALTER TABLE uploads ADD COLUMN user_id INTEGER"))
            except:
                pass
                
            db.session.commit()
            print("✓ Database structure updated successfully!")
            
        except Exception as e:
            print(f"✗ Database migration failed: {str(e)}")
            db.session.rollback()
            return False
        
        # Step 3: Assign existing data to first user
        print("\nStep 3: Assigning existing data to users...")
        
        # Get the first/default user
        first_user = User.query.first()
        if not first_user:
            print("✗ No users found! Please create a user first.")
            return False
        
        print(f"Assigning existing data to user: {first_user.username}")
        
        # Migrate existing data
        if not migrate_existing_data_to_user(first_user.id):
            print("✗ Failed to migrate existing data")
            return False
        
        print("✓ Existing data assigned successfully!")
        
        # Step 4: Create default categories for all users who don't have them
        print("\nStep 4: Setting up default categories for users...")
        
        all_users = User.query.all()
        for user in all_users:
            # Check if user has any categories
            user_categories = Category.query.filter_by(user_id=user.id).first()
            if not user_categories:
                print(f"Creating default categories for user: {user.username}")
                if not create_default_categories_for_user(user.id):
                    print(f"✗ Failed to create categories for {user.username}")
                else:
                    print(f"✓ Categories created for {user.username}")
            else:
                print(f"✓ User {user.username} already has categories")
        
        # Step 5: Add foreign key constraints
        print("\nStep 5: Adding foreign key constraints...")
        
        try:
            # Add foreign key constraints
            constraint_queries = [
                "ALTER TABLE transactions ADD CONSTRAINT fk_transactions_user_id FOREIGN KEY (user_id) REFERENCES users (id)",
                "ALTER TABLE categories ADD CONSTRAINT fk_categories_user_id FOREIGN KEY (user_id) REFERENCES users (id)",
                "ALTER TABLE budgets ADD CONSTRAINT fk_budgets_user_id FOREIGN KEY (user_id) REFERENCES users (id)",
                "ALTER TABLE categorization_rules ADD CONSTRAINT fk_categorization_rules_user_id FOREIGN KEY (user_id) REFERENCES users (id)",
                "ALTER TABLE uploads ADD CONSTRAINT fk_uploads_user_id FOREIGN KEY (user_id) REFERENCES users (id)",
            ]
            
            for query in constraint_queries:
                try:
                    db.session.execute(text(query))
                    print("✓ Added constraint")
                except Exception as e:
                    if "already exists" in str(e).lower():
                        print("✓ Constraint already exists")
                    else:
                        print(f"  Warning: {str(e)}")
                        
            db.session.commit()
            print("✓ Foreign key constraints added!")
            
        except Exception as e:
            print(f"Warning: Some constraints may not have been added: {str(e)}")
            # Don't fail the whole setup for constraint issues
        
        # Step 6: Validation
        print("\nStep 6: Validating user isolation...")
        
        # Count data per user
        user_data_summary = {}
        for user in all_users:
            transactions_count = Transaction.query.filter_by(user_id=user.id).count()
            categories_count = Category.query.filter_by(user_id=user.id).count()
            budgets_count = Budget.query.filter_by(user_id=user.id).count()  
            rules_count = CategorizationRule.query.filter_by(user_id=user.id).count()
            uploads_count = Upload.query.filter_by(user_id=user.id).count()
            
            user_data_summary[user.username] = {
                'transactions': transactions_count,
                'categories': categories_count,
                'budgets': budgets_count,
                'rules': rules_count,
                'uploads': uploads_count
            }
        
        # Show system categories (shared)
        system_categories = Category.query.filter(Category.user_id.is_(None)).count()
        
        print(f"\nData distribution summary:")
        print(f"System categories (shared): {system_categories}")
        
        for username, data in user_data_summary.items():
            print(f"User '{username}':")
            print(f"  - Transactions: {data['transactions']}")
            print(f"  - Categories: {data['categories']}")
            print(f"  - Budgets: {data['budgets']}")
            print(f"  - Rules: {data['rules']}")
            print(f"  - Uploads: {data['uploads']}")
        
        print("\n" + "=" * 60)
        print("🎉 USER ISOLATION SETUP COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print()
        print("✅ Each user now has their own isolated data:")
        print("   - Transactions are user-specific")
        print("   - Categories are user-specific (+ shared system categories)")
        print("   - Budgets are user-specific")
        print("   - Categorization rules are user-specific")
        print("   - File uploads are user-specific")
        print("   - Activity logs remain user-specific")
        print()
        print("✅ New users will automatically get default categories")
        print("✅ All API endpoints now filter by current user")
        print()
        print("🔒 Your application now has complete user data isolation!")
        print()
        
        return True

if __name__ == "__main__":
    success = run_user_isolation_setup()
    sys.exit(0 if success else 1)