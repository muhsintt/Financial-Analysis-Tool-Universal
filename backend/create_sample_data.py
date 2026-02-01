"""
Sample Data Generator for Expense Tracker

This script creates sample transactions and budgets for testing.
Run this AFTER the application has started and created the database.

Usage:
  1. Start the application normally (start.bat or start.sh)
  2. Open Command Prompt/Terminal in the backend folder
  3. Run: python create_sample_data.py
  4. Restart the application to see sample data
"""

import sys
import os
from datetime import datetime, timedelta
from random import choice, randint

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.budget import Budget

def create_sample_data():
    """Create sample data for testing"""
    
    app = create_app()
    
    with app.app_context():
        # Check if data already exists
        if Transaction.query.first():
            print("Sample data already exists. Skipping...")
            return
        
        print("Creating sample categories...")
        
        # Create expense categories
        expense_categories = [
            'Groceries', 'Restaurants', 'Transportation', 'Utilities',
            'Entertainment', 'Shopping', 'Healthcare', 'Insurance',
            'Rent/Mortgage', 'Savings', 'Debt Payment'
        ]
        
        # Create income categories
        income_categories = ['Salary', 'Freelance', 'Investment', 'Bonus']
        
        categories = {}
        
        for cat_name in expense_categories:
            cat = Category(name=cat_name, type='expense', color='#e74c3c')
            db.session.add(cat)
            categories[cat_name] = cat
        
        for cat_name in income_categories:
            cat = Category(name=cat_name, type='income', color='#27ae60')
            db.session.add(cat)
            categories[cat_name] = cat
        
        db.session.commit()
        
        print("Creating sample transactions...")
        
        # Sample expense data
        expenses = [
            ('Trader Joe\'s', 'Groceries', 75.50),
            ('Whole Foods', 'Groceries', 125.00),
            ('McDonald\'s', 'Restaurants', 15.50),
            ('Chipotle', 'Restaurants', 12.75),
            ('Uber', 'Transportation', 18.50),
            ('Gas Station', 'Transportation', 45.00),
            ('Electric Bill', 'Utilities', 120.00),
            ('Water Bill', 'Utilities', 35.50),
            ('Netflix', 'Entertainment', 15.99),
            ('Movie Ticket', 'Entertainment', 16.00),
            ('Amazon', 'Shopping', 89.99),
            ('Target', 'Shopping', 65.30),
            ('CVS Pharmacy', 'Healthcare', 25.50),
            ('Doctor Visit', 'Healthcare', 150.00),
            ('Rent Payment', 'Rent/Mortgage', 1500.00),
            ('Home Insurance', 'Insurance', 75.00),
        ]
        
        # Create transactions for last 3 months
        today = datetime.now().date()
        
        for i in range(90):
            trans_date = today - timedelta(days=i)
            
            # 60% chance of expense per day
            if randint(1, 100) <= 60:
                desc, cat_name, amount = choice(expenses)
                transaction = Transaction(
                    description=desc,
                    amount=amount,
                    type='expense',
                    date=trans_date,
                    category_id=categories[cat_name].id,
                    source='manual'
                )
                db.session.add(transaction)
            
            # 20% chance of income per day
            if randint(1, 100) <= 20 and trans_date.weekday() < 5:  # Weekdays only
                salaries = [
                    ('Salary', 'Salary', 2000),
                    ('Freelance Project', 'Freelance', randint(100, 500))
                ]
                desc, cat_name, amount = choice(salaries)
                transaction = Transaction(
                    description=desc,
                    amount=amount,
                    type='income',
                    date=trans_date,
                    category_id=categories[cat_name].id,
                    source='manual'
                )
                db.session.add(transaction)
        
        db.session.commit()
        
        print("Creating sample budgets...")
        
        # Create budgets for current month
        current_month = today.month
        current_year = today.year
        
        budgets_data = [
            ('Groceries', 400),
            ('Restaurants', 150),
            ('Transportation', 300),
            ('Entertainment', 100),
            ('Shopping', 200),
            ('Utilities', 150),
            ('Healthcare', 200),
        ]
        
        for cat_name, amount in budgets_data:
            budget = Budget(
                category_id=categories[cat_name].id,
                amount=amount,
                period='monthly',
                year=current_year,
                month=current_month
            )
            db.session.add(budget)
        
        db.session.commit()
        
        print("Sample data created successfully!")
        print("")
        print("Summary:")
        print(f"  - Created {Category.query.count()} categories")
        print(f"  - Created {Transaction.query.count()} transactions")
        print(f"  - Created {Budget.query.count()} budgets")
        print("")
        print("You can now restart the application to see the sample data.")

if __name__ == '__main__':
    create_sample_data()
