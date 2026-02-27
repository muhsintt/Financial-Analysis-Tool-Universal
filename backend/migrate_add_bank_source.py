"""
Migration: add bank_source column to transactions, and create bank_templates table.
Run from the backend/ directory:
    python migrate_add_bank_source.py
"""

import sqlite3
import os


def migrate():
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'expense_tracker.db')

    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # ── 1. Add bank_source column to transactions ──────────────────────────
        cursor.execute("PRAGMA table_info(transactions)")
        cols = [col[1] for col in cursor.fetchall()]

        if 'bank_source' not in cols:
            print("Adding bank_source column to transactions…")
            cursor.execute(
                "ALTER TABLE transactions ADD COLUMN bank_source VARCHAR(100)"
            )
            print("  ✓ bank_source added")
        else:
            print("  bank_source already exists — skipping")

        # ── 2. Create bank_templates table ─────────────────────────────────────
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='bank_templates'"
        )
        if not cursor.fetchone():
            print("Creating bank_templates table…")
            cursor.execute(
                """
                CREATE TABLE bank_templates (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    name          VARCHAR(100) NOT NULL,
                    headers       TEXT         NOT NULL,
                    column_mapping TEXT        NOT NULL,
                    user_id       INTEGER      NOT NULL REFERENCES users(id),
                    created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            print("  ✓ bank_templates table created")
        else:
            print("  bank_templates table already exists — skipping")

        conn.commit()
        print("Migration completed successfully!")

    except Exception as exc:
        print(f"Migration error: {exc}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == '__main__':
    migrate()
