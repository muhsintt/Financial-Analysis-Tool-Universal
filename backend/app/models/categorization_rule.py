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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
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
        return {
            'id': self.id,
            'name': self.name,
            'keywords': self.keywords,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'priority': self.priority,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
