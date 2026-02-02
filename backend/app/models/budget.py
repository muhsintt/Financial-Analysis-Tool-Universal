from app import db
from datetime import datetime

class Budget(db.Model):
    __tablename__ = 'budgets'
    
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    period = db.Column(db.String(20), nullable=False)  # 'daily', 'weekly', 'monthly', 'annual'
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer)  # 1-12 for monthly budgets
    week = db.Column(db.Integer)  # ISO week number for weekly budgets
    for_excluded = db.Column(db.Boolean, default=False)  # Budget for excluded expenses
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Budget {self.category.name if self.category else "Unknown"} - {self.amount}>'
    
    def to_dict(self):
        # Get full category name (with parent if subcategory)
        if self.category:
            category_name = self.category.full_name if hasattr(self.category, 'full_name') else self.category.name
            category_color = self.category.color
            parent_id = self.category.parent_id
        else:
            category_name = None
            category_color = None
            parent_id = None
            
        return {
            'id': self.id,
            'category_id': self.category_id,
            'category_name': category_name,
            'category_color': category_color,
            'parent_id': parent_id,
            'amount': self.amount,
            'period': self.period,
            'year': self.year,
            'month': self.month,
            'week': self.week,
            'for_excluded': self.for_excluded,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
