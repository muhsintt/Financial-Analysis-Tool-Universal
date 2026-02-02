import os
from flask import Flask, render_template, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

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
    
    # Ensure directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    
    # Register blueprints
    from app.routes.transactions import transactions_bp
    from app.routes.budgets import budgets_bp
    from app.routes.reports import reports_bp
    from app.routes.uploads import uploads_bp
    from app.routes.categories import categories_bp
    from app.routes.rules import rules_bp
    
    app.register_blueprint(transactions_bp)
    app.register_blueprint(budgets_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(uploads_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(rules_bp)
    
    # Frontend routes
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/<path:filename>')
    def serve_static(filename):
        return send_from_directory(app.static_folder, filename)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app
