#!/usr/bin/env python
"""
Initialize default categorization rules for the expense tracker.
Run this script once to set up common merchant/description keywords.
"""

from app import create_app, db
from app.models.category import Category
from app.models.categorization_rule import CategorizationRule

def initialize_default_rules():
    """Create default categorization rules"""
    
    app = create_app()
    
    with app.app_context():
        # Get or create categories
        categories = {}
        category_list = [
            ('Groceries', 'expense'),
            ('Restaurants & Dining', 'expense'),
            ('Transportation', 'expense'),
            ('Utilities', 'expense'),
            ('Entertainment/Subscriptions', 'expense'),
            ('Shopping/Retail', 'expense'),
            ('Health & Pharmacy', 'expense'),
            ('Housing', 'expense'),
            ('Income', 'income'),
        ]
        
        for name, cat_type in category_list:
            cat = Category.query.filter_by(name=name).first()
            if cat:
                categories[name] = cat.id
            else:
                cat = Category(name=name, type=cat_type, color='#3498db', icon='folder')
                db.session.add(cat)
                db.session.flush()
                categories[name] = cat.id
        
        # Define default rules (priority 0 means standard priority)
        default_rules = [
            # Groceries
            {
                'name': 'Grocery Stores',
                'keywords': 'whole foods, safeway, trader joes, kroger, publix, instacart, sprouts',
                'category_id': categories['Groceries'],
                'priority': 10
            },
            {
                'name': 'Supermarkets',
                'keywords': 'walmart, target, costco, sam\'s club, market basket',
                'category_id': categories['Groceries'],
                'priority': 9
            },
            # Restaurants
            {
                'name': 'Fast Food',
                'keywords': 'mcd, burger king, subway, taco bell, popeyes, chick-fil, chipotle',
                'category_id': categories['Restaurants & Dining'],
                'priority': 10
            },
            {
                'name': 'Restaurants',
                'keywords': 'restaurant, cafe, pizzeria, dining',
                'category_id': categories['Restaurants & Dining'],
                'priority': 8
            },
            # Transportation
            {
                'name': 'Ride Sharing',
                'keywords': 'uber, lyft, taxify',
                'category_id': categories['Transportation'],
                'priority': 10
            },
            {
                'name': 'Gas & Fuel',
                'keywords': 'shell, chevron, exxon, bp, speedway, sunoco, fuel',
                'category_id': categories['Transportation'],
                'priority': 10
            },
            {
                'name': 'Parking & Transit',
                'keywords': 'parking, transit, amtrak, metro',
                'category_id': categories['Transportation'],
                'priority': 8
            },
            # Utilities
            {
                'name': 'Internet & Phone',
                'keywords': 'comcast, verizon, at&t, internet, phone bill, broadband',
                'category_id': categories['Utilities'],
                'priority': 10
            },
            {
                'name': 'Utilities',
                'keywords': 'electric, water, gas, utility, city of',
                'category_id': categories['Utilities'],
                'priority': 9
            },
            # Entertainment
            {
                'name': 'Streaming Services',
                'keywords': 'netflix, hulu, disney, prime video, spotify, youtube',
                'category_id': categories['Entertainment/Subscriptions'],
                'priority': 10
            },
            {
                'name': 'Entertainment',
                'keywords': 'movie, concert, theater, steam, playstation, xbox, nintendo',
                'category_id': categories['Entertainment/Subscriptions'],
                'priority': 8
            },
            # Shopping
            {
                'name': 'Online Retailers',
                'keywords': 'amazon, ebay, etsy',
                'category_id': categories['Shopping/Retail'],
                'priority': 10
            },
            {
                'name': 'Electronics',
                'keywords': 'best buy, apple store, electronics',
                'category_id': categories['Shopping/Retail'],
                'priority': 9
            },
            # Health
            {
                'name': 'Pharmacy',
                'keywords': 'cvs, walgreens, pharmacy, drugstore',
                'category_id': categories['Health & Pharmacy'],
                'priority': 10
            },
            {
                'name': 'Healthcare',
                'keywords': 'doctor, hospital, medical, dental, clinic, health',
                'category_id': categories['Health & Pharmacy'],
                'priority': 8
            },
            # Housing
            {
                'name': 'Rent & Mortgage',
                'keywords': 'rent, mortgage, landlord, lease',
                'category_id': categories['Housing'],
                'priority': 10
            },
            # Income
            {
                'name': 'Salary',
                'keywords': 'salary, paycheck, payroll, wages',
                'category_id': categories['Income'],
                'priority': 10
            },
        ]
        
        # Add rules if they don't exist
        added_count = 0
        for rule_data in default_rules:
            existing = CategorizationRule.query.filter_by(name=rule_data['name']).first()
            if not existing:
                rule = CategorizationRule(**rule_data, is_active=True)
                db.session.add(rule)
                added_count += 1
        
        db.session.commit()
        print(f"✓ Initialized {added_count} default categorization rules")
        print(f"✓ Total rules in database: {CategorizationRule.query.count()}")
        print("\nDefault rules created:")
        for rule in CategorizationRule.query.order_by(CategorizationRule.priority.desc()).all():
            print(f"  - {rule.name} → {rule.category.name} (Priority: {rule.priority})")

if __name__ == '__main__':
    initialize_default_rules()
