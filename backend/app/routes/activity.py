"""
Activity Log routes for viewing and managing activity history.
"""

from flask import Blueprint, request, jsonify, send_file, session
from app import db
from app.models.activity_log import ActivityLog
from app.models.log_settings import LogSettings
from app.routes.auth import write_required, superuser_required
from datetime import datetime, timedelta
import csv
import json
import io
import os

bp = Blueprint('activity', __name__, url_prefix='/api/activity')

@bp.route('/', methods=['GET'])
def get_activities():
    """Get activity logs with optional filters"""
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    # Filters
    category = request.args.get('category')
    action = request.args.get('action')
    username = request.args.get('username')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = ActivityLog.query
    
    if category:
        query = query.filter(ActivityLog.category == category)
    if action:
        query = query.filter(ActivityLog.action == action)
    if username:
        query = query.filter(ActivityLog.username == username)
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(ActivityLog.created_at >= start)
        except ValueError:
            pass
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(ActivityLog.created_at < end)
        except ValueError:
            pass
    
    # Order by most recent
    query = query.order_by(ActivityLog.created_at.desc())
    
    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'activities': [a.to_dict() for a in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })

@bp.route('/recent', methods=['GET'])
def get_recent_activities():
    """Get recent activities (last 24 hours)"""
    limit = request.args.get('limit', 20, type=int)
    
    since = datetime.utcnow() - timedelta(hours=24)
    activities = ActivityLog.query.filter(
        ActivityLog.created_at >= since
    ).order_by(ActivityLog.created_at.desc()).limit(limit).all()
    
    return jsonify([a.to_dict() for a in activities])

@bp.route('/categories', methods=['GET'])
def get_categories():
    """Get distinct activity categories"""
    categories = db.session.query(ActivityLog.category).distinct().all()
    return jsonify([c[0] for c in categories if c[0]])

@bp.route('/actions', methods=['GET'])
def get_actions():
    """Get distinct activity actions"""
    actions = db.session.query(ActivityLog.action).distinct().all()
    return jsonify([a[0] for a in actions if a[0]])

@bp.route('/users', methods=['GET'])
def get_users():
    """Get distinct usernames from activities"""
    users = db.session.query(ActivityLog.username).distinct().all()
    return jsonify([u[0] for u in users if u[0]])

@bp.route('/stats', methods=['GET'])
def get_stats():
    """Get activity statistics"""
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today - timedelta(days=7)
    
    # Count activities by category for last 7 days
    from sqlalchemy import func
    
    category_counts = db.session.query(
        ActivityLog.category,
        func.count(ActivityLog.id)
    ).filter(
        ActivityLog.created_at >= week_ago
    ).group_by(ActivityLog.category).all()
    
    action_counts = db.session.query(
        ActivityLog.action,
        func.count(ActivityLog.id)
    ).filter(
        ActivityLog.created_at >= week_ago
    ).group_by(ActivityLog.action).all()
    
    total_today = ActivityLog.query.filter(ActivityLog.created_at >= today).count()
    total_week = ActivityLog.query.filter(ActivityLog.created_at >= week_ago).count()
    
    return jsonify({
        'total_today': total_today,
        'total_week': total_week,
        'by_category': {c: count for c, count in category_counts},
        'by_action': {a: count for a, count in action_counts}
    })

@bp.route('/clear', methods=['DELETE'])
@superuser_required
def clear_old_activities():
    """Clear activities older than specified days (default 90)"""
    days = request.args.get('days', 90, type=int)
    
    if days < 7:
        return jsonify({'error': 'Cannot clear activities less than 7 days old'}), 400
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    deleted = ActivityLog.query.filter(ActivityLog.created_at < cutoff).delete()
    db.session.commit()
    
    return jsonify({
        'message': f'Deleted {deleted} activity logs older than {days} days',
        'deleted_count': deleted
    })

# ==================== Log Settings Endpoints ==================== #

@bp.route('/settings', methods=['GET'])
def get_log_settings():
    """Get current log settings"""
    settings = LogSettings.get_settings()
    return jsonify(settings.to_dict())

