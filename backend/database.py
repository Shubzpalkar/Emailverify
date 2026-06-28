import duckdb
from config import settings
from passlib.context import CryptContext
import uuid
import asyncio

# Global connection for the main application
db = None

_db_write_lock = asyncio.Lock()

def get_db_write_lock():
    return _db_write_lock

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
    db.execute("PRAGMA memory_limit='4GB'")
    db.execute("PRAGMA temp_directory='/tmp'")
    
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
    CREATE TABLE IF NOT EXISTS api_keys (
        id VARCHAR PRIMARY KEY,
        user_id VARCHAR NOT NULL REFERENCES users(id),
        name VARCHAR NOT NULL,
        key_hash VARCHAR NOT NULL,
        prefix VARCHAR NOT NULL,
        last_used TIMESTAMP,
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

    db.execute("""
    CREATE TABLE IF NOT EXISTS password_reset_tokens (
        id VARCHAR PRIMARY KEY,
        user_id VARCHAR NOT NULL,
        token VARCHAR UNIQUE NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        used BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Migrations
    try:
        db.execute("ALTER TABLE users ADD COLUMN tier VARCHAR DEFAULT 'standard'")
    except Exception:
        pass

    try:
        db.execute("ALTER TABLE domain_intelligence ADD COLUMN server_type VARCHAR DEFAULT 'unknown'")
    except Exception:
        pass

    migrations = [
        "ALTER TABLE users ADD COLUMN admin_id VARCHAR DEFAULT NULL",
        "ALTER TABLE users ADD COLUMN credit_pool INTEGER DEFAULT 0",
        "ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE",
        "ALTER TABLE users ADD COLUMN created_by VARCHAR DEFAULT NULL",
        "ALTER TABLE users ADD COLUMN last_login TIMESTAMP DEFAULT NULL",
        "ALTER TABLE users ADD COLUMN custom_rate_limit INTEGER DEFAULT NULL"
    ]
    for sql in migrations:
        try:
            db.execute(sql)
        except Exception:
            pass

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

    # Seed Superadmin
    existing_sa = db.execute(
        "SELECT id FROM users WHERE role = 'superadmin' LIMIT 1"
    ).fetchone()

    if not existing_sa:
        from datetime import datetime, timezone
        sa_id = str(uuid.uuid4())
        hashed = pwd_context.hash(settings.SUPERADMIN_PASSWORD)
        db.execute("""
            INSERT INTO users (id, email, password_hash, role, credit_pool, is_active, created_at)
            VALUES (?, ?, ?, 'superadmin', 999999999, TRUE, ?)
        """, [sa_id, settings.SUPERADMIN_EMAIL, hashed, datetime.now(timezone.utc)])
        print(f"[BOOT] Superadmin created: {settings.SUPERADMIN_EMAIL} / {settings.SUPERADMIN_PASSWORD}")
        print(f"[BOOT] CHANGE THIS PASSWORD IMMEDIATELY after first login.")
