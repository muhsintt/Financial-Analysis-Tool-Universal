from flask import Blueprint, request, jsonify
from app import db
from app.models.user import User
from app.routes.auth import superuser_required, login_required

users_bp = Blueprint('users', __name__, url_prefix='/api/users')

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
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    if len(username) < 3:
        return jsonify({'error': 'Username must be at least 3 characters'}), 400
    
    if len(password) < 4:
        return jsonify({'error': 'Password must be at least 4 characters'}), 400
    
    if role not in ['superuser', 'standard']:
        return jsonify({'error': 'Role must be superuser or standard'}), 400
    
    # Check if username already exists
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    user = User(
        username=username,
        role=role,
        is_default=False
    )
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
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
        if data['role'] not in ['superuser', 'standard']:
            return jsonify({'error': 'Role must be superuser or standard'}), 400
        # Cannot change role of default admin
        if user.is_default:
            return jsonify({'error': 'Cannot change the role of the default admin'}), 400
        user.role = data['role']
    
    if 'password' in data and data['password']:
        if len(data['password']) < 4:
            return jsonify({'error': 'Password must be at least 4 characters'}), 400
        user.set_password(data['password'])
    
    db.session.commit()
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
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'message': 'User deleted successfully'}), 200

@users_bp.route('/init', methods=['POST'])
def init_default_admin():
    """Initialize default admin user"""
    result = User.create_default_admin()
    if result:
        return jsonify({'message': 'Default admin created', 'created': True})
    return jsonify({'message': 'Default admin already exists', 'created': False})
