from flask import Blueprint, request, jsonify, session
from app import db
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.activity_log import ActivityLog
from app.models.log_settings import LogSettings
from app.routes.auth import write_required, login_required
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
@login_required
def get_transactions():
    """Get all transactions with optional filters"""
    try:
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
        print(f"Found {len(transactions)} transactions for user {session['user_id']}")  # Debug log
        
        result = []
        for t in transactions:
            try:
                result.append(t.to_dict())
            except Exception as e:
                print(f"Error serializing transaction {t.id}: {e}")  # Debug log
                continue
                
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in get_transactions: {e}")  # Debug log
        return jsonify({'error': 'Internal server error'}), 500

@transactions_bp.route('/<int:id>', methods=['GET'])
@login_required
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
    
    # Verify category exists and belongs to current user (or is a system category)
    category = Category.query.filter(
        Category.id == data['category_id'],
        db.or_(Category.user_id == session['user_id'], Category.user_id.is_(None))
    ).first()
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
        category = Category.query.filter(
            Category.id == data['category_id'],
            db.or_(Category.user_id == session['user_id'], Category.user_id.is_(None))
        ).first()
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
    
    category = Category.query.filter(
        Category.id == new_category_id,
        db.or_(Category.user_id == session['user_id'], Category.user_id.is_(None))
    ).first()
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
        category = Category.query.filter(
            Category.id == category_id,
            db.or_(Category.user_id == session['user_id'], Category.user_id.is_(None))
        ).first()
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


@transactions_bp.route('/sanitize-preview', methods=['GET'])
@login_required
def sanitize_preview():
    """Detect potential inter-account transfer pairs for sanitization."""
    user_id = session['user_id']

    # Get all non-excluded transactions for current user
    transactions = Transaction.query.filter_by(
        user_id=user_id,
        is_excluded=False
    ).order_by(Transaction.date).all()

    # Build index by rounded amount for efficient matching
    from collections import defaultdict
    amount_index = defaultdict(list)
    for t in transactions:
        key = round(t.amount, 2)
        amount_index[key].append(t)

    pairs = []
    used_ids = set()

    for amount_key, txns in amount_index.items():
        if len(txns) < 2:
            continue

        # Find pairs: one income + one expense, different bank/source, within 3 days
        income_txns = [t for t in txns if t.type == 'income']
        expense_txns = [t for t in txns if t.type == 'expense']

        for inc in income_txns:
            if inc.id in used_ids:
                continue
            for exp in expense_txns:
                if exp.id in used_ids:
                    continue
                # Check different bank or different upload source
                different_source = False
                if inc.bank_source and exp.bank_source and inc.bank_source != exp.bank_source:
                    different_source = True
                elif inc.upload_id and exp.upload_id and inc.upload_id != exp.upload_id:
                    different_source = True
                elif inc.bank_source != exp.bank_source:
                    # One has bank_source, other doesn't or different
                    if inc.bank_source or exp.bank_source:
                        different_source = True

                if not different_source:
                    continue

                # Check within 3 days
                day_diff = abs((inc.date - exp.date).days)
                if day_diff > 3:
                    continue

                # Valid pair found
                pairs.append({
                    'id': f"{inc.id}-{exp.id}",
                    'transaction_a': {
                        'id': inc.id,
                        'date': inc.date.isoformat(),
                        'description': inc.description,
                        'amount': inc.amount,
                        'type': inc.type,
                        'bank_source': inc.bank_source or 'Unknown',
                        'category_name': inc.category.full_name if inc.category and hasattr(inc.category, 'full_name') else (inc.category.name if inc.category else 'Unknown')
                    },
                    'transaction_b': {
                        'id': exp.id,
                        'date': exp.date.isoformat(),
                        'description': exp.description,
                        'amount': exp.amount,
                        'type': exp.type,
                        'bank_source': exp.bank_source or 'Unknown',
                        'category_name': exp.category.full_name if exp.category and hasattr(exp.category, 'full_name') else (exp.category.name if exp.category else 'Unknown')
                    },
                    'amount': amount_key,
                    'day_difference': day_diff
                })
                used_ids.add(inc.id)
                used_ids.add(exp.id)
                break  # Move to next income transaction

    return jsonify({
        'pairs': pairs,
        'count': len(pairs)
    })


@transactions_bp.route('/sanitize', methods=['POST'])
@write_required
def apply_sanitization():
    """Exclude selected transaction pairs as inter-account transfers."""
    user_id = session['user_id']
    data = request.get_json()
    pair_ids = data.get('pair_ids', [])

    if not pair_ids:
        return jsonify({'error': 'No pairs selected'}), 400

    excluded_count = 0

    for pair_id in pair_ids:
        parts = pair_id.split('-')
        if len(parts) != 2:
            continue
        try:
            id_a = int(parts[0])
            id_b = int(parts[1])
        except ValueError:
            continue

        # Revalidate: both must belong to user, not already excluded, same amount, different source
        t_a = Transaction.query.filter_by(id=id_a, user_id=user_id, is_excluded=False).first()
        t_b = Transaction.query.filter_by(id=id_b, user_id=user_id, is_excluded=False).first()

        if not t_a or not t_b:
            continue
        if round(t_a.amount, 2) != round(t_b.amount, 2):
            continue

        # Exclude both and add note
        t_a.is_excluded = True
        t_a.notes = (t_a.notes + '\n' if t_a.notes else '') + f'[Sanitized] Inter-account transfer detected (paired with transaction #{t_b.id})'
        t_b.is_excluded = True
        t_b.notes = (t_b.notes + '\n' if t_b.notes else '') + f'[Sanitized] Inter-account transfer detected (paired with transaction #{t_a.id})'

        excluded_count += 2

    db.session.commit()

    log_activity('sanitize', f'Sanitized {excluded_count} transactions ({len(pair_ids)} pairs)',
                 {'pair_ids': pair_ids, 'excluded_count': excluded_count})

    return jsonify({
        'success': True,
        'excluded_count': excluded_count,
        'pairs_processed': len(pair_ids)
    })
