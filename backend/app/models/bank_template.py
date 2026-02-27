"""
BankTemplate model for storing bank CSV statement column-mapping templates.
"""

from app import db
from datetime import datetime
import json


class BankTemplate(db.Model):
    __tablename__ = 'bank_templates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    # JSON array of all column headers present in this bank's CSV
    headers = db.Column(db.Text, nullable=False)
    # JSON dict: {date_col, description_col, amount_col, category_col (optional)}
    column_mapping = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='bank_templates')

    def get_headers(self):
        return json.loads(self.headers) if self.headers else []

    def get_mapping(self):
        return json.loads(self.column_mapping) if self.column_mapping else {}

    def match_score(self, file_headers):
        """
        Return a 0-1 score for how well `file_headers` match this template.
        Score = (# template headers found in file) / (# template headers).
        """
        template_set = set(h.lower().strip() for h in self.get_headers())
        file_set = set(h.lower().strip() for h in file_headers)
        if not template_set:
            return 0.0
        return len(template_set & file_set) / len(template_set)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'headers': self.get_headers(),
            'column_mapping': self.get_mapping(),
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
