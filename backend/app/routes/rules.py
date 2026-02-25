from flask import Blueprint, request, jsonify, session
from app import db
from app.models.categorization_rule import CategorizationRule
from app.models.category import Category
from app.models.transaction import Transaction
from app.routes.auth import write_required, login_required

rules_bp = Blueprint('rules', __name__, url_prefix='/api/rules')

@rules_bp.route('/apply', methods=['POST'])
@write_required
def apply_rules():
    """Apply all active rules to existing transactions"""
    current_user_id = session['user_id']
    
    # Get all active rules for current user + system rules ordered by priority
    rules = CategorizationRule.query.filter(
        db.or_(
            CategorizationRule.user_id == current_user_id,
            CategorizationRule.user_id.is_(None)  # System rules
        ),
        CategorizationRule.is_active == True
    ).order_by(
        CategorizationRule.priority.desc()
    ).all()
    
    if not rules:
        return jsonify({'message': 'No active rules found', 'updated': 0}), 200
    
    # Get all transactions for current user
    transactions = Transaction.query.filter_by(user_id=current_user_id).all()
    
    updated_count = 0
    updated_transactions = []
    
    for transaction in transactions:
        for rule in rules:
            if rule.matches(transaction.description):
                # Only update if category is different
                if transaction.category_id != rule.category_id:
                    old_category = transaction.category.name if transaction.category else 'Unknown'
                    transaction.category_id = rule.category_id
                    updated_count += 1
                    updated_transactions.append({
                        'id': transaction.id,
                        'description': transaction.description,
                        'old_category': old_category,
                        'new_category': rule.category.name,
                        'rule_name': rule.name
                    })
                break  # Stop after first matching rule (highest priority)
    
    db.session.commit()
    
    return jsonify({
        'message': f'Applied rules to {updated_count} transactions',
        'updated': updated_count,
        'details': updated_transactions
    }), 200

@rules_bp.route('/', methods=['GET'])
@login_required
def get_rules():
    """Get all categorization rules (user rules + system rules)"""
    current_user_id = session['user_id']
    rules = CategorizationRule.query.filter(
        db.or_(
            CategorizationRule.user_id == current_user_id,
            CategorizationRule.user_id.is_(None)  # System rules
        )
    ).order_by(
        CategorizationRule.priority.desc(),
        CategorizationRule.created_at.desc()
    ).all()
    return jsonify([r.to_dict() for r in rules])

@rules_bp.route('/<int:id>', methods=['GET'])
@login_required
def get_rule(id):
    """Get a specific rule (user rule or system rule)"""
    current_user_id = session['user_id']
    rule = CategorizationRule.query.filter(
        CategorizationRule.id == id,
        db.or_(
            CategorizationRule.user_id == current_user_id,
            CategorizationRule.user_id.is_(None)  # System rules
        )
    ).first_or_404()
    return jsonify(rule.to_dict())

@rules_bp.route('/', methods=['POST'])
@write_required
def create_rule():
    """Create a new categorization rule"""
    data = request.get_json()
    
    required_fields = ['name', 'keywords', 'category_id']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Verify category exists and user has access
    current_user_id = session['user_id']
    category = Category.query.filter(
        Category.id == data['category_id'],
        (Category.user_id == current_user_id) | (Category.user_id.is_(None))
    ).first()
    if not category:
        return jsonify({'error': 'Category not found or access denied'}), 404
    
    # Check for duplicate names within user's scope
    existing = CategorizationRule.query.filter_by(
        name=data['name'], 
        user_id=current_user_id
    ).first()
    if existing:
        return jsonify({'error': 'Rule name already exists'}), 400
    
    rule = CategorizationRule(
        name=data['name'],
        keywords=data['keywords'],
        category_id=data['category_id'],
        priority=data.get('priority', 0),
        is_active=data.get('is_active', True),
        user_id=current_user_id  # Associate with current user
    )
    
    db.session.add(rule)
    db.session.commit()
    
    return jsonify(rule.to_dict()), 201

