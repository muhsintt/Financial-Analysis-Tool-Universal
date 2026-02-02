from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models.transaction import Transaction
from app.models.category import Category
from app.utils.file_processor import process_excel_file, process_csv_file
from datetime import datetime
import os

uploads_bp = Blueprint('uploads', __name__, url_prefix='/api/uploads')

@uploads_bp.route('/upload', methods=['POST'])
def upload_file():
    """Upload and process a bank statement file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Validate file extension
    allowed_extensions = {'csv', 'xlsx', 'xls'}
    if not '.' in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        return jsonify({'error': 'Invalid file type. Allowed: CSV, XLSX, XLS'}), 400
    
    try:
        upload_folder = current_app.config['UPLOAD_FOLDER']
        filename = f"{datetime.now().timestamp()}_{file.filename}"
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        # Process file based on extension
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        
        if file_ext == 'csv':
            transactions_data = process_csv_file(filepath)
        else:  # xlsx or xls
            transactions_data = process_excel_file(filepath)
        
        # Save transactions to database
        created_count = 0
        for trans_data in transactions_data:
            # Use the category_id directly from file processor
            category_id = trans_data.get('category_id')
            
            # If no category_id, try to find or create default
            if not category_id:
                category = Category.query.filter_by(name='Uncategorized').first()
                if not category:
                    category = Category(
                        name='Uncategorized',
                        type='expense',
                        color='#95a5a6',
                        icon='question'
                    )
                    db.session.add(category)
                    db.session.flush()
                category_id = category.id
            
            transaction = Transaction(
                description=trans_data['description'],
                amount=float(trans_data['amount']),
                type=trans_data['type'],
                date=trans_data['date'],
                category_id=category_id,
                source='upload',
                notes=trans_data.get('notes', '')
            )
            
            db.session.add(transaction)
            created_count += 1
        
        db.session.commit()
        
        # Clean up uploaded file
        os.remove(filepath)
        
        return jsonify({
            'message': 'File processed successfully',
            'transactions_created': created_count
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@uploads_bp.route('/preview', methods=['POST'])
def preview_file():
    """Preview file contents before uploading"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        upload_folder = current_app.config['UPLOAD_FOLDER']
        filename = f"preview_{datetime.now().timestamp()}_{file.filename}"
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        
        if file_ext == 'csv':
            preview_data = process_csv_file(filepath, limit=10)
        else:
            preview_data = process_excel_file(filepath, limit=10)
        
        os.remove(filepath)
        
        return jsonify({
            'preview': preview_data,
            'total_rows': len(preview_data)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400
