import duckdb
from config import settings
from database import get_db, init_db

def restore_data():
    # 1. Initialize schema (which now has NO foreign keys)
    init_db()
    db = get_db()
    
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
        "billing_history"
    ]
    
    for table in tables:
        try:
            print(f"Restoring {table}...")
            # Ensure _old exists
            exists = db.execute(f"SELECT count(*) FROM information_schema.tables WHERE table_name = '{table}_old'").fetchone()[0]
            if exists:
                # Insert data from _old to the newly created table
                db.execute(f"INSERT INTO {table} SELECT * FROM {table}_old")
                # Drop _old
                db.execute(f"DROP TABLE {table}_old")
                print(f"Success for {table}")
            else:
                print(f"No {table}_old found.")
        except Exception as e:
            print(f"Error restoring {table}: {e}")

if __name__ == "__main__":
    restore_data()