@rules_bp.route('/<int:id>', methods=['PUT'])
@write_required
def update_rule(id):
    """Update a categorization rule (only user rules can be updated)"""
    current_user_id = session['user_id']
    rule = CategorizationRule.query.filter_by(
        id=id, 
        user_id=current_user_id  # Only allow updates to user rules
    ).first()
    if not rule:
        # Check if it's a system rule the user can't edit
        system_rule = CategorizationRule.query.filter_by(id=id, user_id=None).first()
        if system_rule:
            return jsonify({'error': 'System rules cannot be edited. Duplicate the rule first to create your own copy.'}), 403
        return jsonify({'error': 'Rule not found'}), 404
    data = request.get_json()
    
    # Check for duplicate names if name is being changed
    if 'name' in data and data['name'] != rule.name:
        existing = CategorizationRule.query.filter_by(
            name=data['name'], 
            user_id=current_user_id
        ).first()
        if existing:
            return jsonify({'error': 'Rule name already exists'}), 400
    
    # Verify category exists and user has access if being changed
    if 'category_id' in data:
        category = Category.query.filter(
            Category.id == data['category_id'],
            db.or_(
                Category.user_id == current_user_id,
                Category.user_id.is_(None)  # System categories
            )
        ).first()
        if not category:
            return jsonify({'error': 'Category not found or access denied'}), 404
        rule.category_id = data['category_id']
    
    if 'name' in data:
        rule.name = data['name']
    if 'keywords' in data:
        rule.keywords = data['keywords']
    if 'priority' in data:
        rule.priority = data['priority']
    if 'is_active' in data:
        rule.is_active = data['is_active']
    
    db.session.commit()
    
    return jsonify(rule.to_dict())

@rules_bp.route('/<int:id>', methods=['DELETE'])
@write_required
def delete_rule(id):
    """Delete a categorization rule (only user rules can be deleted)"""
    current_user_id = session['user_id']
    rule = CategorizationRule.query.filter_by(
        id=id, 
        user_id=current_user_id  # Only allow deletion of user rules
    ).first()
    if not rule:
        system_rule = CategorizationRule.query.filter_by(id=id, user_id=None).first()
        if system_rule:
            return jsonify({'error': 'System rules cannot be deleted.'}), 403
        return jsonify({'error': 'Rule not found'}), 404
    
    db.session.delete(rule)
    db.session.commit()
    
    return jsonify({'message': 'Rule deleted successfully'}), 200

@rules_bp.route('/test', methods=['POST'])
def test_rule():
    """Test a rule against a description"""
    data = request.get_json()
    
    if not data.get('description'):
        return jsonify({'error': 'Description is required'}), 400
    
    description = data['description']
    
    # Test against all active rules (user rules + system rules)
    current_user_id = session['user_id']
    rules = CategorizationRule.query.filter(
        db.or_(
            CategorizationRule.user_id == current_user_id,
            CategorizationRule.user_id.is_(None)  # System rules
        ),
        CategorizationRule.is_active == True
    ).order_by(
        CategorizationRule.priority.desc()
    ).all()
    
    matched_rules = []
    for rule in rules:
        if rule.matches(description):
            matched_rules.append({
                'rule_id': rule.id,
                'rule_name': rule.name,
                'category_id': rule.category_id,
                'category_name': rule.category.name,
                'priority': rule.priority,
                'matched_keywords': [kw for kw in rule.get_keywords_list() if kw in description.lower()]
            })
    
    return jsonify({
        'description': description,
        'matched_rules': matched_rules,
        'primary_match': matched_rules[0] if matched_rules else None
    })

