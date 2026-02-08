
import os
import io
import json
from datetime import datetime
from flask import Blueprint, jsonify, request, session, send_file, current_app
from app import db
from app.models.api_status import ApiStatus
from app.models.activity_log import ActivityLog
from app.models.log_settings import LogSettings
from app.models.user import User
from app.models.category import Category
from app.models.categorization_rule import CategorizationRule
from app.models.budget import Budget
from app.routes.auth import write_required


status_bp = Blueprint('status', __name__, url_prefix='/api/status')


# --- PROFILE RESET ---
@status_bp.route('/settings/reset', methods=['POST'])
@write_required
def reset_profile():
    """Reset all settings and data except default admin user"""
    User.query.filter(User.username != 'admin').delete()
    Category.query.delete()
    CategorizationRule.query.delete()
    Budget.query.delete()
    ActivityLog.query.delete()
    LogSettings.query.delete()
    db.session.commit()
    return jsonify({
        'success': True,
        'message': 'Profile reset to default. Only admin user remains.'
    })


# --- DATABASE BACKUP ---
@status_bp.route('/settings/db/backup', methods=['GET'])
@write_required
def backup_database():
    """Download the full SQLite database file"""
    db_path = os.path.join(
        current_app.root_path, '..', 'data', 'expense_tracker.db'
    )
    db_path = os.path.abspath(db_path)
    if not os.path.exists(db_path):
        return jsonify({'error': 'Database file not found'}), 404
    return send_file(
        db_path,
        as_attachment=True,
        download_name='expense_tracker.db',
        mimetype='application/octet-stream'
    )
# --- DATABASE RESTORE ---
@status_bp.route('/settings/db/restore', methods=['POST'])
@write_required
def restore_database():
    """Restore the full SQLite database file (overwrites current DB)"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['file']
    db_path = os.path.join(
        current_app.root_path, '..', 'data', 'expense_tracker.db'
    )
    db_path = os.path.abspath(db_path)
    file.save(db_path)
    return jsonify({
        'success': True,
        'message': 'Database restored. Please restart the app.'
    })



def log_activity(action, description, details=None):
    """Helper to log settings activities - checks settings before logging"""
    try:
        settings = LogSettings.get_settings()
        if not settings.should_log(action, ActivityLog.CATEGORY_SETTINGS):
            return
    except Exception:
        pass

    log = ActivityLog(
        action=action,
        category=ActivityLog.CATEGORY_SETTINGS,
        description=description,
        details=json.dumps(details) if details else None,
        user_id=session.get('user_id'),
        username=session.get('username', 'anonymous'),
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()



def get_or_create_api_status():
    """Get or create the API status record"""
    status = ApiStatus.query.first()
    if not status:
        status = ApiStatus(is_enabled=True, last_toggled_by='system')
        db.session.add(status)
        db.session.commit()
    return status




 # --- SETTINGS BACKUP/RESTORE ---

@status_bp.route('/settings/backup', methods=['GET'])
def backup_settings():
    """Download all settings as a JSON file"""
    users = [u.to_dict() for u in User.query.all()]
    categories = [
        c.to_dict(include_subcategories=True)
        for c in Category.query.all()
    ]
    log_settings = LogSettings.get_settings().to_dict()
    rules = [r.to_dict() for r in CategorizationRule.query.all()]
    budgets = [b.to_dict() for b in Budget.query.all()]
    data = {
        'users': users,
        'categories': categories,
        'log_settings': log_settings,
        'rules': rules,
        'budgets': budgets
    }
    buf = io.BytesIO()
    buf.write(json.dumps(data, indent=2, default=str).encode('utf-8'))
    buf.seek(0)
    return send_file(
        buf,
        mimetype='application/json',
        as_attachment=True,
        download_name='settings-backup.json'
    )
@status_bp.route('/settings/restore', methods=['POST'])
@write_required
def restore_settings():
    """Restore all settings from a JSON file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['file']
    try:
        data = json.load(file)
    except Exception as e:
        return jsonify({'error': f'Invalid JSON: {e}'}), 400

    # Restore users (skip if username exists)
    for u in data.get('users', []):
        if not User.query.filter_by(username=u['username']).first():
            user = User(
                username=u['username'],
                role=u.get('role', 'standard'),
                is_default=u.get('is_default', False),
                calendar_preference=u.get('calendar_preference', 'both')
            )

    # Restore categories (skip if name exists)
    for c in data.get('categories', []):
        if not Category.query.filter_by(
            name=c['name'], parent_id=c['parent_id']
        ).first():
            cat = Category(
                name=c['name'],
                type=c['type'],
                color=c.get('color', '#3498db'),
                icon=c.get('icon', 'folder'),
                is_default=c.get('is_default', False),
                parent_id=c.get('parent_id')
            )
            db.session.add(cat)

    # Restore log settings (overwrite)
    if 'log_settings' in data:
        s = LogSettings.get_settings()
        for k, v in data['log_settings'].items():
            if hasattr(s, k):
                setattr(s, k, v)
        db.session.add(s)

    # Restore rules (skip if name exists)
    for r in data.get('rules', []):
        if not CategorizationRule.query.filter_by(name=r['name']).first():
            rule = CategorizationRule(
                name=r['name'],
                keywords=r['keywords'],
                category_id=r['category_id'],
                priority=r.get('priority', 0),
                is_active=r.get('is_active', True)
            )
            db.session.add(rule)

    # Restore budgets (skip if category_id/period/year/month/week exists)
    for b in data.get('budgets', []):
        exists = Budget.query.filter_by(
            category_id=b['category_id'],
            period=b['period'],
            year=b['year'],
            month=b.get('month'),
            week=b.get('week')
        ).first()
        if not exists:
            budget = Budget(
                category_id=b['category_id'],
                amount=b['amount'],
                period=b['period'],
                year=b['year'],
                month=b.get('month'),
                week=b.get('week'),
                for_excluded=b.get('for_excluded', False)
            )
            db.session.add(budget)

    db.session.commit()
    return jsonify({'success': True, 'message': 'Settings restored'})

@status_bp.route('/', methods=['GET'])
def get_status():
    """Get current API status"""

    status = get_or_create_api_status()
    return jsonify(status.to_dict())

@status_bp.route('/toggle', methods=['POST'])
@write_required
def toggle_api():
    """Toggle API on/off"""
    status = get_or_create_api_status()
    data = request.get_json() or {}
    
    # Toggle the status
    status.is_enabled = not status.is_enabled
    status.last_toggled = datetime.utcnow()
    status.last_toggled_by = data.get('toggled_by', 'user')
    
    db.session.commit()
    
    # Log the toggle
    new_state = 'enabled' if status.is_enabled else 'disabled'
    log_activity(
        ActivityLog.ACTION_TOGGLE,
        f'API {new_state}',
        {'new_state': new_state, 'toggled_by': status.last_toggled_by}
    )
    
    return jsonify({
        'message': f'API is now {status.to_dict()["status"]}',
        'data': status.to_dict()
    }), 200

@status_bp.route('/set', methods=['POST'])
@write_required
def set_status():
    """Set API status to specific state"""
    status = get_or_create_api_status()
    data = request.get_json()
    
    if 'is_enabled' not in data:
        return jsonify({'error': 'is_enabled field is required'}), 400
    
    status.is_enabled = bool(data['is_enabled'])
    status.last_toggled = datetime.utcnow()
    status.last_toggled_by = data.get('toggled_by', 'user')
    
    db.session.commit()
    
    return jsonify({
        'message': f'API is now {status.to_dict()["status"]}',
        'data': status.to_dict()
    }), 200
