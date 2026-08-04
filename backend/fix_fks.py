import duckdb
import os
from config import settings

def fix_foreign_keys():
    db = duckdb.connect(database=settings.DATABASE_PATH, read_only=False)
    
    tables_to_strip = [
        "verification_results",
        "payment_transactions",
        "invoices",
        "credit_transactions",
        "credits_log",
        "api_keys",
        "verification_jobs",
        "subscriptions",
        "payments",
        "billing_history"
    ]
    
    for table in tables_to_strip:
        try:
            # Clean up dangling _new tables
            db.execute(f"DROP TABLE IF EXISTS {table}_new")
            
            print(f"Stripping FKs from {table}...")
            exists = db.execute(f"SELECT count(*) FROM information_schema.tables WHERE table_name = '{table}'").fetchone()[0]
            if exists:
                db.execute(f"CREATE TABLE {table}_new AS SELECT * FROM {table}")
                db.execute(f"DROP TABLE {table}")
                db.execute(f"ALTER TABLE {table}_new RENAME TO {table}")
                print(f"Success for {table}.")
            else:
                print(f"Table {table} does not exist, skipping.")
        except Exception as e:
            print(f"Error on {table}: {e}")
            if "invalidated" in str(e).lower() or "fatal" in str(e).lower() or "dereference" in str(e).lower():
                db.close()
                db = duckdb.connect(database=settings.DATABASE_PATH, read_only=False)

if __name__ == "__main__":
    fix_foreign_keys()
