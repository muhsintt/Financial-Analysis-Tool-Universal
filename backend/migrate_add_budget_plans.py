#!/usr/bin/env python3
"""Migration: add budget_plans and budget_plan_items tables."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    inspector = db.inspect(db.engine)
    existing = inspector.get_table_names()

    with db.engine.connect() as conn:
        if 'budget_plans' not in existing:
            conn.execute(text("""
                CREATE TABLE budget_plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(150) NOT NULL,
                    source_year INTEGER,
                    source_month INTEGER,
                    total_amount FLOAT NOT NULL DEFAULT 0.0,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            print("Created table: budget_plans")
        else:
            print("Table budget_plans already exists, skipping.")

        if 'budget_plan_items' not in existing:
            conn.execute(text("""
                CREATE TABLE budget_plan_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plan_id INTEGER NOT NULL REFERENCES budget_plans(id),
                    category_id INTEGER NOT NULL REFERENCES categories(id),
                    amount FLOAT NOT NULL DEFAULT 0.0,
                    actual_amount FLOAT NOT NULL DEFAULT 0.0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            print("Created table: budget_plan_items")
        else:
            print("Table budget_plan_items already exists, skipping.")

    print("Migration complete.")
