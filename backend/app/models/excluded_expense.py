from app import db
from datetime import datetime

class ExcludedExpense(db.Model):
    __tablename__ = 'excluded_expenses'
    
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=False)
    reason = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ExcludedExpense {self.transaction_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'reason': self.reason,
            'created_at': self.created_at.isoformat()
        }
