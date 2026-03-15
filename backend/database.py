import duckdb
from config import settings
from passlib.context import CryptContext
import uuid

# Global connection for the main application
db = None

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def get_db():
    global db
    if db is None:
        init_db()
    return db

def init_db():
    global db
    db = duckdb.connect(database=settings.DATABASE_PATH, read_only=False)
    
    # Enable multi-threading for the connection
    db.execute("PRAGMA threads=4")
    
    # Create tables
    db.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id VARCHAR PRIMARY KEY,
        email VARCHAR UNIQUE NOT NULL,
        password_hash VARCHAR NOT NULL,
        credits INTEGER DEFAULT 0,
        role VARCHAR DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    db.execute("""
    CREATE TABLE IF NOT EXISTS verification_jobs (
        id VARCHAR PRIMARY KEY,
        user_id VARCHAR NOT NULL REFERENCES users(id),
        file_name VARCHAR,
        total_emails INTEGER DEFAULT 0,
        processed_emails INTEGER DEFAULT 0,
        status VARCHAR DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP
    );
    """)
    
    db.execute("""
    CREATE TABLE IF NOT EXISTS verification_results (
        id VARCHAR PRIMARY KEY,
        job_id VARCHAR NOT NULL REFERENCES verification_jobs(id),
        email VARCHAR NOT NULL,
        domain VARCHAR,
        status VARCHAR,
        is_role BOOLEAN,
        is_disposable BOOLEAN,
        smtp_result VARCHAR,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    db.execute("""
    CREATE TABLE IF NOT EXISTS credits_log (
        id VARCHAR PRIMARY KEY,
        user_id VARCHAR NOT NULL REFERENCES users(id),
        credits_used INTEGER,
        job_id VARCHAR,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS disposable_domains (
        domain VARCHAR PRIMARY KEY
    );
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS domain_intelligence (
        domain VARCHAR PRIMARY KEY,
        mx_server VARCHAR,
        catch_all BOOLEAN,
        disposable BOOLEAN,
        reputation_score DOUBLE,
        last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS email_cache (
        email VARCHAR PRIMARY KEY,
        status VARCHAR,
        confidence DOUBLE,
        verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Seed an admin user if not exists
    admin_email = "admin@example.com"
    res = db.execute("SELECT id FROM users WHERE email = ?", [admin_email]).fetchone()
    if not res:
        admin_id = str(uuid.uuid4())
        hashed_password = pwd_context.hash("admin")
        db.execute(
            "INSERT INTO users (id, email, password_hash, credits, role) VALUES (?, ?, ?, ?, ?)",
            [admin_id, admin_email, hashed_password, 1000000, 'admin']
        )
