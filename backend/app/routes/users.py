from flask import Blueprint, request, jsonify, session
from app import db
from app.models.user import User
from app.models.activity_log import ActivityLog
from app.models.log_settings import LogSettings
from app.routes.auth import superuser_required, login_required
import json

users_bp = Blueprint('users', __name__, url_prefix='/api/users')

def log_activity(action, description, details=None):
    """Helper to log user management activities - checks settings before logging"""
    try:
        settings = LogSettings.get_settings()
        if not settings.should_log(action, ActivityLog.CATEGORY_USER):
            return
    except:
        pass
    
    log = ActivityLog(
        action=action,
        category=ActivityLog.CATEGORY_USER,
        description=description,
        details=json.dumps(details) if details else None,
        user_id=session.get('user_id'),
        username=session.get('username', 'anonymous'),
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

@users_bp.route('/', methods=['GET'])
@login_required
def get_users():
    """Get all users (superuser only sees all, standard users see only themselves)"""
    from flask import session
    
    current_user = User.query.get(session['user_id'])
    
    if current_user.is_superuser():
        users = User.query.order_by(User.created_at).all()
        return jsonify([u.to_dict() for u in users])
    else:
        # Standard users can only see their own info
        return jsonify([current_user.to_dict()])

@users_bp.route('/<int:id>', methods=['GET'])
@login_required
def get_user(id):
    """Get a specific user"""
    from flask import session
    
    current_user = User.query.get(session['user_id'])
    
    # Standard users can only view themselves
    if not current_user.is_superuser() and current_user.id != id:
        return jsonify({'error': 'Access denied'}), 403
    
    user = User.query.get_or_404(id)
    return jsonify(user.to_dict())

@users_bp.route('/', methods=['POST'])
@superuser_required
def create_user():
    """Create a new user (superuser only)"""
    data = request.get_json()
    
    username = data.get('username', '').strip()
    password = data.get('password', '')
    role = data.get('role', 'standard')
    calendar_preference = data.get('calendar_preference', 'both')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    if len(username) < 3:
        return jsonify({'error': 'Username must be at least 3 characters'}), 400
    
    if len(password) < 4:
        return jsonify({'error': 'Password must be at least 4 characters'}), 400
    
    if role not in User.ROLE_CHOICES:
        return jsonify({'error': 'Role must be superuser, standard, or viewer'}), 400
    
    if calendar_preference not in User.CALENDAR_CHOICES:
        return jsonify({'error': 'Calendar preference must be both, gregorian, or badi'}), 400
    
    # Check if username already exists
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    user = User(
        username=username,
        role=role,
        is_default=False,
        calendar_preference=calendar_preference
    )
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    # Log user creation
    log_activity(
        ActivityLog.ACTION_CREATE,
        f'Created user: {username} ({role}, calendar: {calendar_preference})',
        {'new_user_id': user.id, 'username': username, 'role': role, 'calendar_preference': calendar_preference}
    )
    
    return jsonify(user.to_dict()), 201

@users_bp.route('/<int:id>', methods=['PUT'])
@superuser_required
def update_user(id):
    """Update a user (superuser only)"""
    user = User.query.get_or_404(id)
    data = request.get_json()
    
    # Cannot change the default admin username
    if user.is_default and 'username' in data and data['username'] != user.username:
        return jsonify({'error': 'Cannot change the default admin username'}), 400
    
    if 'username' in data:
        new_username = data['username'].strip()
        if len(new_username) < 3:
            return jsonify({'error': 'Username must be at least 3 characters'}), 400
        # Check if username is taken by another user
        existing = User.query.filter_by(username=new_username).first()
        if existing and existing.id != id:
            return jsonify({'error': 'Username already exists'}), 400
        user.username = new_username
    
    if 'role' in data:
        if data['role'] not in User.ROLE_CHOICES:
            return jsonify({'error': 'Role must be superuser, standard, or viewer'}), 400
        # Cannot change role of default admin
        if user.is_default:
            return jsonify({'error': 'Cannot change the role of the default admin'}), 400
        user.role = data['role']
    
    if 'password' in data and data['password']:
        if len(data['password']) < 4:
            return jsonify({'error': 'Password must be at least 4 characters'}), 400
        user.set_password(data['password'])
    
    if 'calendar_preference' in data:
        if data['calendar_preference'] not in User.CALENDAR_CHOICES:
            return jsonify({'error': 'Calendar preference must be both, gregorian, or badi'}), 400
        user.calendar_preference = data['calendar_preference']
    
    db.session.commit()
    
    # Log user update
    log_activity(
        ActivityLog.ACTION_UPDATE,
        f'Updated user: {user.username}',
        {'updated_user_id': id, 'changes': list(data.keys())}
    )
    
    return jsonify(user.to_dict())

@users_bp.route('/<int:id>', methods=['DELETE'])
@superuser_required
def delete_user(id):
    """Delete a user (superuser only, cannot delete default admin)"""
    from flask import session
    
    user = User.query.get_or_404(id)
    
    # Cannot delete the default admin
    if user.is_default:
        return jsonify({'error': 'Cannot delete the default admin user'}), 400
    
    # Cannot delete yourself
    if user.id == session['user_id']:
        return jsonify({'error': 'Cannot delete your own account'}), 400
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    # Log user deletion
    log_activity(
        ActivityLog.ACTION_DELETE,
        f'Deleted user: {username}',
        {'deleted_user_id': id, 'username': username}
    )
    
    return jsonify({'message': 'User deleted successfully'}), 200

@users_bp.route('/init', methods=['POST'])
def init_default_admin():
    """Initialize default admin user"""
    result = User.create_default_admin()
    if result:
        return jsonify({'message': 'Default admin created', 'created': True})
    return jsonify({'message': 'Default admin already exists', 'created': False})
