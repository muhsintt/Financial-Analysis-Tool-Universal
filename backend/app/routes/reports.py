from flask import Blueprint, request, jsonify
from app import db
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.models.category import Category
from datetime import datetime, date, timedelta
from sqlalchemy import func
import calendar

reports_bp = Blueprint('reports', __name__, url_prefix='/api/reports')

def get_date_range(period, year, month=None, week=None):
    """Get start and end dates for a period"""
    if period == 'daily':
        today = date.today()
        return today, today
    elif period == 'weekly':
        today = date.today()
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
        return start, end
    elif period == 'monthly':
        if month is None:
            month = date.today().month
        year_obj = year if year else date.today().year
        first = date(year_obj, month, 1)
        last_day = calendar.monthrange(year_obj, month)[1]
        last = date(year_obj, month, last_day)
        return first, last
    elif period == 'annual':
        year_obj = year if year else date.today().year
        return date(year_obj, 1, 1), date(year_obj, 12, 31)
    else:
        return date.today(), date.today()

@reports_bp.route('/summary', methods=['GET'])
def get_summary():
    """Get financial summary"""
    period = request.args.get('period', 'monthly')
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    include_excluded = request.args.get('include_excluded', 'false').lower() == 'true'
    
    start_date, end_date = get_date_range(period, year, month)
    
    query = Transaction.query.filter(
        Transaction.date >= start_date,
        Transaction.date <= end_date
    )
    
    if not include_excluded:
        query = query.filter_by(is_excluded=False)
    
    transactions = query.all()
    
    total_income = sum(t.amount for t in transactions if t.type == 'income')
    total_expense = sum(t.amount for t in transactions if t.type == 'expense')
    
    return jsonify({
        'period': period,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'total_income': total_income,
        'total_expense': total_expense,
        'net': total_income - total_expense,
        'transaction_count': len(transactions)
    })

@reports_bp.route('/by-category', methods=['GET'])
def get_by_category():
    """Get expenses/income by category"""
    period = request.args.get('period', 'monthly')
    transaction_type = request.args.get('type', 'expense')
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    include_excluded = request.args.get('include_excluded', 'false').lower() == 'true'
    
    start_date, end_date = get_date_range(period, year, month)
    
    query = Transaction.query.filter(
        Transaction.date >= start_date,
        Transaction.date <= end_date,
        Transaction.type == transaction_type
    )
    
    if not include_excluded:
        query = query.filter_by(is_excluded=False)
    
    transactions = query.all()
    
    # Group by category
    category_totals = {}
    for t in transactions:
        cat_name = t.category.name if t.category else 'Unknown'
        if cat_name not in category_totals:
            category_totals[cat_name] = {
                'amount': 0,
                'count': 0,
                'category_id': t.category_id if t.category else None
            }
        category_totals[cat_name]['amount'] += t.amount
        category_totals[cat_name]['count'] += 1
    
    result = []
    for cat_name, data in sorted(category_totals.items(), key=lambda x: x[1]['amount'], reverse=True):
        result.append({
            'category': cat_name,
            'category_id': data['category_id'],
            'amount': data['amount'],
            'count': data['count'],
            'percentage': 0  # Will be calculated on frontend
        })
    
    total = sum(item['amount'] for item in result)
    for item in result:
        item['percentage'] = round((item['amount'] / total * 100) if total > 0 else 0, 2)
    
    return jsonify({
        'period': period,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'type': transaction_type,
        'total': total,
        'categories': result
    })

@reports_bp.route('/budget-analysis', methods=['GET'])
def get_budget_analysis():
    """Get budget vs actual analysis"""
    period = request.args.get('period', 'monthly')
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    include_excluded = request.args.get('include_excluded', 'false').lower() == 'true'
    
    start_date, end_date = get_date_range(period, year, month)
    
    # Get all budgets for this period
    budgets = Budget.query.filter_by(period=period, year=year).all()
    if period == 'monthly':
        budgets = [b for b in budgets if b.month == month]
    
    results = []
    for budget in budgets:
        query = Transaction.query.filter(
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.category_id == budget.category_id
        )
        
        if not include_excluded:
            query = query.filter_by(is_excluded=False)
        
        actual = sum(t.amount for t in query.all())
        
        results.append({
            'category': budget.category.name if budget.category else 'Unknown',
            'category_id': budget.category_id,
            'budgeted': budget.amount,
            'actual': actual,
            'difference': budget.amount - actual,
            'percentage': round((actual / budget.amount * 100) if budget.amount > 0 else 0, 2),
            'status': 'under' if actual < budget.amount else 'over'
        })
    
    return jsonify({
        'period': period,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'budgets': results
    })

@reports_bp.route('/trending', methods=['GET'])
def get_trending():
    """Get spending trends over time"""
    months = request.args.get('months', 6, type=int)
    transaction_type = request.args.get('type', 'expense')
    include_excluded = request.args.get('include_excluded', 'false').lower() == 'true'
    
    today = date.today()
    trend_data = []
    
    for i in range(months):
        current_date = today - timedelta(days=30 * i)
        start = date(current_date.year, current_date.month, 1)
        last_day = calendar.monthrange(current_date.year, current_date.month)[1]
        end = date(current_date.year, current_date.month, last_day)
        
        query = Transaction.query.filter(
            Transaction.date >= start,
            Transaction.date <= end,
            Transaction.type == transaction_type
        )
        
        if not include_excluded:
            query = query.filter_by(is_excluded=False)
        
        amount = sum(t.amount for t in query.all())
        
        trend_data.append({
            'month': start.strftime('%Y-%m'),
            'amount': amount
        })
    
    return jsonify({
        'type': transaction_type,
        'months': months,
        'data': trend_data[::-1]  # Reverse to show oldest first
    })
