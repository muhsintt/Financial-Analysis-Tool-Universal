import os
import secrets
from flask import Flask, render_template, send_from_directory, jsonify, request, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta

db = SQLAlchemy()

def create_app():
    # Get absolute paths
    app_dir = os.path.dirname(__file__)  # backend/app
    backend_dir = os.path.dirname(app_dir)  # backend
    parent_dir = os.path.dirname(backend_dir)  # expense_tracker
    
    app = Flask(__name__, 
                template_folder=os.path.abspath(os.path.join(parent_dir, 'frontend', 'templates')),
                static_folder=os.path.abspath(os.path.join(parent_dir, 'frontend', 'static')))
    
    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(backend_dir, "expense_tracker.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file upload
    app.config['UPLOAD_FOLDER'] = os.path.join(backend_dir, 'uploads')
    
    # Session configuration
    app.config['SECRET_KEY'] = secrets.token_hex(32)
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    
    # Ensure directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    CORS(app, supports_credentials=True)
    
    # Register blueprints
    from app.routes.transactions import transactions_bp
    from app.routes.budgets import budgets_bp
    from app.routes.reports import reports_bp
    from app.routes.uploads import uploads_bp
    from app.routes.categories import categories_bp
    from app.routes.rules import rules_bp
    from app.routes.status import status_bp
    from app.routes.auth import auth_bp
    from app.routes.users import users_bp
    
    app.register_blueprint(transactions_bp)
    app.register_blueprint(budgets_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(uploads_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(rules_bp)
    app.register_blueprint(status_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    
    # Authentication Middleware
    @app.before_request
    def check_authentication():
        """Check if user is authenticated before processing API requests"""
        # Skip auth check for auth endpoints, static files, and login page
        public_paths = ['/api/auth/', '/api/users/init', '/static/', '/']
        
        if any(request.path.startswith(p) or request.path == p for p in public_paths):
            return
        
        # All other API routes require authentication
        if request.path.startswith('/api'):
            if 'user_id' not in session:
                return jsonify({
                    'error': 'Authentication required',
                    'authenticated': False
                }), 401
            
            # Check if user can modify data (superuser only for write operations)
            if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
                from app.models.user import User
                user = User.query.get(session['user_id'])
                if not user or not user.is_superuser():
                    return jsonify({
                        'error': 'Permission denied. Read-only access for standard users.',
                        'authorized': False
                    }), 403
    
    # API Status Middleware
    @app.before_request
    def check_api_status():
        """Check if API is enabled before processing requests"""
        from app.models.api_status import ApiStatus
        
        # Always allow status endpoint and frontend routes
        if request.path.startswith('/api/status') or not request.path.startswith('/api'):
            return
        
        status = ApiStatus.query.first()
        if status and not status.is_enabled:
            return jsonify({
                'error': 'API is currently offline for maintenance',
                'status': 'offline'
            }), 503
    
    # Frontend routes
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/<path:filename>')
    def serve_static(filename):
        return send_from_directory(app.static_folder, filename)
    
    # Create tables and initialize default admin
    with app.app_context():
        db.create_all()
        # Create default admin user
        from app.models.user import User
        User.create_default_admin()
    
    return app
