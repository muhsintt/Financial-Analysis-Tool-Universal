"""
Helper functions for user data isolation
"""

from app import db
from app.models.category import Category
from app.models.user import User

def create_default_categories_for_user(user_id):
    """Create default categories for a new user"""
    
    DEFAULT_EXPENSE_CATEGORIES = [
        'Groceries', 'Restaurants', 'Transportation', 'Utilities',
        'Entertainment', 'Shopping', 'Healthcare', 'Insurance',
        'Rent/Mortgage', 'Savings', 'Debt Payment', 'Other'
    ]

    DEFAULT_INCOME_CATEGORIES = [
        'Salary', 'Freelance', 'Investment', 'Bonus', 'Other Income'
    ]
    
    try:
        # Create expense categories
        for category_name in DEFAULT_EXPENSE_CATEGORIES:
            category = Category(
                name=category_name,
                type='expense',
                color='#e74c3c' if category_name in ['Rent/Mortgage', 'Utilities'] else '#3498db',
                icon='folder',
                is_default=False,  # User categories are not system defaults
                user_id=user_id
            )
            db.session.add(category)
        
        # Create income categories
        for category_name in DEFAULT_INCOME_CATEGORIES:
            category = Category(
                name=category_name,
                type='income',
                color='#27ae60',
                icon='folder',
                is_default=False,  # User categories are not system defaults
                user_id=user_id
            )
            db.session.add(category)
        
        db.session.commit()
        return True
        
    except Exception as e:
        print(f"Error creating default categories for user {user_id}: {str(e)}")
        db.session.rollback()
        return False

def ensure_user_can_access_category(category_id, user_id):
    """Check if user can access a category (system or their own)"""
    category = Category.query.filter(
        Category.id == category_id,
        (Category.user_id == user_id) | (Category.user_id.is_(None))
    ).first()
    return category is not None

def get_user_accessible_categories(user_id, category_type=None, parent_id=None):
    """Get all categories accessible to a user (system + their own)"""
    query = Category.query.filter(
        (Category.user_id == user_id) | (Category.user_id.is_(None))
    )
    
    if category_type:
        query = query.filter(Category.type == category_type)
    
    if parent_id is not None:
        query = query.filter(Category.parent_id == parent_id)
    
    return query.all()

def migrate_existing_data_to_user(target_user_id):
    """Migrate existing data (transactions, budgets, rules) to a specific user.
    This should only be used during initial migration."""
    
    from app.models.transaction import Transaction
    from app.models.budget import Budget
    from app.models.categorization_rule import CategorizationRule
    from app.models.upload import Upload
    
    try:
        # Migrate transactions without user_id
        Transaction.query.filter(Transaction.user_id.is_(None)).update({
            Transaction.user_id: target_user_id
        })
        
        # Migrate budgets without user_id
        Budget.query.filter(Budget.user_id.is_(None)).update({
            Budget.user_id: target_user_id
        })
        
        # Migrate rules without user_id
        CategorizationRule.query.filter(CategorizationRule.user_id.is_(None)).update({
            CategorizationRule.user_id: target_user_id
        })
        
        # Migrate uploads without user_id
        Upload.query.filter(Upload.user_id.is_(None)).update({
            Upload.user_id: target_user_id
        })
        
        # Migrate user-created categories (not system defaults)
        Category.query.filter(
            Category.user_id.is_(None),
            Category.is_default == False
        ).update({
            Category.user_id: target_user_id
        })
        
        db.session.commit()
        return True
        
    except Exception as e:
        print(f"Error migrating data to user {target_user_id}: {str(e)}")
        db.session.rollback()
        return False