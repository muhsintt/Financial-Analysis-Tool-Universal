from flask import Blueprint, request, jsonify, session
from app import db
from app.models.budget_plan import BudgetPlan, BudgetPlanItem
from app.models.transaction import Transaction
from app.models.category import Category
from app.routes.auth import write_required, login_required
from datetime import date
import calendar
import json

budget_plans_bp = Blueprint('budget_plans', __name__, url_prefix='/api/budget-plans')


def _user_id():
    return session['user_id']


# ──────────────────────────────────────────────────────────────────────────────
# Month summary helper
# ──────────────────────────────────────────────────────────────────────────────

def _get_month_summary(year, month, user_id):
    """Return (income, expense, net, category_totals) for a calendar month."""
    first = date(year, month, 1)
    last = date(year, month, calendar.monthrange(year, month)[1])

    transactions = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.date >= first,
        Transaction.date <= last,
        Transaction.is_excluded == False,  # noqa: E712
    ).all()

    income = sum(t.amount for t in transactions if t.type == 'income')
    expense = sum(t.amount for t in transactions if t.type == 'expense')

    # Aggregate by category for expenses only
    category_totals = {}
    for t in transactions:
        if t.type == 'expense' and t.category_id:
            cat_id = t.category_id
            category_totals[cat_id] = category_totals.get(cat_id, 0.0) + t.amount

    return income, expense, income - expense, category_totals


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/budget-plans/month-summary?year=&month=
# Returns income/expense/net + per-category breakdown for the requested month.
# ──────────────────────────────────────────────────────────────────────────────

@budget_plans_bp.route('/month-summary', methods=['GET'])
@login_required
def month_summary():
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    if not year or not month or not (1 <= month <= 12):
        return jsonify({'error': 'Valid year and month (1-12) are required'}), 400

    uid = _user_id()
    income, expense, net, cat_totals = _get_month_summary(year, month, uid)

    # Enrich with category names
    categories = []
    for cat_id, total in cat_totals.items():
        cat = Category.query.get(cat_id)
        if cat:
            categories.append({
                'category_id': cat_id,
                'category_name': cat.full_name if hasattr(cat, 'full_name') else cat.name,
                'category_color': cat.color,
                'actual_amount': round(total, 2),
            })
    categories.sort(key=lambda x: -x['actual_amount'])

    return jsonify({
        'year': year,
        'month': month,
        'income': round(income, 2),
        'expense': round(expense, 2),
        'net': round(net, 2),
        'categories': categories,
    })


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/budget-plans/
# ──────────────────────────────────────────────────────────────────────────────

@budget_plans_bp.route('/', methods=['GET'])
@login_required
def list_plans():
    plans = BudgetPlan.query.filter_by(user_id=_user_id()).order_by(
        BudgetPlan.created_at.desc()
    ).all()
    return jsonify([p.to_dict(include_items=False) for p in plans])


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/budget-plans/<id>
# ──────────────────────────────────────────────────────────────────────────────

@budget_plans_bp.route('/<int:plan_id>', methods=['GET'])
@login_required
def get_plan(plan_id):
    plan = BudgetPlan.query.filter_by(id=plan_id, user_id=_user_id()).first_or_404()
    return jsonify(plan.to_dict())


# ──────────────────────────────────────────────────────────────────────────────
# POST /api/budget-plans/
# Body: { name, source_year, source_month, items: [{category_id, amount}] }
# ──────────────────────────────────────────────────────────────────────────────

@budget_plans_bp.route('/', methods=['POST'])
@write_required
def create_plan():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON body'}), 400

    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'Budget plan name is required'}), 400

    source_year = data.get('source_year')
    source_month = data.get('source_month')
    items_data = data.get('items', [])

    if not isinstance(items_data, list) or not items_data:
        return jsonify({'error': 'At least one budget item is required'}), 400

    uid = _user_id()

    plan = BudgetPlan(
        name=name,
        source_year=source_year,
        source_month=source_month,
        user_id=uid,
        total_amount=0.0,
    )
    db.session.add(plan)
    db.session.flush()  # get plan.id

    for item in items_data:
        cat_id = item.get('category_id')
        amount = float(item.get('amount', 0))
        actual = float(item.get('actual_amount', 0))
        group_name = (item.get('group_name') or '').strip() or None
        consolidated_ids = item.get('consolidated_category_ids')  # list or None

        # For consolidated items, category_id must be the primary (first) category
        if not cat_id:
            if consolidated_ids and isinstance(consolidated_ids, list):
                cat_id = consolidated_ids[0]
            else:
                continue

        # Verify category access
        cat = Category.query.filter(
            Category.id == cat_id,
            (Category.user_id == uid) | (Category.user_id.is_(None))
        ).first()
        if not cat:
            continue

        # Serialize consolidated_ids to JSON string for storage
        consolidated_json = (
            json.dumps(consolidated_ids)
            if consolidated_ids and isinstance(consolidated_ids, list)
            else None
        )

        plan_item = BudgetPlanItem(
            plan_id=plan.id,
            category_id=cat_id,
            group_name=group_name,
            consolidated_category_ids=consolidated_json,
            amount=amount,
            actual_amount=actual,
        )
        db.session.add(plan_item)

    db.session.flush()
    plan.recalculate_total()
    db.session.commit()

    return jsonify(plan.to_dict()), 201


