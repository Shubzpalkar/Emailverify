import duckdb
from config import settings

def final_cleanup():
    db = duckdb.connect(settings.DATABASE_PATH, read_only=False)
    
    tables_to_strip = [
        "billing_history",
        "payments"
    ]
    
    for table in tables_to_strip:
        try:
            print(f"Stripping FKs from {table}...")
            # Check if table exists
            exists = db.execute(f"SELECT count(*) FROM information_schema.tables WHERE table_name = '{table}'").fetchone()[0]
            if exists:
                db.execute(f"CREATE TABLE {table}_new_clean AS SELECT * FROM {table}")
                db.execute(f"DROP TABLE {table}")
                db.execute(f"ALTER TABLE {table}_new_clean RENAME TO {table}")
                print(f"Success for {table}.")
        except Exception as e:
            print(f"Error on {table}: {e}")
            
    # Also drop any lingering _old tables
    try:
        db.execute("DROP TABLE IF EXISTS payments_old")
        print("Dropped payments_old")
    except Exception as e:
        print(f"Failed to drop payments_old: {e}")
        
    try:
        db.execute("DROP TABLE IF EXISTS billing_history_old")
        print("Dropped billing_history_old")
    except Exception:
        pass

if __name__ == "__main__":
    final_cleanup()
