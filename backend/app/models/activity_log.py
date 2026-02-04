"""
Activity Log model for tracking user actions and system events.
"""

from app import db
from datetime import datetime

class ActivityLog(db.Model):
    """Model to track user activities and system events"""
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(100), nullable=False)  # e.g., 'upload', 'delete', 'edit', 'login'
    category = db.Column(db.String(50), nullable=False)  # e.g., 'transaction', 'user', 'upload', 'settings'
    description = db.Column(db.Text, nullable=False)
    details = db.Column(db.Text)  # JSON string for additional details
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    username = db.Column(db.String(100), default='system')
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationship to user
    user = db.relationship('User', backref='activities', lazy='select')
    
    # Action type constants
    ACTION_LOGIN = 'login'
    ACTION_LOGOUT = 'logout'
    ACTION_UPLOAD = 'upload'
    ACTION_DOWNLOAD = 'download'
    ACTION_CREATE = 'create'
    ACTION_UPDATE = 'update'
    ACTION_DELETE = 'delete'
    ACTION_BULK_DELETE = 'bulk_delete'
    ACTION_TOGGLE = 'toggle'
    ACTION_IMPORT = 'import'
    ACTION_EXPORT = 'export'
    ACTION_PASSWORD_CHANGE = 'password_change'
    
    # Category constants
    CATEGORY_AUTH = 'auth'
    CATEGORY_TRANSACTION = 'transaction'
    CATEGORY_UPLOAD = 'upload'
    CATEGORY_USER = 'user'
    CATEGORY_SETTINGS = 'settings'
    CATEGORY_CATEGORY = 'category'
    CATEGORY_BUDGET = 'budget'
    CATEGORY_RULE = 'rule'
    CATEGORY_SYSTEM = 'system'
    
    def to_dict(self):
        return {
            'id': self.id,
            'action': self.action,
            'category': self.category,
            'description': self.description,
            'details': self.details,
            'user_id': self.user_id,
            'username': self.username,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'time_ago': self.get_time_ago()
        }
    
    def get_time_ago(self):
        """Get human-readable time difference"""
        if not self.created_at:
            return 'Unknown'
        
        now = datetime.utcnow()
        diff = now - self.created_at
        
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return 'Just now'
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f'{minutes} minute{"s" if minutes > 1 else ""} ago'
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f'{hours} hour{"s" if hours > 1 else ""} ago'
        elif seconds < 604800:
            days = int(seconds / 86400)
            return f'{days} day{"s" if days > 1 else ""} ago'
        else:
            return self.created_at.strftime('%Y-%m-%d %H:%M')
    
    @classmethod
    def log(cls, action, category, description, details=None, user_id=None, username=None, ip_address=None):
        """Create a new activity log entry"""
        log_entry = cls(
            action=action,
            category=category,
            description=description,
            details=details,
            user_id=user_id,
            username=username or 'system',
            ip_address=ip_address
        )
        db.session.add(log_entry)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
        return log_entry
