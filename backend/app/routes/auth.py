from flask import Blueprint, request, jsonify, session
from app import db
from app.models.user import User
from app.models.activity_log import ActivityLog
from app.models.log_settings import LogSettings
from functools import wraps

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

def log_activity(action, category, description, details=None):
    """Helper to log activities - checks settings before logging"""
    import json
    try:
        settings = LogSettings.get_settings()
        if not settings.should_log(action, category):
            return
    except:
        pass  # If settings fail, log anyway
    
    log = ActivityLog(
        action=action,
        category=category,
        description=description,
        details=json.dumps(details) if details else None,
        user_id=session.get('user_id'),
        username=session.get('username', 'anonymous'),
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

def login_required(f):
    """Decorator to require login for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required', 'authenticated': False}), 401
        return f(*args, **kwargs)
    return decorated_function

def superuser_required(f):
    """Decorator to require superuser role for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required', 'authenticated': False}), 401
        
        user = User.query.get(session['user_id'])
        if not user or not user.is_superuser():
            return jsonify({'error': 'Superuser access required', 'authorized': False}), 403
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Get the currently logged in user"""
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login endpoint"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    user = User.query.filter_by(username=username).first()
    
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid username or password'}), 401
    
    # Set session
    session['user_id'] = user.id
    session['username'] = user.username
    session['role'] = user.role
    session.permanent = True
    
    # Log successful login
    log_activity(
        ActivityLog.ACTION_LOGIN,
        ActivityLog.CATEGORY_AUTH,
        f'User {user.username} logged in',
        {'user_id': user.id, 'role': user.role}
    )
    
    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict()
    })

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout endpoint"""
    username = session.get('username', 'unknown')
    user_id = session.get('user_id')
    
    # Log logout before clearing session
    if user_id:
        log = ActivityLog(
            action=ActivityLog.ACTION_LOGOUT,
            category=ActivityLog.CATEGORY_AUTH,
            description=f'User {username} logged out',
            user_id=user_id,
            username=username,
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
    
    session.clear()
    return jsonify({'message': 'Logged out successfully'})

@auth_bp.route('/me', methods=['GET'])
def get_current_user_info():
    """Get current user info"""
    if 'user_id' not in session:
        return jsonify({'authenticated': False}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return jsonify({'authenticated': False}), 401
    
    return jsonify({
        'authenticated': True,
        'user': user.to_dict()
    })

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change current user's password"""
    data = request.get_json()
    
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    
    if not current_password or not new_password:
        return jsonify({'error': 'Current password and new password are required'}), 400
    
    if len(new_password) < 4:
        return jsonify({'error': 'Password must be at least 4 characters'}), 400
    
    user = User.query.get(session['user_id'])
    
    if not user.check_password(current_password):
        return jsonify({'error': 'Current password is incorrect'}), 401
    
    user.set_password(new_password)
    db.session.commit()
    
    # Log password change
    log_activity(
        ActivityLog.ACTION_PASSWORD_CHANGE,
        ActivityLog.CATEGORY_AUTH,
        f'User {user.username} changed their password',
        {'user_id': user.id}
    )
    
    return jsonify({'message': 'Password changed successfully'})
