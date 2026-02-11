from flask import Blueprint, request, jsonify, session
from app import db
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.activity_log import ActivityLog
from app.models.log_settings import LogSettings
from app.routes.auth import write_required
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_
import json

transactions_bp = Blueprint('transactions', __name__, url_prefix='/api/transactions')

def log_activity(action, description, details=None):
    """Helper to log transaction activities - checks settings before logging"""
    try:
        settings = LogSettings.get_settings()
        if not settings.should_log(action, ActivityLog.CATEGORY_TRANSACTION):
            return
    except:
        pass
    
    log = ActivityLog(
        action=action,
        category=ActivityLog.CATEGORY_TRANSACTION,
        description=description,
        details=json.dumps(details) if details else None,
        user_id=session.get('user_id'),
        username=session.get('username', 'anonymous'),
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

@transactions_bp.route('/', methods=['GET'])
def get_transactions():
    """Get all transactions with optional filters"""
    category_id = request.args.get('category_id', type=int)
    transaction_type = request.args.get('type')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    include_excluded = request.args.get('include_excluded', 'false').lower() == 'true'
    
    # Filter by current user
    query = Transaction.query.filter_by(user_id=session['user_id'])
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    if transaction_type:
        query = query.filter_by(type=transaction_type)
    if not include_excluded:
        query = query.filter_by(is_excluded=False)
    
    if start_date:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        query = query.filter(Transaction.date >= start)
    if end_date:
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        query = query.filter(Transaction.date <= end)
    
    transactions = query.order_by(Transaction.date.desc()).all()
    return jsonify([t.to_dict() for t in transactions])

@transactions_bp.route('/<int:id>', methods=['GET'])
def get_transaction(id):
    """Get a specific transaction"""
    transaction = Transaction.query.filter_by(id=id, user_id=session['user_id']).first_or_404()
    return jsonify(transaction.to_dict())

@transactions_bp.route('/', methods=['POST'])
@write_required
def create_transaction():
    """Create a new transaction"""
    data = request.get_json()
    
    required_fields = ['description', 'amount', 'type', 'date', 'category_id']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if data['type'] not in ['income', 'expense']:
        return jsonify({'error': 'Type must be income or expense'}), 400
    
    # Verify category exists and belongs to current user
    category = Category.query.filter_by(id=data['category_id'], user_id=session['user_id']).first()
    if not category:
        return jsonify({'error': 'Category not found'}), 404
    
    transaction = Transaction(
        description=data['description'],
        amount=float(data['amount']),
        type=data['type'],
        date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
        category_id=data['category_id'],
        user_id=session['user_id'],  # Associate with current user
        notes=data.get('notes', '')
    )
    
    db.session.add(transaction)
    db.session.commit()
    
    # Log the activity
    log_activity(
        ActivityLog.ACTION_CREATE,
        f'Created transaction: {data["description"][:50]}',
        {'transaction_id': transaction.id, 'amount': float(data['amount']), 'type': data['type']}
    )
    
    return jsonify(transaction.to_dict()), 201

@transactions_bp.route('/<int:id>', methods=['PUT'])
@write_required
def update_transaction(id):
    """Update a transaction"""
    transaction = Transaction.query.filter_by(id=id, user_id=session['user_id']).first_or_404()
    data = request.get_json()
    
    if 'description' in data:
        transaction.description = data['description']
    if 'amount' in data:
        transaction.amount = float(data['amount'])
    if 'type' in data and data['type'] in ['income', 'expense']:
        transaction.type = data['type']
    if 'date' in data:
        transaction.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    if 'category_id' in data:
        category = Category.query.filter_by(id=data['category_id'], user_id=session['user_id']).first()
        if not category:
            return jsonify({'error': 'Category not found'}), 404
        transaction.category_id = data['category_id']
    if 'is_excluded' in data:
        transaction.is_excluded = data['is_excluded']
    if 'notes' in data:
        transaction.notes = data['notes']
    
    db.session.commit()
    
    # Log the activity
    log_activity(
        ActivityLog.ACTION_UPDATE,
        f'Updated transaction: {transaction.description[:50]}',
        {'transaction_id': id, 'changes': data}
    )
    
    return jsonify(transaction.to_dict())

@transactions_bp.route('/<int:id>', methods=['DELETE'])
@write_required
def delete_transaction(id):
    """Delete a transaction"""
    transaction = Transaction.query.filter_by(id=id, user_id=session['user_id']).first_or_404()
    desc = transaction.description[:50]
    amount = transaction.amount
    db.session.delete(transaction)
    db.session.commit()
    
    # Log the activity
    log_activity(
        ActivityLog.ACTION_DELETE,
        f'Deleted transaction: {desc}',
        {'transaction_id': id, 'amount': amount}
    )
    
    return jsonify({'message': 'Transaction deleted'}), 204

@transactions_bp.route('/exclude/<int:id>', methods=['PUT'])
@write_required
def toggle_exclude(id):
    """Toggle exclude status of a transaction"""
    transaction = Transaction.query.filter_by(id=id, user_id=session['user_id']).first_or_404()
    transaction.is_excluded = not transaction.is_excluded
    db.session.commit()
    return jsonify(transaction.to_dict())

@transactions_bp.route('/category/<int:category_id>', methods=['PUT'])
@write_required
def change_category(category_id):
    """Change category for multiple transactions"""
    data = request.get_json()
    transaction_ids = data.get('transaction_ids', [])
    new_category_id = data.get('new_category_id')
    
    if not new_category_id or not transaction_ids:
        return jsonify({'error': 'Missing new_category_id or transaction_ids'}), 400
    
    category = Category.query.filter_by(id=new_category_id, user_id=session['user_id']).first()
    if not category:
        return jsonify({'error': 'Category not found'}), 404
    
    count = Transaction.query.filter(
        Transaction.id.in_(transaction_ids),
        Transaction.user_id == session['user_id']  # Ensure user isolation
    ).update(
        {'category_id': new_category_id},
        synchronize_session=False
    )
    db.session.commit()
    
    return jsonify({'message': f'{count} transactions updated'})

@transactions_bp.route('/bulk-update/', methods=['PUT'])
@write_required
def bulk_update():
    """Bulk update transactions (category or other fields)"""
    data = request.get_json()
    transaction_ids = data.get('transaction_ids', [])
    
    if not transaction_ids:
        return jsonify({'error': 'Missing transaction_ids'}), 400
    
    # Filter valid transaction IDs for current user
    transactions = Transaction.query.filter(
        Transaction.id.in_(transaction_ids),
        Transaction.user_id == session['user_id']
    ).all()
    
    if not transactions:
        return jsonify({'error': 'No transactions found'}), 404
    
    # Update category if provided
    if 'category_id' in data:
        category_id = data.get('category_id')
        category = Category.query.filter_by(id=category_id, user_id=session['user_id']).first()
        if not category:
            return jsonify({'error': 'Category not found'}), 404
        
        for trans in transactions:
            trans.category_id = category_id
    
    # Update other fields as provided
    if 'type' in data:
        for trans in transactions:
            trans.type = data['type']
    
    if 'is_excluded' in data:
        for trans in transactions:
            trans.is_excluded = data['is_excluded']
    
    db.session.commit()
    
    return jsonify({
        'message': f'{len(transactions)} transaction(s) updated',
        'count': len(transactions)
    })

@transactions_bp.route('/bulk-delete/', methods=['DELETE'])
@write_required
def bulk_delete():
    """Delete multiple transactions by IDs"""
    data = request.get_json()
    transaction_ids = data.get('transaction_ids', [])
    
    if not transaction_ids:
        return jsonify({'error': 'Missing transaction_ids'}), 400
    
    transactions = Transaction.query.filter(
        Transaction.id.in_(transaction_ids),
        Transaction.user_id == session['user_id']
    ).all()
    
    if not transactions:
        return jsonify({'error': 'No transactions found'}), 404
    
    deleted_count = len(transactions)
    for trans in transactions:
        db.session.delete(trans)
    
    db.session.commit()
    
    return jsonify({
        'message': f'{deleted_count} transaction(s) deleted',
        'deleted_count': deleted_count
    })

@transactions_bp.route('/bulk-delete-preview/', methods=['POST'])
@write_required
def bulk_delete_preview():
    """Preview which transactions will be deleted from a file upload"""
    from app.utils.file_processor import process_delete_file
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        # Process the file to get transaction IDs to delete
        transaction_ids = process_delete_file(file)
        
        if not transaction_ids:
            return jsonify({'error': 'No valid transaction IDs found in file'}), 400
        
        # Get the transactions that would be deleted for current user
        transactions = Transaction.query.filter(
            Transaction.id.in_(transaction_ids),
            Transaction.user_id == session['user_id']
        ).all()
        
        return jsonify({
            'count': len(transactions),
            'transactions': [t.to_dict() for t in transactions]
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@transactions_bp.route('/bulk-delete-by-file/', methods=['POST'])
@write_required
def bulk_delete_by_file():
    """Delete transactions by uploading a file (CSV or Excel with Transaction IDs)"""
    from app.utils.file_processor import process_delete_file
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        # Process the file to get transaction IDs to delete
        transaction_ids = process_delete_file(file)
        
        if not transaction_ids:
            return jsonify({'error': 'No valid transaction IDs found in file'}), 400
        
        # Delete the transactions
        transactions = Transaction.query.filter(Transaction.id.in_(transaction_ids)).all()
        deleted_count = len(transactions)
        
        for trans in transactions:
            db.session.delete(trans)
        
        db.session.commit()
        
        return jsonify({
            'message': f'{deleted_count} transaction(s) deleted',
            'deleted_count': deleted_count
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@transactions_bp.route('/clear/all', methods=['DELETE'])
@write_required
def clear_all_transactions():
    """Delete all transactions"""
    try:
        count = Transaction.query.count()
        Transaction.query.delete()
        db.session.commit()
        
        # Log the activity
        log_activity(
            ActivityLog.ACTION_BULK_DELETE,
            f'Cleared all transactions ({count} deleted)',
            {'deleted_count': count, 'clear_type': 'all'}
        )
        
        return jsonify({
            'message': f'All {count} transaction(s) deleted',
            'deleted_count': count
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@transactions_bp.route('/clear/by-date', methods=['DELETE'])
@write_required
def clear_transactions_by_date():
    """Delete transactions for a specific date"""
    target_date = request.args.get('date')
    
    if not target_date:
        return jsonify({'error': 'Date parameter is required (format: YYYY-MM-DD)'}), 400
    
    try:
        parsed_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        
        transactions = Transaction.query.filter(Transaction.date == parsed_date).all()
        count = len(transactions)
        
        for t in transactions:
            db.session.delete(t)
        
        db.session.commit()
        
        # Log the activity
        log_activity(
            ActivityLog.ACTION_BULK_DELETE,
            f'Cleared transactions for {target_date} ({count} deleted)',
            {'deleted_count': count, 'clear_type': 'date', 'date': target_date}
        )
        
        return jsonify({
            'message': f'{count} transaction(s) deleted for {target_date}',
            'deleted_count': count,
            'date': target_date
        })
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@transactions_bp.route('/clear/by-period', methods=['DELETE'])
@write_required
def clear_transactions_by_period():
    """Delete transactions within a date range"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date or not end_date:
        return jsonify({'error': 'Both start_date and end_date are required (format: YYYY-MM-DD)'}), 400
    
    try:
        parsed_start = datetime.strptime(start_date, '%Y-%m-%d').date()
        parsed_end = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        if parsed_start > parsed_end:
            return jsonify({'error': 'start_date must be before or equal to end_date'}), 400
        
        transactions = Transaction.query.filter(
            Transaction.date >= parsed_start,
            Transaction.date <= parsed_end
        ).all()
        count = len(transactions)
        
        for t in transactions:
            db.session.delete(t)
        
        db.session.commit()
        
        # Log the activity
        log_activity(
            ActivityLog.ACTION_BULK_DELETE,
            f'Cleared transactions from {start_date} to {end_date} ({count} deleted)',
            {'deleted_count': count, 'clear_type': 'period', 'start_date': start_date, 'end_date': end_date}
        )
        
        return jsonify({
            'message': f'{count} transaction(s) deleted from {start_date} to {end_date}',
            'deleted_count': count,
            'start_date': start_date,
            'end_date': end_date
        })
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@transactions_bp.route('/clear/preview', methods=['GET'])
def preview_clear_transactions():
    """Preview how many transactions would be deleted"""
    clear_type = request.args.get('type', 'all')  # 'all', 'date', or 'period'
    target_date = request.args.get('date')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    try:
        if clear_type == 'all':
            count = Transaction.query.count()
            return jsonify({'count': count, 'type': 'all'})
        
        elif clear_type == 'date':
            if not target_date:
                return jsonify({'error': 'Date parameter is required'}), 400
            parsed_date = datetime.strptime(target_date, '%Y-%m-%d').date()
            count = Transaction.query.filter(Transaction.date == parsed_date).count()
            return jsonify({'count': count, 'type': 'date', 'date': target_date})
        
        elif clear_type == 'period':
            if not start_date or not end_date:
                return jsonify({'error': 'Both start_date and end_date are required'}), 400
            parsed_start = datetime.strptime(start_date, '%Y-%m-%d').date()
            parsed_end = datetime.strptime(end_date, '%Y-%m-%d').date()
            count = Transaction.query.filter(
                Transaction.date >= parsed_start,
                Transaction.date <= parsed_end
            ).count()
            return jsonify({'count': count, 'type': 'period', 'start_date': start_date, 'end_date': end_date})
        
        else:
            return jsonify({'error': 'Invalid type. Use: all, date, or period'}), 400
            
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
