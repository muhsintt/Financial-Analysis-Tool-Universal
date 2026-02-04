"""
Upload model for tracking file uploads and their related transactions.
"""

from app import db
from datetime import datetime

class Upload(db.Model):
    """Model to track file uploads"""
    __tablename__ = 'uploads'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, default=0)  # Size in bytes
    file_type = db.Column(db.String(50))  # csv, xlsx, xls
    transaction_count = db.Column(db.Integer, default=0)
    uploaded_by = db.Column(db.String(100), default='system')
    status = db.Column(db.String(50), default='completed')  # pending, completed, failed
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to transactions
    transactions = db.relationship('Transaction', backref='upload', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'file_size_formatted': self.format_file_size(),
            'file_type': self.file_type,
            'transaction_count': self.transaction_count,
            'uploaded_by': self.uploaded_by,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def format_file_size(self):
        """Format file size in human-readable format"""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} MB"
    
    def update_transaction_count(self):
        """Update the transaction count for this upload"""
        self.transaction_count = self.transactions.count()
        db.session.commit()
