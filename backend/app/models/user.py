from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    
    # Role options
    ROLE_SUPERUSER = 'superuser'
    ROLE_STANDARD = 'standard'
    ROLE_VIEWER = 'viewer'
    ROLE_CHOICES = [ROLE_SUPERUSER, ROLE_STANDARD, ROLE_VIEWER]
    
    # Calendar preference options
    CALENDAR_BOTH = 'both'
    CALENDAR_GREGORIAN = 'gregorian'
    CALENDAR_BADI = 'badi'
    CALENDAR_CHOICES = [CALENDAR_BOTH, CALENDAR_GREGORIAN, CALENDAR_BADI]
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='standard')  # 'superuser', 'standard', or 'viewer'
    is_default = db.Column(db.Boolean, default=False)  # True for the default admin user
    calendar_preference = db.Column(db.String(20), nullable=False, default='both')  # 'both', 'gregorian', or 'badi'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        """Hash and set the password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches the hash"""
        return check_password_hash(self.password_hash, password)
    
    def is_superuser(self):
        """Check if user has superuser role"""
        return self.role == 'superuser'
    
    def is_viewer(self):
        """Check if user has viewer (read-only) role"""
        return self.role == 'viewer'
    
    def can_write(self):
        """Check if user can write/modify data (superuser and standard users)"""
        return self.role in ['superuser', 'standard']
    
    def can_modify(self):
        """Check if user can modify data (only superusers)"""
        return self.role == 'superuser'
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'is_default': self.is_default,
            'calendar_preference': self.calendar_preference or 'both',
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @staticmethod
    def create_default_admin():
        """Create the default admin user if it doesn't exist"""
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                role='superuser',
                is_default=True,
                calendar_preference='both'
            )
            admin.set_password('money')
            db.session.add(admin)
            db.session.commit()
            return admin
        return None
