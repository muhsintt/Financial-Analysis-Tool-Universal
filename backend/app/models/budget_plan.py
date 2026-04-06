from app import db
from datetime import datetime


class BudgetPlan(db.Model):
    """A named budget plan with per-category line items, created from month data."""
    __tablename__ = 'budget_plans'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    source_year = db.Column(db.Integer, nullable=True)   # month the plan was derived from
    source_month = db.Column(db.Integer, nullable=True)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='budget_plans')
    items = db.relationship(
        'BudgetPlanItem',
        backref='plan',
        lazy=True,
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<BudgetPlan {self.name}>'

    def recalculate_total(self):
        self.total_amount = sum(i.amount for i in self.items)

    def to_dict(self, include_items=True):
        result = {
            'id': self.id,
            'name': self.name,
            'source_year': self.source_year,
            'source_month': self.source_month,
            'total_amount': self.total_amount,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
        if include_items:
            result['items'] = [i.to_dict() for i in self.items]
        return result


class BudgetPlanItem(db.Model):
    """A single category line in a BudgetPlan."""
    __tablename__ = 'budget_plan_items'

    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('budget_plans.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False, default=0.0)
    actual_amount = db.Column(db.Float, nullable=False, default=0.0)  # from source month
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    category = db.relationship('Category', backref='budget_plan_items')

    def __repr__(self):
        return f'<BudgetPlanItem plan={self.plan_id} cat={self.category_id} amt={self.amount}>'

    def to_dict(self):
        category_name = None
        category_color = None
        if self.category:
            category_name = (
                self.category.full_name
                if hasattr(self.category, 'full_name')
                else self.category.name
            )
            category_color = self.category.color
        return {
            'id': self.id,
            'plan_id': self.plan_id,
            'category_id': self.category_id,
            'category_name': category_name,
            'category_color': category_color,
            'amount': self.amount,
            'actual_amount': self.actual_amount,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
