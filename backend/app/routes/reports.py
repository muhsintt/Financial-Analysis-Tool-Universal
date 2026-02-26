from flask import Blueprint, request, jsonify, session
from app import db
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.models.category import Category
from app.routes.auth import login_required
from datetime import datetime, date, timedelta
from sqlalchemy import func
import calendar
from app.utils.badi_calendar import (
    get_badi_month_date_range,
    get_badi_year_date_range,
    get_current_badi_date
)

reports_bp = Blueprint('reports', __name__, url_prefix='/api/reports')

def get_date_range(period, year=None, month=None, week=None, calendar_type='gregorian',
                   specific_date=None, week_start=None, date_from=None, date_to=None):
    """Get start and end dates for a period. Supports custom, daily (any day),
    weekly (any week), monthly, and annual (year-to-date). Handles both
    Gregorian and Badí' calendars."""

    # ---- Custom range always takes priority ----
    if period == 'custom':
        try:
            start = datetime.strptime(date_from, '%Y-%m-%d').date() if date_from else date.today()
            end   = datetime.strptime(date_to,   '%Y-%m-%d').date() if date_to   else date.today()
        except (ValueError, TypeError):
            start = end = date.today()
        return start, end

    if calendar_type == 'badi':
        # Handle Badí' calendar periods
        if period == 'daily':
            if specific_date:
                try:
                    d = datetime.strptime(specific_date, '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    d = date.today()
            else:
                d = date.today()
            return d, d
        elif period == 'weekly':
            if week_start:
                try:
                    start = datetime.strptime(week_start, '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    today = date.today()
                    start = today - timedelta(days=today.weekday())
            else:
                today = date.today()
                start = today - timedelta(days=today.weekday())
            end = start + timedelta(days=6)
            return start, end
        elif period == 'monthly':
            if year is None or month is None:
                badi_year, badi_month, _ = get_current_badi_date()
                year  = year  or badi_year
                month = month if month is not None else badi_month
            return get_badi_month_date_range(year, month)
        elif period == 'annual':
            if year is None:
                badi_year, _, _ = get_current_badi_date()
                year = badi_year
            return get_badi_year_date_range(year)
        else:
            return date.today(), date.today()
    else:
        # Handle Gregorian calendar periods
        if period == 'daily':
            if specific_date:
                try:
                    d = datetime.strptime(specific_date, '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    d = date.today()
            else:
                d = date.today()
            return d, d
        elif period == 'weekly':
            if week_start:
                try:
                    start = datetime.strptime(week_start, '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    today = date.today()
                    start = today - timedelta(days=today.weekday())
            else:
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
            year_obj  = year if year else date.today().year
            today_obj = date.today()
            start = date(year_obj, 1, 1)
            # Year-to-date: for current year end at today; for past years end at Dec 31
            end = date(year_obj, 12, 31) if year_obj < today_obj.year else today_obj
            return start, end
        else:
            return date.today(), date.today()

@reports_bp.route('/summary', methods=['GET'])
@login_required
def get_summary():
    """Get financial summary"""
    period        = request.args.get('period', 'monthly')
    year          = request.args.get('year', type=int)
    month         = request.args.get('month', type=int)
    calendar_type = request.args.get('calendar', 'gregorian')
    specific_date = request.args.get('specific_date')
    week_start    = request.args.get('week_start')
    date_from     = request.args.get('date_from')
    date_to       = request.args.get('date_to')

    start_date, end_date = get_date_range(
        period, year, month, calendar_type=calendar_type,
        specific_date=specific_date, week_start=week_start,
        date_from=date_from, date_to=date_to
    )
    
    # Get all transactions in the date range for current user
    all_transactions = Transaction.query.filter(
        Transaction.date >= start_date,
        Transaction.date <= end_date,
        Transaction.user_id == session['user_id']
    ).all()
    
    # Calculate totals for all transactions (included + excluded)
    total_income = sum(t.amount for t in all_transactions if t.type == 'income')
    total_expense = sum(t.amount for t in all_transactions if t.type == 'expense')
    
    # Calculate totals for excluded transactions only
    excluded_income = sum(t.amount for t in all_transactions if t.type == 'income' and t.is_excluded)
    excluded_expense = sum(t.amount for t in all_transactions if t.type == 'expense' and t.is_excluded)
    total_excluded = excluded_income + excluded_expense
    
    # Calculate included totals for net balance
    included_income = total_income - excluded_income
    included_expense = total_expense - excluded_expense
    
    return jsonify({
        'period': period,
        'calendar_type': calendar_type,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'total_income': total_income,
        'total_expense': total_expense,
        'excluded_income': excluded_income,
        'excluded_expense': excluded_expense,
        'total_excluded': total_excluded,
        'included_income': included_income,
        'included_expense': included_expense,
        'net': included_income - included_expense,
        'transaction_count': len(all_transactions)
    })

@reports_bp.route('/by-category', methods=['GET'])
@login_required
def get_by_category():
    """Get expenses/income by category"""
    period           = request.args.get('period', 'monthly')
    transaction_type = request.args.get('type', 'expense')
    year             = request.args.get('year', type=int)
    month            = request.args.get('month', type=int)
    include_excluded = request.args.get('include_excluded', 'false').lower() == 'true'
    calendar_type    = request.args.get('calendar', 'gregorian')
    specific_date    = request.args.get('specific_date')
    week_start       = request.args.get('week_start')
    date_from        = request.args.get('date_from')
    date_to          = request.args.get('date_to')

    start_date, end_date = get_date_range(
        period, year, month, calendar_type=calendar_type,
        specific_date=specific_date, week_start=week_start,
        date_from=date_from, date_to=date_to
    )
    
    query = Transaction.query.filter(
        Transaction.date >= start_date,
        Transaction.date <= end_date,
        Transaction.type == transaction_type
    )
    
    if not include_excluded:
        query = query.filter_by(is_excluded=False)
    
    transactions = query.all()
    
    # Group by category (using full_name which includes parent for subcategories)
    category_totals = {}
    for t in transactions:
        if t.category:
            # Use full_name to show "Parent > Subcategory" format
            cat_name = t.category.full_name if hasattr(t.category, 'full_name') else t.category.name
            cat_color = t.category.color
            parent_id = t.category.parent_id
        else:
            cat_name = 'Unknown'
            cat_color = '#999999'
            parent_id = None
            
        if cat_name not in category_totals:
            category_totals[cat_name] = {
                'amount': 0,
                'count': 0,
                'category_id': t.category_id if t.category else None,
                'color': cat_color,
                'parent_id': parent_id
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
            'color': data['color'],
            'parent_id': data['parent_id'],
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
@login_required
def get_budget_analysis():
    """Get budget vs actual analysis"""
    period           = request.args.get('period', 'monthly')
    year             = request.args.get('year', type=int)
    month            = request.args.get('month', type=int)
    include_excluded = request.args.get('include_excluded', 'false').lower() == 'true'
    calendar_type    = request.args.get('calendar', 'gregorian')
    specific_date    = request.args.get('specific_date')
    week_start       = request.args.get('week_start')
    date_from        = request.args.get('date_from')
    date_to          = request.args.get('date_to')

    start_date, end_date = get_date_range(
        period, year, month, calendar_type=calendar_type,
        specific_date=specific_date, week_start=week_start,
        date_from=date_from, date_to=date_to
    )
    
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
        
        # Use full_name to show parent for subcategories
        if budget.category:
            cat_name = budget.category.full_name if hasattr(budget.category, 'full_name') else budget.category.name
            cat_color = budget.category.color
            parent_id = budget.category.parent_id
        else:
            cat_name = 'Unknown'
            cat_color = '#999999'
            parent_id = None
        
        results.append({
            'category': cat_name,
            'category_id': budget.category_id,
            'color': cat_color,
            'parent_id': parent_id,
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
@login_required
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
