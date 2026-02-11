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
    # Store database in data directory for persistence across container rebuilds
    data_dir = os.path.join(backend_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)  # Ensure data directory exists
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(data_dir, "expense_tracker.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file upload
    app.config['UPLOAD_FOLDER'] = os.path.join(backend_dir, 'uploads')
    
    # Session configuration
    # Use consistent secret key based on environment or generate one that persists
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        # Generate consistent secret key based on data directory path
        # This ensures the same key is used across app restarts
        import hashlib
        secret_source = f"{data_dir}_financial_analysis_tool_secret"
        secret_key = hashlib.sha256(secret_source.encode()).hexdigest()
    
    app.config['SECRET_KEY'] = secret_key
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
    from app.routes.calendar import bp as calendar_bp
    from app.routes.activity import bp as activity_bp
    
    app.register_blueprint(transactions_bp)
    app.register_blueprint(budgets_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(uploads_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(rules_bp)
    app.register_blueprint(status_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(calendar_bp)
    app.register_blueprint(activity_bp)
    
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
    
    # Create tables and initialize defaults
    with app.app_context():
        db.create_all()
        # Create default admin user
        from app.models.user import User
        User.create_default_admin()
        # Initialize default categorization rules
        _initialize_default_rules()
    
    return app


def _initialize_default_rules():
    """Create default categorization rules if none exist"""
    from app.models.categorization_rule import CategorizationRule
    from app.models.category import Category
    
    # Only initialize if no rules exist
    if CategorizationRule.query.count() > 0:
        return
    
    # Define categories
    category_list = [
        ('Groceries', 'expense', '#27ae60'),
        ('Restaurants & Dining', 'expense', '#e74c3c'),
        ('Transportation', 'expense', '#3498db'),
        ('Utilities', 'expense', '#9b59b6'),
        ('Entertainment/Subscriptions', 'expense', '#e67e22'),
        ('Shopping/Retail', 'expense', '#1abc9c'),
        ('Health & Pharmacy', 'expense', '#2ecc71'),
        ('Housing', 'expense', '#34495e'),
        ('Income', 'income', '#27ae60'),
    ]
    
    # Create categories if they don't exist
    categories = {}
    for name, cat_type, color in category_list:
        cat = Category.query.filter_by(name=name).first()
        if not cat:
            cat = Category(name=name, type=cat_type, color=color, icon='folder')
            db.session.add(cat)
            db.session.flush()
        categories[name] = cat.id
    
    # Define default rules
    default_rules = [
        ('Grocery Stores', 'whole foods, safeway, trader joes, kroger, publix, instacart, sprouts', 'Groceries', 10),
        ('Supermarkets', 'walmart, target, costco, sam\'s club, market basket', 'Groceries', 9),
        ('Fast Food', 'mcd, burger king, subway, taco bell, popeyes, chick-fil, chipotle', 'Restaurants & Dining', 10),
        ('Restaurants', 'restaurant, cafe, pizzeria, dining', 'Restaurants & Dining', 8),
        ('Ride Sharing', 'uber, lyft, taxify', 'Transportation', 10),
        ('Gas & Fuel', 'shell, chevron, exxon, bp, speedway, sunoco, fuel', 'Transportation', 10),
        ('Parking & Transit', 'parking, transit, amtrak, metro', 'Transportation', 8),
        ('Internet & Phone', 'comcast, verizon, at&t, internet, phone bill, broadband', 'Utilities', 10),
        ('Utilities', 'electric, water, gas, utility, city of', 'Utilities', 9),
        ('Streaming Services', 'netflix, hulu, disney, prime video, spotify, youtube', 'Entertainment/Subscriptions', 10),
        ('Entertainment', 'movie, concert, theater, steam, playstation, xbox, nintendo', 'Entertainment/Subscriptions', 8),
        ('Online Retailers', 'amazon, ebay, etsy', 'Shopping/Retail', 10),
        ('Electronics', 'best buy, apple store, electronics', 'Shopping/Retail', 9),
        ('Pharmacy', 'cvs, walgreens, pharmacy, drugstore', 'Health & Pharmacy', 10),
        ('Healthcare', 'doctor, hospital, medical, dental, clinic, health', 'Health & Pharmacy', 8),
        ('Rent & Mortgage', 'rent, mortgage, landlord, lease', 'Housing', 10),
        ('Salary', 'salary, paycheck, payroll, wages', 'Income', 10),
    ]
    
    # Create rules
    for name, keywords, category_name, priority in default_rules:
        rule = CategorizationRule(
            name=name,
            keywords=keywords,
            category_id=categories[category_name],
            priority=priority,
            is_active=True
        )
        db.session.add(rule)
    
    db.session.commit()
    print(f"✓ Initialized {len(default_rules)} default categorization rules")
