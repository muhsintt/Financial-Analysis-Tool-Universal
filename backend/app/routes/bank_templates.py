"""
API routes for bank statement templates.
Endpoints:
  GET    /api/bank-templates/            list templates for current user
  POST   /api/bank-templates/            create a new template
  DELETE /api/bank-templates/<id>        delete a template
  POST   /api/bank-templates/detect      analyse a file and suggest a matching template
"""

from flask import Blueprint, request, jsonify, session
from app import db
from app.models.bank_template import BankTemplate
from app.routes.auth import login_required, write_required
import json
import csv
import io

bank_templates_bp = Blueprint('bank_templates', __name__, url_prefix='/api/bank-templates')


# ── list ──────────────────────────────────────────────────────────────────────

@bank_templates_bp.route('/', methods=['GET'])
@login_required
def get_templates():
    templates = (
        BankTemplate.query
        .filter_by(user_id=session['user_id'])
        .order_by(BankTemplate.name)
        .all()
    )
    return jsonify([t.to_dict() for t in templates])


# ── create ────────────────────────────────────────────────────────────────────

@bank_templates_bp.route('/', methods=['POST'])
@write_required
def create_template():
    data = request.get_json()
    name = (data.get('name') or '').strip()
    headers = data.get('headers', [])
    mapping = data.get('column_mapping', {})

    if not name:
        return jsonify({'error': 'name is required'}), 400
    if not headers:
        return jsonify({'error': 'headers are required'}), 400
    if not mapping.get('date_col') or not mapping.get('description_col') or not mapping.get('amount_col'):
        return jsonify({'error': 'column_mapping must include date_col, description_col, and amount_col'}), 400

    template = BankTemplate(
        name=name,
        headers=json.dumps(headers),
        column_mapping=json.dumps(mapping),
        user_id=session['user_id'],
    )
    db.session.add(template)
    db.session.commit()
    return jsonify(template.to_dict()), 201


# ── delete ────────────────────────────────────────────────────────────────────

@bank_templates_bp.route('/<int:template_id>', methods=['DELETE'])
@write_required
def delete_template(template_id):
    template = BankTemplate.query.filter_by(
        id=template_id, user_id=session['user_id']
    ).first_or_404()
    db.session.delete(template)
    db.session.commit()
    return jsonify({'message': 'Template deleted'})


# ── detect ────────────────────────────────────────────────────────────────────

@bank_templates_bp.route('/detect', methods=['POST'])
@login_required
def detect_bank():
    """
    Accepts a CSV/Excel file, extracts its column headers, and returns the
    best-matching saved template together with a confidence score.
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    filename = (file.filename or '').lower()

    try:
        if filename.endswith('.csv'):
            raw = file.read().decode('utf-8', errors='replace')
            reader = csv.reader(io.StringIO(raw))
            headers = [h.strip() for h in (next(reader, []))]
        elif filename.endswith(('.xlsx', '.xls')):
            import pandas as pd
            df = pd.read_excel(file, nrows=0)
            headers = [str(c).strip() for c in df.columns]
        else:
            return jsonify({'error': 'Unsupported file type'}), 400

        headers = [h for h in headers if h]

        templates = BankTemplate.query.filter_by(user_id=session['user_id']).all()
        matches = []
        for t in templates:
            score = t.match_score(headers)
            if score > 0:
                matches.append({'template': t.to_dict(), 'score': round(score, 3)})
        matches.sort(key=lambda x: x['score'], reverse=True)

        return jsonify({
            'file_headers': headers,
            'best_match': matches[0] if matches else None,
            'all_matches': matches,
        })

    except Exception as exc:
        return jsonify({'error': str(exc)}), 400
