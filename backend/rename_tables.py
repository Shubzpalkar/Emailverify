import duckdb
import os
from config import settings
from database import get_db

def fix_foreign_keys_robust():
    db = get_db()
    
    # 1. Rename all tables to _old (in safe order for dropping constraints implicitly by renaming the referenced ones? No, renaming doesn't drop constraints, but we just move the old table aside)
    tables = [
        "verification_results",
        "payment_transactions",
        "invoices",
        "credit_transactions",
        "credits_log",
        "api_keys",
        "verification_jobs",
        "subscriptions",
        "payments",
        "billing_history",
        "users", # we don't need to rename users, we only need child tables
    ]
    
    for table in tables:
        if table == "users":
            continue
        try:
            db.execute(f"DROP TABLE IF EXISTS {table}_old")
            db.execute(f"ALTER TABLE {table} RENAME TO {table}_old")
            print(f"Renamed {table} to {table}_old")
        except Exception as e:
            print(f"Error renaming {table}: {e}")

if __name__ == "__main__":
    fix_foreign_keys_robust()