@rules_bp.route('/bulk-import', methods=['POST'])
@write_required
def bulk_import_rules():
    """Bulk import categorization rules from a list"""
    data = request.get_json()
    
    if not isinstance(data.get('rules'), list):
        return jsonify({'error': 'Rules must be a list'}), 400
    
    imported_count = 0
    errors = []
    
    for i, rule_data in enumerate(data['rules']):
        try:
            required_fields = ['name', 'keywords', 'category_id']
            if not all(field in rule_data for field in required_fields):
                errors.append(f"Rule {i}: Missing required fields")
                continue
            
            # Check for duplicate names
            existing = CategorizationRule.query.filter_by(name=rule_data['name']).first()
            if existing:
                errors.append(f"Rule {i}: Rule name '{rule_data['name']}' already exists")
                continue
            
            # Verify category exists
            category = Category.query.get(rule_data['category_id'])
            if not category:
                errors.append(f"Rule {i}: Category {rule_data['category_id']} not found")
                continue
            
            rule = CategorizationRule(
                name=rule_data['name'],
                keywords=rule_data['keywords'],
                category_id=rule_data['category_id'],
                priority=rule_data.get('priority', 0),
                is_active=rule_data.get('is_active', True)
            )
            
            db.session.add(rule)
            imported_count += 1
        
        except Exception as e:
            errors.append(f"Rule {i}: {str(e)}")
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 400
    
    return jsonify({
        'imported': imported_count,
        'total': len(data['rules']),
        'errors': errors if errors else None
    }), 201

@rules_bp.route('/export', methods=['GET'])
@login_required
def export_rules():
    """Export all rules as JSON with category names for portability"""
    rules = CategorizationRule.query.order_by(
        CategorizationRule.priority.desc()
    ).all()
    
    export_data = []
    for rule in rules:
        export_data.append({
            'name': rule.name,
            'keywords': rule.keywords,
            'category_name': rule.category.name if rule.category else None,
            'category_type': rule.category.type if rule.category else None,
            'priority': rule.priority,
            'is_active': rule.is_active
        })
    
    return jsonify({
        'rules': export_data,
        'count': len(export_data)
    })

@rules_bp.route('/import', methods=['POST'])
@write_required
def import_rules():
    """Import rules from JSON, matching categories by name"""
    data = request.get_json()
    
    if not isinstance(data.get('rules'), list):
        return jsonify({'error': 'Rules must be a list'}), 400
    
    imported_count = 0
    skipped_count = 0
    errors = []
    
    for i, rule_data in enumerate(data['rules']):
        try:
            # Check required fields
            if not rule_data.get('name') or not rule_data.get('keywords'):
                errors.append(f"Rule {i+1}: Missing name or keywords")
                continue
            
            # Check for duplicate names
            existing = CategorizationRule.query.filter_by(name=rule_data['name']).first()
            if existing:
                skipped_count += 1
                continue
            
            # Find category by name or ID
            category = None
            if rule_data.get('category_id'):
                category = Category.query.get(rule_data['category_id'])
            elif rule_data.get('category_name'):
                category = Category.query.filter_by(name=rule_data['category_name']).first()
                # Create category if it doesn't exist
                if not category and rule_data.get('category_type'):
                    category = Category(
                        name=rule_data['category_name'],
                        type=rule_data['category_type']
                    )
                    db.session.add(category)
                    db.session.flush()  # Get the ID
            
            if not category:
                errors.append(f"Rule {i+1} '{rule_data['name']}': Category not found")
                continue
            
            rule = CategorizationRule(
                name=rule_data['name'],
                keywords=rule_data['keywords'],
                category_id=category.id,
                priority=rule_data.get('priority', 0),
                is_active=rule_data.get('is_active', True)
            )
            
            db.session.add(rule)
            imported_count += 1
        
        except Exception as e:
            errors.append(f"Rule {i+1}: {str(e)}")
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 400
    
    return jsonify({
        'imported': imported_count,
        'skipped': skipped_count,
        'total': len(data['rules']),
        'errors': errors if errors else None
    }), 201