@bp.route('/settings', methods=['PUT'])
@superuser_required
def update_log_settings():
    """Update log settings"""
    data = request.get_json()
    settings = LogSettings.get_settings()
    
    # Update master toggle
    if 'logging_enabled' in data:
        settings.logging_enabled = bool(data['logging_enabled'])
    
    # Update enabled categories
    if 'enabled_categories' in data:
        settings.set_enabled_categories(data['enabled_categories'])
    
    # Update enabled actions
    if 'enabled_actions' in data:
        settings.set_enabled_actions(data['enabled_actions'])
    
    # Update retention settings
    if 'retention_days' in data:
        days = int(data['retention_days'])
        if days < 1:
            return jsonify({'error': 'Retention days must be at least 1'}), 400
        settings.retention_days = days
    
    if 'auto_cleanup' in data:
        settings.auto_cleanup = bool(data['auto_cleanup'])
    
    # Update export format
    if 'export_format' in data:
        if data['export_format'] not in ['csv', 'json', 'txt']:
            return jsonify({'error': 'Export format must be csv, json, or txt'}), 400
        settings.export_format = data['export_format']
    
    # Update file logging settings
    if 'file_logging_enabled' in data:
        settings.file_logging_enabled = bool(data['file_logging_enabled'])
    
    if 'log_destination_type' in data:
        if data['log_destination_type'] not in ['local', 'smb', 'nfs']:
            return jsonify({'error': 'Destination type must be local, smb, or nfs'}), 400
        settings.log_destination_type = data['log_destination_type']
    
    if 'log_path' in data:
        settings.log_path = data['log_path']
    
    # Update SMB settings
    if 'smb_server' in data:
        settings.smb_server = data['smb_server']
    if 'smb_share' in data:
        settings.smb_share = data['smb_share']
    if 'smb_username' in data:
        settings.smb_username = data['smb_username']
    if 'smb_password' in data:
        settings.smb_password = data['smb_password']
    if 'smb_domain' in data:
        settings.smb_domain = data['smb_domain']
    
    # Update NFS settings
    if 'nfs_server' in data:
        settings.nfs_server = data['nfs_server']
    if 'nfs_export' in data:
        settings.nfs_export = data['nfs_export']
    if 'nfs_mount_options' in data:
        settings.nfs_mount_options = data['nfs_mount_options']
    
    settings.updated_by = session.get('username', 'system')
    db.session.commit()
    
    return jsonify({
        'message': 'Log settings updated successfully',
        'settings': settings.to_dict()
    })

@bp.route('/export', methods=['GET'])
def export_logs():
    """Export activity logs to file"""
    settings = LogSettings.get_settings()
    export_format = request.args.get('format', settings.export_format)
    
    # Get filter parameters
    category = request.args.get('category')
    action = request.args.get('action')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = ActivityLog.query
    
    if category:
        query = query.filter(ActivityLog.category == category)
    if action:
        query = query.filter(ActivityLog.action == action)
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(ActivityLog.created_at >= start)
        except ValueError:
            pass
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(ActivityLog.created_at < end)
        except ValueError:
            pass
    
    logs = query.order_by(ActivityLog.created_at.desc()).all()
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if export_format == 'csv':
        return export_csv(logs, timestamp)
    elif export_format == 'json':
        return export_json(logs, timestamp)
    else:  # txt
        return export_txt(logs, timestamp)

