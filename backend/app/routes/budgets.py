from flask import Blueprint, request, jsonify
from app import db
from app.models.budget import Budget
from app.models.category import Category
from datetime import datetime, date

budgets_bp = Blueprint('budgets', __name__, url_prefix='/api/budgets')

@budgets_bp.route('/', methods=['GET'])
def get_budgets():
    """Get all budgets with optional filters"""
    period = request.args.get('period')
    for_excluded = request.args.get('for_excluded', 'false').lower() == 'true'
    
    query = Budget.query
    
    if period:
        query = query.filter_by(period=period)
    
    query = query.filter_by(for_excluded=for_excluded)
    
    budgets = query.all()
    return jsonify([b.to_dict() for b in budgets])

@budgets_bp.route('/', methods=['POST'])
def create_budget():
    """Create a new budget"""
    data = request.get_json()
    
    required_fields = ['category_id', 'amount', 'period', 'year']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if data['period'] not in ['daily', 'weekly', 'monthly', 'annual']:
        return jsonify({'error': 'Invalid period'}), 400
    
    category = Category.query.get(data['category_id'])
    if not category:
        return jsonify({'error': 'Category not found'}), 404
    
    budget = Budget(
        category_id=data['category_id'],
        amount=float(data['amount']),
        period=data['period'],
        year=int(data['year']),
        month=data.get('month'),
        week=data.get('week'),
        for_excluded=data.get('for_excluded', False)
    )
    
    db.session.add(budget)
    db.session.commit()
    
    return jsonify(budget.to_dict()), 201

@budgets_bp.route('/<int:id>', methods=['GET'])
def get_budget(id):
    """Get a specific budget"""
    budget = Budget.query.get_or_404(id)
    return jsonify(budget.to_dict())

@budgets_bp.route('/<int:id>', methods=['PUT'])
def update_budget(id):
    """Update a budget"""
    budget = Budget.query.get_or_404(id)
    data = request.get_json()
    
    if 'amount' in data:
        budget.amount = float(data['amount'])
    if 'month' in data:
        budget.month = data['month']
    if 'week' in data:
        budget.week = data['week']
    
    db.session.commit()
    return jsonify(budget.to_dict())

@budgets_bp.route('/<int:id>', methods=['DELETE'])
def delete_budget(id):
    """Delete a budget"""
    budget = Budget.query.get_or_404(id)
    db.session.delete(budget)
    db.session.commit()
    return jsonify({'message': 'Budget deleted'}), 204
