from flask import Blueprint, request, jsonify, session
from app import db
from app.models.budget import Budget
from app.models.category import Category
from app.routes.auth import write_required, login_required
from datetime import datetime, date

budgets_bp = Blueprint('budgets', __name__, url_prefix='/api/budgets')

@budgets_bp.route('/', methods=['GET'])
@login_required
def get_budgets():
    """Get all budgets with optional filters"""
    period = request.args.get('period')
    for_excluded = request.args.get('for_excluded', 'false').lower() == 'true'
    
    # Filter by current user
    query = Budget.query.filter_by(user_id=session['user_id'])
    
    if period:
        query = query.filter_by(period=period)
    
    query = query.filter_by(for_excluded=for_excluded)
    
    budgets = query.all()
    return jsonify([b.to_dict() for b in budgets])

@budgets_bp.route('/', methods=['POST'])
@write_required
def create_budget():
    """Create a new budget"""
    data = request.get_json()
    
    required_fields = ['category_id', 'amount', 'period', 'year']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if data['period'] not in ['daily', 'weekly', 'monthly', 'annual']:
        return jsonify({'error': 'Invalid period'}), 400
    
    # Verify category exists and user has access
    current_user_id = session['user_id']
    category = Category.query.filter(
        Category.id == data['category_id'],
        (Category.user_id == current_user_id) | (Category.user_id.is_(None))
    ).first()
    if not category:
        return jsonify({'error': 'Category not found or access denied'}), 404
    
    budget = Budget(
        category_id=data['category_id'],
        amount=float(data['amount']),
        period=data['period'],
        year=int(data['year']),
        month=data.get('month'),
        week=data.get('week'),
        for_excluded=data.get('for_excluded', False),
        user_id=current_user_id  # Associate with current user
    )
    
    db.session.add(budget)
    db.session.commit()
    
    return jsonify(budget.to_dict()), 201

@budgets_bp.route('/<int:id>', methods=['GET'])
@login_required
def get_budget(id):
    """Get a specific budget"""
    budget = Budget.query.filter_by(id=id, user_id=session['user_id']).first_or_404()
    return jsonify(budget.to_dict())

@budgets_bp.route('/<int:id>', methods=['PUT'])
@write_required
def update_budget(id):
    """Update a budget"""
    budget = Budget.query.filter_by(id=id, user_id=session['user_id']).first_or_404()
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
@write_required
def delete_budget(id):
    """Delete a budget"""
    budget = Budget.query.filter_by(id=id, user_id=session['user_id']).first_or_404()
    """Delete a budget"""
    budget = Budget.query.get_or_404(id)
    db.session.delete(budget)
    db.session.commit()
    return jsonify({'message': 'Budget deleted'}), 204
