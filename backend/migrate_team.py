import duckdb
from config import settings

def update_schema():
    db = duckdb.connect(settings.DATABASE_PATH, read_only=False)
    
    # 1. Add department column to users
    try:
        db.execute("ALTER TABLE users ADD COLUMN department VARCHAR")
        print("Added department column to users.")
    except Exception as e:
        print(f"Error adding department (might already exist): {e}")

    # 2. Create audit_logs table
    try:
        db.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id VARCHAR PRIMARY KEY,
            workspace_id VARCHAR NOT NULL,
            actor_id VARCHAR NOT NULL,
            action VARCHAR NOT NULL,
            target_id VARCHAR,
            details VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        print("Created audit_logs table.")
    except Exception as e:
        print(f"Error creating audit_logs: {e}")

if __name__ == "__main__":
    update_schema()
