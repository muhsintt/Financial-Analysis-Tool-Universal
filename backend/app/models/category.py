from app import db
from datetime import datetime

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'income' or 'expense'
    color = db.Column(db.String(7), default='#3498db')
    icon = db.Column(db.String(50), default='folder')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    transactions = db.relationship('Transaction', backref='category', lazy=True, cascade='all, delete-orphan')
    budgets = db.relationship('Budget', backref='category', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Category {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'color': self.color,
            'icon': self.icon,
            'created_at': self.created_at.isoformat()
        }
