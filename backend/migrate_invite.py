import duckdb
from config import settings

def migrate():
    db = duckdb.connect(settings.DATABASE_PATH, read_only=False)
    
    try:
        db.execute("""
        CREATE TABLE IF NOT EXISTS invitations (
            id VARCHAR PRIMARY KEY,
            workspace_id VARCHAR NOT NULL,
            email VARCHAR NOT NULL,
            role VARCHAR DEFAULT 'user',
            department VARCHAR,
            token VARCHAR UNIQUE NOT NULL,
            status VARCHAR DEFAULT 'Pending',
            created_by VARCHAR NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        print("Created invitations table.")
    except Exception as e:
        print(f"Error creating invitations: {e}")

if __name__ == "__main__":
    migrate()