def export_csv(logs, timestamp):
    """Export logs as CSV"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['Timestamp', 'User', 'Action', 'Category', 'Description', 'IP Address', 'Details'])
    
    # Data
    for log in logs:
        writer.writerow([
            log.created_at.isoformat() if log.created_at else '',
            log.username or '',
            log.action or '',
            log.category or '',
            log.description or '',
            log.ip_address or '',
            log.details or ''
        ])
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'activity_logs_{timestamp}.csv'
    )

def export_json(logs, timestamp):
    """Export logs as JSON"""
    data = {
        'exported_at': datetime.utcnow().isoformat(),
        'total_records': len(logs),
        'logs': [log.to_dict() for log in logs]
    }
    
    output = json.dumps(data, indent=2, default=str)
    
    return send_file(
        io.BytesIO(output.encode('utf-8')),
        mimetype='application/json',
        as_attachment=True,
        download_name=f'activity_logs_{timestamp}.json'
    )

def export_txt(logs, timestamp):
    """Export logs as plain text"""
    lines = [
        f"Activity Logs Export",
        f"Exported: {datetime.utcnow().isoformat()}",
        f"Total Records: {len(logs)}",
        "=" * 80,
        ""
    ]
    
    for log in logs:
        lines.append(f"[{log.created_at.isoformat() if log.created_at else 'N/A'}]")
        lines.append(f"  User: {log.username or 'N/A'}")
        lines.append(f"  Action: {log.action or 'N/A'}")
        lines.append(f"  Category: {log.category or 'N/A'}")
        lines.append(f"  Description: {log.description or 'N/A'}")
        lines.append(f"  IP Address: {log.ip_address or 'N/A'}")
        if log.details:
            lines.append(f"  Details: {log.details}")
        lines.append("-" * 40)
    
    output = '\n'.join(lines)
    
    return send_file(
        io.BytesIO(output.encode('utf-8')),
        mimetype='text/plain',
        as_attachment=True,
        download_name=f'activity_logs_{timestamp}.txt'
    )

@bp.route('/save-to-file', methods=['POST'])
@superuser_required
def save_logs_to_file():
    """Save logs to configured file destination"""
    settings = LogSettings.get_settings()
    
    if not settings.file_logging_enabled:
        return jsonify({'error': 'File logging is not enabled'}), 400
    
    if not settings.log_path:
        return jsonify({'error': 'Log path is not configured'}), 400
    
    # Get logs to export
    logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).all()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    try:
        if settings.log_destination_type == 'local':
            return save_to_local(logs, settings, timestamp)
        elif settings.log_destination_type == 'smb':
            return save_to_smb(logs, settings, timestamp)
        elif settings.log_destination_type == 'nfs':
            return save_to_nfs(logs, settings, timestamp)
        else:
            return jsonify({'error': 'Invalid destination type'}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to save logs: {str(e)}'}), 500

def save_to_local(logs, settings, timestamp):
    """Save logs to local file system"""
    try:
        # Ensure directory exists
        os.makedirs(settings.log_path, exist_ok=True)
        
        filename = f'activity_logs_{timestamp}.{settings.export_format}'
        filepath = os.path.join(settings.log_path, filename)
        
        if settings.export_format == 'csv':
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Timestamp', 'User', 'Action', 'Category', 'Description', 'IP Address', 'Details'])
                for log in logs:
                    writer.writerow([
                        log.created_at.isoformat() if log.created_at else '',
                        log.username or '', log.action or '', log.category or '',
                        log.description or '', log.ip_address or '', log.details or ''
                    ])
        elif settings.export_format == 'json':
            with open(filepath, 'w', encoding='utf-8') as f:
                data = {'exported_at': datetime.utcnow().isoformat(), 'total_records': len(logs),
                        'logs': [log.to_dict() for log in logs]}
                json.dump(data, f, indent=2, default=str)
        else:  # txt
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Activity Logs Export\nExported: {datetime.utcnow().isoformat()}\n")
                f.write(f"Total Records: {len(logs)}\n{'=' * 80}\n\n")
                for log in logs:
                    f.write(f"[{log.created_at.isoformat() if log.created_at else 'N/A'}]\n")
                    f.write(f"  User: {log.username}\n  Action: {log.action}\n")
                    f.write(f"  Category: {log.category}\n  Description: {log.description}\n")
                    f.write(f"  IP: {log.ip_address}\n{'-' * 40}\n")
        
        return jsonify({
            'message': f'Logs saved successfully to {filepath}',
            'filepath': filepath,
            'records': len(logs)
        })
    except Exception as e:
        return jsonify({'error': f'Failed to save to local: {str(e)}'}), 500

def save_to_smb(logs, settings, timestamp):
    """Save logs to SMB share"""
    # Note: In production, you would use smbclient or pysmb library
    # For now, we return instructions for manual setup
    return jsonify({
        'message': 'SMB export requires additional configuration',
        'instructions': f'Mount SMB share //{settings.smb_server}/{settings.smb_share} and use local export',
        'smb_path': f'//{settings.smb_server}/{settings.smb_share}',
        'records': len(logs)
    })

def save_to_nfs(logs, settings, timestamp):
    """Save logs to NFS share"""
    # Note: NFS should be mounted on the system level
    # We attempt to write to the mount point if it exists
    nfs_path = settings.log_path if settings.log_path else f'/mnt/{settings.nfs_export}'
    
    if os.path.exists(nfs_path) and os.path.isdir(nfs_path):
        settings.log_path = nfs_path
        return save_to_local(logs, settings, timestamp)
    
    return jsonify({
        'message': 'NFS export requires mount configuration',
        'instructions': f'Mount NFS export {settings.nfs_server}:{settings.nfs_export} to {nfs_path}',
        'nfs_path': f'{settings.nfs_server}:{settings.nfs_export}',
        'records': len(logs)
    })

@bp.route('/test-destination', methods=['POST'])
@superuser_required
def test_destination():
    """Test log destination connectivity"""
    settings = LogSettings.get_settings()
    
    if settings.log_destination_type == 'local':
        try:
            if not settings.log_path:
                return jsonify({'success': False, 'error': 'Log path not configured'})
            
            os.makedirs(settings.log_path, exist_ok=True)
            test_file = os.path.join(settings.log_path, '.test_write')
            
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            
            return jsonify({'success': True, 'message': f'Successfully connected to {settings.log_path}'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    elif settings.log_destination_type == 'smb':
        return jsonify({
            'success': False, 
            'message': 'SMB connection test not implemented. Please verify mount manually.',
            'path': f'//{settings.smb_server}/{settings.smb_share}'
        })
    
    elif settings.log_destination_type == 'nfs':
        nfs_path = settings.log_path if settings.log_path else f'/mnt/{settings.nfs_export}'
        if os.path.exists(nfs_path) and os.path.isdir(nfs_path):
            return jsonify({'success': True, 'message': f'NFS mount accessible at {nfs_path}'})
        return jsonify({
            'success': False,
            'message': f'NFS mount not found at {nfs_path}. Please mount {settings.nfs_server}:{settings.nfs_export}'
        })
    
    return jsonify({'success': False, 'error': 'Invalid destination type'})
