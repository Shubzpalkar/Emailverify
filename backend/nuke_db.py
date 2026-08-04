import duckdb
import os
import glob
from config import settings
from database import init_db, get_db

def nuke_and_rebuild():
    # 1. Export all tables to parquet
    print("Connecting to db...")
    db = duckdb.connect(settings.DATABASE_PATH, read_only=False)
    
    tables = [
        "users",
        "workspaces",
        "api_keys",
        "verification_jobs",
        "verification_results",
        "credits_log",
        "subscriptions",
        "payments",
        "payment_transactions",
        "credit_transactions",
        "invoices",
        "billing_history",
        "disposable_domains",
        "domain_intelligence",
        "email_cache",
        "password_reset_tokens",
        "plans"
    ]
    
    print("Exporting data...")
    os.makedirs("backup_parquet", exist_ok=True)
    for table in tables:
        try:
            # Check if it has data
            count = db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            if count > 0:
                db.execute(f"COPY {table} TO 'backup_parquet/{table}.parquet' (FORMAT PARQUET)")
                print(f"Exported {table}")
        except Exception as e:
            print(f"Skipping {table}: {e}")
            
    db.close()
    
    # 2. Delete the database file
    print("Deleting old database...")
    os.remove(settings.DATABASE_PATH)
    if os.path.exists(settings.DATABASE_PATH + ".wal"):
        os.remove(settings.DATABASE_PATH + ".wal")
        
    # 3. Init new database
    print("Initializing new database...")
    init_db()
    db = get_db()
    
    # 4. Import data
    print("Importing data...")
    for file in glob.glob("backup_parquet/*.parquet"):
        table = os.path.basename(file).split(".")[0]
        try:
            # First delete any seed data (like plans)
            db.execute(f"DELETE FROM {table}")
            
            # Insert from parquet
            db.execute(f"INSERT INTO {table} SELECT * FROM '{file}'")
            print(f"Imported {table}")
        except Exception as e:
            # The columns might not match if schema changed (e.g. workspace_id missing in users? wait, users in the parquet HAS workspace_id)
            # If columns don't match, we can do INSERT INTO table BY NAME SELECT * FROM parquet
            try:
                db.execute(f"INSERT INTO {table} BY NAME SELECT * FROM '{file}'")
                print(f"Imported {table} BY NAME")
            except Exception as e2:
                print(f"Failed to import {table}: {e2}")

if __name__ == "__main__":
    nuke_and_rebuild()
