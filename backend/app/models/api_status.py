from app import db
from datetime import datetime

class ApiStatus(db.Model):
    __tablename__ = 'api_status'
    
    id = db.Column(db.Integer, primary_key=True)
    is_enabled = db.Column(db.Boolean, default=True)
    last_toggled = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_toggled_by = db.Column(db.String(255), default='system')
    
    def __repr__(self):
        return f'<ApiStatus enabled={self.is_enabled}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'is_enabled': self.is_enabled,
            'status': 'Online' if self.is_enabled else 'Offline',
            'last_toggled': self.last_toggled.isoformat() if self.last_toggled else None,
            'last_toggled_by': self.last_toggled_by
        }
