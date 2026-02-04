"""
Log Settings model for configuring activity logging behavior.
"""

from app import db
from datetime import datetime
import json

class LogSettings(db.Model):
    """Model to store logging configuration"""
    __tablename__ = 'log_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Master toggle
    logging_enabled = db.Column(db.Boolean, default=True)
    
    # Category toggles (stored as JSON)
    enabled_categories = db.Column(db.Text, default='["auth","transaction","upload","user","settings","system"]')
    
    # Action toggles (stored as JSON)
    enabled_actions = db.Column(db.Text, default='["login","logout","upload","download","create","update","delete","bulk_delete","toggle","password_change"]')
    
    # Retention settings (in days)
    retention_days = db.Column(db.Integer, default=90)
    auto_cleanup = db.Column(db.Boolean, default=True)
    
    # Export settings
    export_format = db.Column(db.String(20), default='csv')  # csv, json, txt
    
    # File logging settings
    file_logging_enabled = db.Column(db.Boolean, default=False)
    log_destination_type = db.Column(db.String(20), default='local')  # local, smb, nfs
    log_path = db.Column(db.String(500), default='')
    
    # SMB settings
    smb_server = db.Column(db.String(255), default='')
    smb_share = db.Column(db.String(255), default='')
    smb_username = db.Column(db.String(100), default='')
    smb_password = db.Column(db.String(255), default='')  # Should be encrypted in production
    smb_domain = db.Column(db.String(100), default='')
    
    # NFS settings
    nfs_server = db.Column(db.String(255), default='')
    nfs_export = db.Column(db.String(255), default='')
    nfs_mount_options = db.Column(db.String(255), default='')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.String(100), default='system')
    
    # Available categories
    ALL_CATEGORIES = ['auth', 'transaction', 'upload', 'user', 'settings', 'system', 'category', 'budget', 'rule']
    
    # Available actions
    ALL_ACTIONS = ['login', 'logout', 'upload', 'download', 'create', 'update', 'delete', 'bulk_delete', 'toggle', 'password_change', 'import', 'export']
    
    def get_enabled_categories(self):
        """Get list of enabled categories"""
        try:
            return json.loads(self.enabled_categories) if self.enabled_categories else []
        except:
            return self.ALL_CATEGORIES
    
    def set_enabled_categories(self, categories):
        """Set enabled categories"""
        self.enabled_categories = json.dumps(categories)
    
    def get_enabled_actions(self):
        """Get list of enabled actions"""
        try:
            return json.loads(self.enabled_actions) if self.enabled_actions else []
        except:
            return self.ALL_ACTIONS
    
    def set_enabled_actions(self, actions):
        """Set enabled actions"""
        self.enabled_actions = json.dumps(actions)
    
    def is_category_enabled(self, category):
        """Check if a category is enabled for logging"""
        if not self.logging_enabled:
            return False
        return category in self.get_enabled_categories()
    
    def is_action_enabled(self, action):
        """Check if an action is enabled for logging"""
        if not self.logging_enabled:
            return False
        return action in self.get_enabled_actions()
    
    def should_log(self, action, category):
        """Check if this action/category combination should be logged"""
        if not self.logging_enabled:
            return False
        return self.is_action_enabled(action) and self.is_category_enabled(category)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'logging_enabled': self.logging_enabled,
            'enabled_categories': self.get_enabled_categories(),
            'enabled_actions': self.get_enabled_actions(),
            'all_categories': self.ALL_CATEGORIES,
            'all_actions': self.ALL_ACTIONS,
            'retention_days': self.retention_days,
            'auto_cleanup': self.auto_cleanup,
            'export_format': self.export_format,
            'file_logging_enabled': self.file_logging_enabled,
            'log_destination_type': self.log_destination_type,
            'log_path': self.log_path,
            'smb_server': self.smb_server,
            'smb_share': self.smb_share,
            'smb_username': self.smb_username,
            'smb_domain': self.smb_domain,
            'nfs_server': self.nfs_server,
            'nfs_export': self.nfs_export,
            'nfs_mount_options': self.nfs_mount_options,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'updated_by': self.updated_by
        }
    
    @classmethod
    def get_settings(cls):
        """Get or create the log settings singleton"""
        settings = cls.query.first()
        if not settings:
            settings = cls()
            db.session.add(settings)
            db.session.commit()
        return settings
