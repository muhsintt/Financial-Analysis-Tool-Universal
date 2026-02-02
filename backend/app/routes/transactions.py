from flask import Blueprint, request, jsonify
from app import db
from app.models.transaction import Transaction
from app.models.category import Category
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_

transactions_bp = Blueprint('transactions', __name__, url_prefix='/api/transactions')

@transactions_bp.route('/', methods=['GET'])
def get_transactions():
    """Get all transactions with optional filters"""
    category_id = request.args.get('category_id', type=int)
    transaction_type = request.args.get('type')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    include_excluded = request.args.get('include_excluded', 'false').lower() == 'true'
    
    query = Transaction.query
    
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
    transaction = Transaction.query.get_or_404(id)
    return jsonify(transaction.to_dict())

@transactions_bp.route('/', methods=['POST'])
def create_transaction():
    """Create a new transaction"""
    data = request.get_json()
    
    required_fields = ['description', 'amount', 'type', 'date', 'category_id']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if data['type'] not in ['income', 'expense']:
        return jsonify({'error': 'Type must be income or expense'}), 400
    
    # Verify category exists
    category = Category.query.get(data['category_id'])
    if not category:
        return jsonify({'error': 'Category not found'}), 404
    
    transaction = Transaction(
        description=data['description'],
        amount=float(data['amount']),
        type=data['type'],
        date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
        category_id=data['category_id'],
        notes=data.get('notes', '')
    )
    
    db.session.add(transaction)
    db.session.commit()
    
    return jsonify(transaction.to_dict()), 201

@transactions_bp.route('/<int:id>', methods=['PUT'])
def update_transaction(id):
    """Update a transaction"""
    transaction = Transaction.query.get_or_404(id)
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
        category = Category.query.get(data['category_id'])
        if not category:
            return jsonify({'error': 'Category not found'}), 404
        transaction.category_id = data['category_id']
    if 'is_excluded' in data:
        transaction.is_excluded = data['is_excluded']
    if 'notes' in data:
        transaction.notes = data['notes']
    
    db.session.commit()
    return jsonify(transaction.to_dict())

@transactions_bp.route('/<int:id>', methods=['DELETE'])
def delete_transaction(id):
    """Delete a transaction"""
    transaction = Transaction.query.get_or_404(id)
    db.session.delete(transaction)
    db.session.commit()
    return jsonify({'message': 'Transaction deleted'}), 204

@transactions_bp.route('/exclude/<int:id>', methods=['PUT'])
def toggle_exclude(id):
    """Toggle exclude status of a transaction"""
    transaction = Transaction.query.get_or_404(id)
    transaction.is_excluded = not transaction.is_excluded
    db.session.commit()
    return jsonify(transaction.to_dict())

@transactions_bp.route('/category/<int:category_id>', methods=['PUT'])
def change_category(category_id):
    """Change category for multiple transactions"""
    data = request.get_json()
    transaction_ids = data.get('transaction_ids', [])
    new_category_id = data.get('new_category_id')
    
    if not new_category_id or not transaction_ids:
        return jsonify({'error': 'Missing new_category_id or transaction_ids'}), 400
    
    category = Category.query.get(new_category_id)
    if not category:
        return jsonify({'error': 'Category not found'}), 404
    
    count = Transaction.query.filter(Transaction.id.in_(transaction_ids)).update(
        {'category_id': new_category_id},
        synchronize_session=False
    )
    db.session.commit()
    
    return jsonify({'message': f'{count} transactions updated'})

@transactions_bp.route('/bulk-update/', methods=['PUT'])
def bulk_update():
    """Bulk update transactions (category or other fields)"""
    data = request.get_json()
    transaction_ids = data.get('transaction_ids', [])
    
    if not transaction_ids:
        return jsonify({'error': 'Missing transaction_ids'}), 400
    
    # Filter valid transaction IDs
    transactions = Transaction.query.filter(Transaction.id.in_(transaction_ids)).all()
    
    if not transactions:
        return jsonify({'error': 'No transactions found'}), 404
    
    # Update category if provided
    if 'category_id' in data:
        category_id = data.get('category_id')
        category = Category.query.get(category_id)
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
def bulk_delete():
    """Delete multiple transactions by IDs"""
    data = request.get_json()
    transaction_ids = data.get('transaction_ids', [])
    
    if not transaction_ids:
        return jsonify({'error': 'Missing transaction_ids'}), 400
    
    transactions = Transaction.query.filter(Transaction.id.in_(transaction_ids)).all()
    
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

@transactions_bp.route('/bulk-delete-by-file/', methods=['POST'])
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


