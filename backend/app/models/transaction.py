from app import db
from datetime import datetime

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'income' or 'expense'
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    is_excluded = db.Column(db.Boolean, default=False)
    source = db.Column(db.String(100), default='manual')  # 'manual' or 'upload'
    upload_id = db.Column(db.Integer, db.ForeignKey('uploads.id'), nullable=True)  # Link to upload
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # User isolation
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='transactions')
    
    def __repr__(self):
        return f'<Transaction {self.description} - {self.amount}>'
    
    def to_dict(self):
        # Get full category name (with parent if subcategory)
        category_name = None
        if self.category:
            category_name = self.category.full_name if hasattr(self.category, 'full_name') else self.category.name
        
        return {
            'id': self.id,
            'description': self.description,
            'amount': self.amount,
            'type': self.type,
            'date': self.date.isoformat(),
            'category_id': self.category_id,
            'category_name': category_name,
            'is_excluded': self.is_excluded,
            'source': self.source,
            'upload_id': self.upload_id,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
