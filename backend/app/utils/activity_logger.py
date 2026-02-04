"""
Activity Logger utility for tracking user actions.
"""

from flask import request, session
import json

def log_activity(action, category, description, details=None):
    """
    Log an activity with current user context.
    
    Args:
        action: The type of action (e.g., 'create', 'delete', 'update')
        category: The category of the action (e.g., 'transaction', 'user', 'settings')
        description: Human-readable description of the action
        details: Optional dict with additional details (will be JSON serialized)
    """
    from app.models.activity_log import ActivityLog
    
    # Get user info from session
    user_id = session.get('user_id')
    username = session.get('username', 'system')
    
    # Get IP address
    ip_address = request.remote_addr if request else None
    
    # Serialize details to JSON if provided
    details_json = json.dumps(details) if details else None
    
    return ActivityLog.log(
        action=action,
        category=category,
        description=description,
        details=details_json,
        user_id=user_id,
        username=username,
        ip_address=ip_address
    )
