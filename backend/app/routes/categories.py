from flask import Blueprint, request, jsonify
from app import db
from app.models.category import Category
from datetime import datetime

categories_bp = Blueprint('categories', __name__, url_prefix='/api/categories')

# Default categories
DEFAULT_EXPENSE_CATEGORIES = [
    'Groceries', 'Restaurants', 'Transportation', 'Utilities',
    'Entertainment', 'Shopping', 'Healthcare', 'Insurance',
    'Rent/Mortgage', 'Savings', 'Debt Payment', 'Other'
]

DEFAULT_INCOME_CATEGORIES = [
    'Salary', 'Freelance', 'Investment', 'Bonus', 'Other Income'
]

@categories_bp.route('/', methods=['GET'])
def get_categories():
    """Get all categories with optional filtering"""
    include_subs = request.args.get('include_subcategories', 'false').lower() == 'true'
    parents_only = request.args.get('parents_only', 'false').lower() == 'true'
    flat = request.args.get('flat', 'false').lower() == 'true'
    
    if parents_only:
        # Only return top-level categories (no parent)
        categories = Category.query.filter_by(parent_id=None).all()
    else:
        categories = Category.query.all()
    
    if flat:
        # Return flat list with full names for dropdowns
        result = []
        for cat in Category.query.filter_by(parent_id=None).all():
            result.append(cat.to_dict())
            for sub in cat.subcategories:
                sub_dict = sub.to_dict()
                sub_dict['display_name'] = f"{cat.name} > {sub.name}"
                result.append(sub_dict)
        return jsonify(result)
    
    return jsonify([cat.to_dict(include_subcategories=include_subs) for cat in categories])

@categories_bp.route('/<int:id>/subcategories', methods=['GET'])
def get_subcategories(id):
    """Get all subcategories of a category"""
    category = Category.query.get_or_404(id)
    return jsonify([sub.to_dict() for sub in category.subcategories])

@categories_bp.route('/type/<type>', methods=['GET'])
def get_categories_by_type(type):
    """Get categories by type (income or expense)"""
    if type not in ['income', 'expense']:
        return jsonify({'error': 'Invalid type'}), 400
    
    parents_only = request.args.get('parents_only', 'false').lower() == 'true'
    include_subs = request.args.get('include_subcategories', 'false').lower() == 'true'
    
    if parents_only:
        categories = Category.query.filter_by(type=type, parent_id=None).all()
    else:
        categories = Category.query.filter_by(type=type).all()
    
    return jsonify([cat.to_dict(include_subcategories=include_subs) for cat in categories])

@categories_bp.route('/', methods=['POST'])
def create_category():
    """Create a new category or subcategory"""
    data = request.get_json()
    
    if not data.get('name'):
        return jsonify({'error': 'Name is required'}), 400
    
    parent_id = data.get('parent_id')
    
    # If parent_id is provided, inherit type from parent
    if parent_id:
        parent = Category.query.get(parent_id)
        if not parent:
            return jsonify({'error': 'Parent category not found'}), 404
        if parent.parent_id:
            return jsonify({'error': 'Cannot create subcategory of a subcategory (only one level allowed)'}), 400
        category_type = parent.type
    else:
        if not data.get('type'):
            return jsonify({'error': 'Type is required for top-level categories'}), 400
        if data['type'] not in ['income', 'expense']:
            return jsonify({'error': 'Type must be income or expense'}), 400
        category_type = data['type']
    
    # Check for duplicate name within the same parent
    existing = Category.query.filter_by(name=data['name'], parent_id=parent_id).first()
    if existing:
        if parent_id:
            return jsonify({'error': 'Subcategory with this name already exists in this category'}), 409
        else:
            return jsonify({'error': 'Category already exists'}), 409
    
    category = Category(
        name=data['name'],
        type=category_type,
        color=data.get('color', '#3498db'),
        icon=data.get('icon', 'folder'),
        parent_id=parent_id
    )
    
    db.session.add(category)
    db.session.commit()
    
    return jsonify(category.to_dict()), 201

