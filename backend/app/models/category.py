from app import db
from datetime import datetime

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'income' or 'expense'
    color = db.Column(db.String(7), default='#3498db')
    icon = db.Column(db.String(50), default='folder')
    is_default = db.Column(db.Boolean, default=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # NULL for system categories
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Self-referential relationship for subcategories
    subcategories = db.relationship('Category', backref=db.backref('parent', remote_side=[id]), lazy=True)
    
    # Relationships
    user = db.relationship('User', backref='categories')
    transactions = db.relationship('Transaction', backref='category', lazy=True, cascade='all, delete-orphan')
    budgets = db.relationship('Budget', backref='category', lazy=True, cascade='all, delete-orphan')
    
    # Unique constraint on name + parent_id to allow same name in different parent categories
    __table_args__ = (
        db.UniqueConstraint('name', 'parent_id', name='uq_category_name_parent'),
    )
    
    def __repr__(self):
        return f'<Category {self.name}>'
    
    def to_dict(self, include_subcategories=False):
        result = {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'color': self.color,
            'icon': self.icon,
            'is_default': self.is_default,
            'parent_id': self.parent_id,
            'parent_name': self.parent.name if self.parent else None,
            'created_at': self.created_at.isoformat()
        }
        if include_subcategories:
            result['subcategories'] = [sub.to_dict() for sub in self.subcategories]
        return result
    
    @property
    def full_name(self):
        """Get full category path (e.g., 'Groceries > Organic')"""
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name
