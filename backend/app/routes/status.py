from flask import Blueprint, jsonify, request, session
from app import db
from app.models.api_status import ApiStatus
from app.models.activity_log import ActivityLog
from app.models.log_settings import LogSettings
from app.routes.auth import write_required
from datetime import datetime
import json

status_bp = Blueprint('status', __name__, url_prefix='/api/status')

def log_activity(action, description, details=None):
    """Helper to log settings activities - checks settings before logging"""
    try:
        settings = LogSettings.get_settings()
        if not settings.should_log(action, ActivityLog.CATEGORY_SETTINGS):
            return
    except:
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