@categories_bp.route('/<int:id>', methods=['PUT'])
def update_category(id):
    """Update a category"""
    category = Category.query.get_or_404(id)
    data = request.get_json()
    
    # Check for duplicate names if name is being changed
    if 'name' in data and data['name'] != category.name:
        existing = Category.query.filter_by(name=data['name']).first()
        if existing:
            return jsonify({'error': 'Category name already exists'}), 400
        category.name = data['name']
    if 'color' in data:
        category.color = data['color']
    if 'icon' in data:
        category.icon = data['icon']
    
    db.session.commit()
    return jsonify(category.to_dict())

@categories_bp.route('/<int:id>/set-default', methods=['POST'])
def set_default_category(id):
    """Set a category as the default for its type"""
    category = Category.query.get_or_404(id)
    
    # Remove default from other categories of the same type
    Category.query.filter_by(type=category.type, is_default=True).update({'is_default': False})
    
    # Set this category as default
    category.is_default = True
    db.session.commit()
    
    return jsonify({
        'message': f'{category.name} is now the default {category.type} category',
        'category': category.to_dict()
    })

@categories_bp.route('/<int:id>', methods=['DELETE'])
def delete_category(id):
    """Delete a category and reassign its transactions to the default/parent category"""
    from app.models.transaction import Transaction
    from app.models.budget import Budget
    from app.models.categorization_rule import CategorizationRule
    
    category = Category.query.get_or_404(id)
    category_type = category.type
    category_name = category.name
    is_subcategory = category.parent_id is not None
    
    # Don't allow deleting the default category (only applies to parent categories)
    if category.is_default and not is_subcategory:
        return jsonify({'error': 'Cannot delete the default category. Set another category as default first.'}), 400
    
    # Determine reassignment target
    if is_subcategory:
        # Subcategories reassign to their parent
        target_category = category.parent
    else:
        # First, reassign or delete all subcategories
        for subcategory in category.subcategories:
            # Move subcategory transactions to parent before deleting
            Transaction.query.filter_by(category_id=subcategory.id).update({'category_id': id})
            Budget.query.filter_by(category_id=subcategory.id).update({'category_id': id})
            CategorizationRule.query.filter_by(category_id=subcategory.id).update({'category_id': id})
            db.session.delete(subcategory)
        
        # Find the default category of the same type
        target_category = Category.query.filter_by(type=category_type, is_default=True, parent_id=None).first()
        
        if not target_category or target_category.id == id:
            # Fall back to "Other" category
            other_category_name = 'Other Income' if category_type == 'income' else 'Other'
            target_category = Category.query.filter_by(name=other_category_name, type=category_type, parent_id=None).first()
            
            if not target_category:
                target_category = Category(name=other_category_name, type=category_type, is_default=True)
                db.session.add(target_category)
                db.session.flush()
    
    # Count affected items
    transaction_count = Transaction.query.filter_by(category_id=id).count()
    budget_count = Budget.query.filter_by(category_id=id).count()
    rule_count = CategorizationRule.query.filter_by(category_id=id).count()
    
    # Reassign transactions to target category
    Transaction.query.filter_by(category_id=id).update({'category_id': target_category.id})
    
    # Reassign budgets to target category
    Budget.query.filter_by(category_id=id).update({'category_id': target_category.id})
    
    # Reassign categorization rules to target category
    CategorizationRule.query.filter_by(category_id=id).update({'category_id': target_category.id})
    
    # Now delete the category
    db.session.delete(category)
    db.session.commit()
    
    return jsonify({
        'message': f'{"Subcategory" if is_subcategory else "Category"} "{category_name}" deleted',
        'reassigned_to': target_category.name,
        'reassigned': {
            'transactions': transaction_count,
            'budgets': budget_count,
            'rules': rule_count
        }
    }), 200

@categories_bp.route('/init', methods=['POST'])
def initialize_categories():
    """Initialize default categories"""
    created = []
    
    for cat_name in DEFAULT_EXPENSE_CATEGORIES:
        if not Category.query.filter_by(name=cat_name).first():
            category = Category(name=cat_name, type='expense')
            db.session.add(category)
            created.append(cat_name)
    
    for cat_name in DEFAULT_INCOME_CATEGORIES:
        if not Category.query.filter_by(name=cat_name).first():
            category = Category(name=cat_name, type='income')
            db.session.add(category)
            created.append(cat_name)
    
    db.session.commit()
    return jsonify({
        'message': 'Categories initialized',
        'created': created
    }), 201
