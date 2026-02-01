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
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Transaction {self.description} - {self.amount}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'description': self.description,
            'amount': self.amount,
            'type': self.type,
            'date': self.date.isoformat(),
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'is_excluded': self.is_excluded,
            'source': self.source,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