# ──────────────────────────────────────────────────────────────────────────────
# PUT /api/budget-plans/<id>
# Body: { name?, items: [{id?, category_id, amount, actual_amount}] }
# The caller is responsible for confirming any total-budget increase before
# calling this endpoint (the frontend handles that confirmation).
# ──────────────────────────────────────────────────────────────────────────────

@budget_plans_bp.route('/<int:plan_id>', methods=['PUT'])
@write_required
def update_plan(plan_id):
    plan = BudgetPlan.query.filter_by(id=plan_id, user_id=_user_id()).first_or_404()
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON body'}), 400

    if 'name' in data:
        name = (data['name'] or '').strip()
        if not name:
            return jsonify({'error': 'Budget plan name cannot be empty'}), 400
        plan.name = name

    if 'items' in data:
        uid = _user_id()

        # Build lookup maps for existing items
        existing_by_id = {item.id: item for item in plan.items}
        existing_by_cat = {item.category_id: item for item in plan.items}

        # Track which existing item ids are touched
        touched_ids = set()

        for item_data in data['items']:
            cat_id = item_data.get('category_id')
            amount = float(item_data.get('amount', 0))
            actual = float(item_data.get('actual_amount', 0))
            item_id = item_data.get('id')
            group_name = (item_data.get('group_name') or '').strip() or None
            consolidated_ids = item_data.get('consolidated_category_ids')

            # For consolidated items, derive primary category_id
            if not cat_id and consolidated_ids and isinstance(consolidated_ids, list):
                cat_id = consolidated_ids[0]
            if not cat_id:
                continue

            consolidated_json = (
                json.dumps(consolidated_ids)
                if consolidated_ids and isinstance(consolidated_ids, list)
                else None
            )

            if item_id and item_id in existing_by_id:
                # Update existing item by DB id
                existing = existing_by_id[item_id]
                existing.amount = amount
                existing.actual_amount = actual
                existing.group_name = group_name
                existing.consolidated_category_ids = consolidated_json
                touched_ids.add(item_id)
            elif cat_id in existing_by_cat:
                # Update by primary category match
                existing = existing_by_cat[cat_id]
                existing.amount = amount
                existing.actual_amount = actual
                existing.group_name = group_name
                existing.consolidated_category_ids = consolidated_json
                touched_ids.add(existing.id)
            else:
                # New item — verify category access
                cat = Category.query.filter(
                    Category.id == cat_id,
                    (Category.user_id == uid) | (Category.user_id.is_(None))
                ).first()
                if cat:
                    new_item = BudgetPlanItem(
                        plan_id=plan.id,
                        category_id=cat_id,
                        group_name=group_name,
                        consolidated_category_ids=consolidated_json,
                        amount=amount,
                        actual_amount=actual,
                    )
                    db.session.add(new_item)
                    db.session.flush()
                    touched_ids.add(new_item.id)

        # Remove items that are no longer in the payload
        for item in list(plan.items):
            if item.id not in touched_ids:
                db.session.delete(item)

    db.session.flush()
    plan.recalculate_total()
    db.session.commit()

    return jsonify(plan.to_dict())


# ──────────────────────────────────────────────────────────────────────────────
# DELETE /api/budget-plans/<id>
# ──────────────────────────────────────────────────────────────────────────────

@budget_plans_bp.route('/<int:plan_id>', methods=['DELETE'])
@write_required
def delete_plan(plan_id):
    plan = BudgetPlan.query.filter_by(id=plan_id, user_id=_user_id()).first_or_404()
    db.session.delete(plan)
    db.session.commit()
    return jsonify({'message': 'Budget plan deleted'}), 200
