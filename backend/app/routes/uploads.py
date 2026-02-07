from flask import Blueprint, request, jsonify, current_app, send_file, session
from app import db
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.upload import Upload
from app.models.activity_log import ActivityLog
from app.models.log_settings import LogSettings
from app.routes.auth import write_required
from app.utils.file_processor import process_excel_file, process_csv_file
from datetime import datetime
import os
import io
import csv
import json

uploads_bp = Blueprint('uploads', __name__, url_prefix='/api/uploads')

def log_activity(action, description, details=None):
    """Helper to log upload activities - checks settings before logging"""
    try:
        settings = LogSettings.get_settings()
        if not settings.should_log(action, ActivityLog.CATEGORY_UPLOAD):
            return
    except:
        pass
    
    log = ActivityLog(
        action=action,
        category=ActivityLog.CATEGORY_UPLOAD,
        description=description,
        details=json.dumps(details) if details else None,
        user_id=session.get('user_id'),
        username=session.get('username', 'anonymous'),
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

@uploads_bp.route('/', methods=['GET'])
def get_uploads():
    """Get all upload records"""
    uploads = Upload.query.order_by(Upload.created_at.desc()).all()
    return jsonify([u.to_dict() for u in uploads])

@uploads_bp.route('/<int:upload_id>', methods=['GET'])
def get_upload(upload_id):
    """Get a specific upload record"""
    upload = Upload.query.get_or_404(upload_id)
    return jsonify(upload.to_dict())

@uploads_bp.route('/<int:upload_id>/transactions', methods=['GET'])
def get_upload_transactions(upload_id):
    """Get all transactions for a specific upload"""
    upload = Upload.query.get_or_404(upload_id)
    transactions = Transaction.query.filter_by(upload_id=upload_id).order_by(Transaction.date.desc()).all()
    return jsonify({
        'upload': upload.to_dict(),
        'transactions': [t.to_dict() for t in transactions]
    })

@uploads_bp.route('/<int:upload_id>/download', methods=['GET'])
def download_upload_transactions(upload_id):
    """Download transactions from a specific upload as CSV"""
    upload = Upload.query.get_or_404(upload_id)
    transactions = Transaction.query.filter_by(upload_id=upload_id).order_by(Transaction.date.desc()).all()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Date', 'Description', 'Amount', 'Type', 'Category', 'Status', 'Notes'])
    
    # Write transactions
    for t in transactions:
        writer.writerow([
            t.date.isoformat(),
            t.description,
            t.amount,
            t.type,
            t.category.name if t.category else 'Uncategorized',
            'Excluded' if t.is_excluded else 'Included',
            t.notes or ''
        ])
    
    # Create response
    output.seek(0)
    
    # Log the download
    log_activity(
        ActivityLog.ACTION_DOWNLOAD,
        f'Downloaded transactions from upload: {upload.original_filename}',
        {'upload_id': upload_id, 'transaction_count': len(transactions)}
    )
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f"upload_{upload_id}_{upload.original_filename.rsplit('.', 1)[0]}.csv"
    )

@uploads_bp.route('/<int:upload_id>', methods=['DELETE'])
@write_required
def delete_upload(upload_id):
    """Delete an upload and all its related transactions"""
    upload = Upload.query.get_or_404(upload_id)
    original_filename = upload.original_filename
    
    # Delete all transactions related to this upload
    transaction_count = Transaction.query.filter_by(upload_id=upload_id).count()
    Transaction.query.filter_by(upload_id=upload_id).delete()
    
    # Delete the upload record
    db.session.delete(upload)
    db.session.commit()
    
    # Log the deletion
    log_activity(
        ActivityLog.ACTION_DELETE,
        f'Deleted upload: {original_filename} ({transaction_count} transactions)',
        {'upload_id': upload_id, 'filename': original_filename, 'deleted_transactions': transaction_count}
    )
    
    return jsonify({
        'message': f'Upload and {transaction_count} transaction(s) deleted',
        'deleted_transactions': transaction_count
    })

@uploads_bp.route('/upload', methods=['POST'])
@write_required
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
        
        # Get file size before saving
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Seek back to beginning
        
        file.save(filepath)
        
        # Process file based on extension
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        
        if file_ext == 'csv':
            transactions_data = process_csv_file(filepath)
        else:  # xlsx or xls
            transactions_data = process_excel_file(filepath)
        
        # Get uploaded_by from request (if provided)
        uploaded_by = request.form.get('uploaded_by', 'system')
        
        # Create Upload record first
        upload_record = Upload(
            filename=filename,
            original_filename=file.filename,
            file_size=file_size,
            file_type=file_ext,
            transaction_count=0,
            uploaded_by=uploaded_by,
            status='processing'
        )
        db.session.add(upload_record)
        db.session.flush()  # Get the ID
        
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
                upload_id=upload_record.id,  # Link to upload record
                notes=trans_data.get('notes', '')
            )
            
            db.session.add(transaction)
            created_count += 1
        
        # Update upload record with transaction count
        upload_record.transaction_count = created_count
        upload_record.status = 'completed'
        
        db.session.commit()
        
        # Log the upload
        log_activity(
            ActivityLog.ACTION_UPLOAD,
            f'Uploaded file: {file.filename} ({created_count} transactions)',
            {'upload_id': upload_record.id, 'filename': file.filename, 'transaction_count': created_count}
        )
        
        # Clean up uploaded file
        os.remove(filepath)
        
        return jsonify({
            'message': 'File processed successfully',
            'transactions_created': created_count,
            'upload_id': upload_record.id,
            'upload': upload_record.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
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
