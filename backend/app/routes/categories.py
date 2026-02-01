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
    """Get all categories"""
    categories = Category.query.all()
    return jsonify([cat.to_dict() for cat in categories])

@categories_bp.route('/<type>', methods=['GET'])
def get_categories_by_type(type):
    """Get categories by type (income or expense)"""
    if type not in ['income', 'expense']:
        return jsonify({'error': 'Invalid type'}), 400
    
    categories = Category.query.filter_by(type=type).all()
    return jsonify([cat.to_dict() for cat in categories])

@categories_bp.route('/', methods=['POST'])
def create_category():
    """Create a new category"""
    data = request.get_json()
    
    if not data.get('name') or not data.get('type'):
        return jsonify({'error': 'Name and type are required'}), 400
    
    if data['type'] not in ['income', 'expense']:
        return jsonify({'error': 'Type must be income or expense'}), 400
    
    existing = Category.query.filter_by(name=data['name']).first()
    if existing:
        return jsonify({'error': 'Category already exists'}), 409
    
    category = Category(
        name=data['name'],
        type=data['type'],
        color=data.get('color', '#3498db'),
        icon=data.get('icon', 'folder')
    )
    
    db.session.add(category)
    db.session.commit()
    
    return jsonify(category.to_dict()), 201

@categories_bp.route('/<int:id>', methods=['PUT'])
def update_category(id):
    """Update a category"""
    category = Category.query.get_or_404(id)
    data = request.get_json()
    
    if 'name' in data:
        category.name = data['name']
    if 'color' in data:
        category.color = data['color']
    if 'icon' in data:
        category.icon = data['icon']
    
    db.session.commit()
    return jsonify(category.to_dict())

@categories_bp.route('/<int:id>', methods=['DELETE'])
def delete_category(id):
    """Delete a category"""
    category = Category.query.get_or_404(id)
    db.session.delete(category)
    db.session.commit()
    return jsonify({'message': 'Category deleted'}), 204

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
