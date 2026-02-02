from flask import Blueprint, request, jsonify
from app import db
from app.models.categorization_rule import CategorizationRule
from app.models.category import Category

rules_bp = Blueprint('rules', __name__, url_prefix='/api/rules')

@rules_bp.route('/', methods=['GET'])
def get_rules():
    """Get all categorization rules"""
    rules = CategorizationRule.query.order_by(
        CategorizationRule.priority.desc(),
        CategorizationRule.created_at.desc()
    ).all()
    return jsonify([r.to_dict() for r in rules])

@rules_bp.route('/<int:id>', methods=['GET'])
def get_rule(id):
    """Get a specific rule"""
    rule = CategorizationRule.query.get_or_404(id)
    return jsonify(rule.to_dict())

@rules_bp.route('/', methods=['POST'])
def create_rule():
    """Create a new categorization rule"""
    data = request.get_json()
    
    required_fields = ['name', 'keywords', 'category_id']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Verify category exists
    category = Category.query.get(data['category_id'])
    if not category:
        return jsonify({'error': 'Category not found'}), 404
    
    # Check for duplicate names
    existing = CategorizationRule.query.filter_by(name=data['name']).first()
    if existing:
        return jsonify({'error': 'Rule name already exists'}), 400
    
    rule = CategorizationRule(
        name=data['name'],
        keywords=data['keywords'],
        category_id=data['category_id'],
        priority=data.get('priority', 0),
        is_active=data.get('is_active', True)
    )
    
    db.session.add(rule)
    db.session.commit()
    
    return jsonify(rule.to_dict()), 201

@rules_bp.route('/<int:id>', methods=['PUT'])
def update_rule(id):
    """Update a categorization rule"""
    rule = CategorizationRule.query.get_or_404(id)
    data = request.get_json()
    
    # Check for duplicate names if name is being changed
    if 'name' in data and data['name'] != rule.name:
        existing = CategorizationRule.query.filter_by(name=data['name']).first()
        if existing:
            return jsonify({'error': 'Rule name already exists'}), 400
    
    # Verify category exists if being changed
    if 'category_id' in data:
        category = Category.query.get(data['category_id'])
        if not category:
            return jsonify({'error': 'Category not found'}), 404
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
def delete_rule(id):
    """Delete a categorization rule"""
    rule = CategorizationRule.query.get_or_404(id)
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
    
    # Test against all active rules
    rules = CategorizationRule.query.filter_by(is_active=True).order_by(
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
