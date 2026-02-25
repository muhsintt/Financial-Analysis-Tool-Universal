from app import db
from datetime import datetime

class CategorizationRule(db.Model):
    __tablename__ = 'categorization_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    keywords = db.Column(db.String(500), nullable=False)  # Comma-separated keywords
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    priority = db.Column(db.Integer, default=0)  # Higher priority = checked first
    is_active = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # User isolation - nullable for system rules
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='categorization_rules')
    category = db.relationship('Category', backref='categorization_rules')
    
    def __repr__(self):
        return f'<CategorizationRule {self.name}>'
    
    def get_keywords_list(self):
        """Return keywords as a list"""
        return [kw.strip().lower() for kw in self.keywords.split(',') if kw.strip()]
    
    def matches(self, description):
        """Check if any keyword matches the description"""
        desc_lower = description.lower()
        return any(keyword in desc_lower for keyword in self.get_keywords_list())
    
    def to_dict(self):
        # Get full category name (with parent if subcategory)
        if self.category:
            category_name = self.category.full_name if hasattr(self.category, 'full_name') else self.category.name
            parent_id = self.category.parent_id
        else:
            category_name = None
            parent_id = None
            
        return {
            'id': self.id,
            'name': self.name,
            'keywords': self.keywords,
            'category_id': self.category_id,
            'category_name': category_name,
            'parent_id': parent_id,
            'priority': self.priority,
            'is_active': self.is_active,
            'is_system': self.user_id is None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
