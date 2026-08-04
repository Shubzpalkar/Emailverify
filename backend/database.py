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
        firebase_uid VARCHAR UNIQUE,
        email VARCHAR UNIQUE NOT NULL,
        display_name VARCHAR,
        role VARCHAR DEFAULT 'user',
        plan VARCHAR DEFAULT 'Free',
        credits INTEGER DEFAULT 100,
        status VARCHAR DEFAULT 'Active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP,
        email_verified BOOLEAN DEFAULT FALSE,
        password_hash VARCHAR,
        credit_pool INTEGER DEFAULT 100,
        is_active BOOLEAN DEFAULT TRUE,
        tier VARCHAR DEFAULT 'free',
        company VARCHAR,
        phone VARCHAR,
        admin_id VARCHAR,
        created_by VARCHAR,
        custom_rate_limit INTEGER,
        workspace_id VARCHAR,
        department VARCHAR
    );
    """)
    
    db.execute("""
    CREATE TABLE IF NOT EXISTS workspaces (
        id VARCHAR PRIMARY KEY,
        company_name VARCHAR NOT NULL,
        workspace_slug VARCHAR UNIQUE NOT NULL,
        company_logo VARCHAR,
        industry VARCHAR,
        company_size VARCHAR,
        website VARCHAR,
        country VARCHAR,
        timezone VARCHAR,
        language VARCHAR DEFAULT 'en',
        plan VARCHAR DEFAULT 'Free',
        credits_remaining INTEGER DEFAULT 0,
        credits_used INTEGER DEFAULT 0,
        workspace_status VARCHAR DEFAULT 'Active',
        owner_user_id VARCHAR NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    db.execute("""
    CREATE TABLE IF NOT EXISTS api_keys (
        id VARCHAR PRIMARY KEY,
        user_id VARCHAR NOT NULL,
        name VARCHAR NOT NULL,
        key_hash VARCHAR NOT NULL,
        prefix VARCHAR NOT NULL,
        last_used TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        workspace_id VARCHAR
    );
    """)
    
    db.execute("""
    CREATE TABLE IF NOT EXISTS verification_jobs (
        id VARCHAR PRIMARY KEY,
        user_id VARCHAR NOT NULL,
        file_name VARCHAR,
        total_emails INTEGER DEFAULT 0,
        processed_emails INTEGER DEFAULT 0,
        status VARCHAR DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        workspace_id VARCHAR
    );
    """)
    
    db.execute("""
    CREATE TABLE IF NOT EXISTS verification_results (
        id VARCHAR PRIMARY KEY,
        job_id VARCHAR NOT NULL,
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
        user_id VARCHAR NOT NULL,
        credits_used INTEGER,
        job_id VARCHAR,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        workspace_id VARCHAR
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

    db.execute("""
    CREATE TABLE IF NOT EXISTS roles (
        id VARCHAR PRIMARY KEY,
        name VARCHAR UNIQUE NOT NULL,
        slug VARCHAR UNIQUE NOT NULL,
        description VARCHAR
    );
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS permissions (
        id VARCHAR PRIMARY KEY,
        key VARCHAR UNIQUE NOT NULL,
        description VARCHAR
    );
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS role_permissions (
        role_id VARCHAR,
        permission_id VARCHAR,
        PRIMARY KEY (role_id, permission_id)
    );
    """)

    # Billing & Subscription module tables
    db.execute("""
    CREATE TABLE IF NOT EXISTS plans (
        id VARCHAR PRIMARY KEY,
        name VARCHAR UNIQUE NOT NULL,
        price DOUBLE NOT NULL,
        credits INTEGER NOT NULL,
        max_upload_size INTEGER NOT NULL,
        api_access BOOLEAN DEFAULT FALSE,
        bulk_verification BOOLEAN DEFAULT TRUE,
        support_level VARCHAR NOT NULL,
        verification_speed VARCHAR DEFAULT 'normal',
        teams_allowed INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        id VARCHAR PRIMARY KEY,
        user_id VARCHAR NOT NULL,
        dodo_customer_id VARCHAR,
        dodo_subscription_id VARCHAR,
        plan_name VARCHAR NOT NULL,
        status VARCHAR NOT NULL,
        credits_allotted INTEGER,
        credits_used INTEGER DEFAULT 0,
        start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_date TIMESTAMP,
        auto_renew BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        workspace_id VARCHAR
    );
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id VARCHAR PRIMARY KEY,
        user_id VARCHAR NOT NULL,
        dodo_customer_id VARCHAR,
        subscription_id VARCHAR,
        checkout_session_id VARCHAR UNIQUE,
        transaction_id VARCHAR,
        payment_status VARCHAR NOT NULL,
        amount DOUBLE NOT NULL,
        currency VARCHAR DEFAULT 'INR',
        invoice_id VARCHAR,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        workspace_id VARCHAR
    );
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS payment_transactions (
        id VARCHAR PRIMARY KEY,
        payment_id VARCHAR,
        event_type VARCHAR,
        status VARCHAR,
        raw_payload VARCHAR,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS credit_transactions (
        id VARCHAR PRIMARY KEY,
        user_id VARCHAR NOT NULL,
        amount INTEGER NOT NULL,
        transaction_type VARCHAR NOT NULL,
        description VARCHAR,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        workspace_id VARCHAR
    );
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id VARCHAR PRIMARY KEY,
        user_id VARCHAR NOT NULL,
        payment_id VARCHAR,
        invoice_number VARCHAR UNIQUE NOT NULL,
        amount DOUBLE NOT NULL,
        tax DOUBLE DEFAULT 0.0,
        plan_name VARCHAR NOT NULL,
        status VARCHAR DEFAULT 'paid',
        billing_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        pdf_path VARCHAR,
        workspace_id VARCHAR
    );
    """)

    db.execute("""
    CREATE TABLE IF NOT EXISTS billing_history (
        id VARCHAR PRIMARY KEY,
        user_id VARCHAR NOT NULL,
        payment_id VARCHAR,
        plan_name VARCHAR NOT NULL,
        amount DOUBLE NOT NULL,
        currency VARCHAR DEFAULT 'INR',
        status VARCHAR NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        workspace_id VARCHAR
    );
    """)

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

    # Seed Default Plans
    plans_to_seed = [
        ("plan_free", "Free", 0.0, 100, 1000, False, True, "Community", "normal", 1),
        ("plan_starter", "Starter", 999.0, 50000, 100000, False, True, "Email", "normal", 1),
        ("plan_growth", "Growth", 4999.0, 500000, 1000000, True, True, "Priority", "fast", 3),
        ("plan_enterprise", "Enterprise", 99999.0, 10000000, 999999999, True, True, "Dedicated", "instant", 99)
    ]
    for pid, pname, pprice, pcredits, pmax_up, papi, pbulk, psupport, pspeed, pteams in plans_to_seed:
        try:
            db.execute("""
                INSERT INTO plans (id, name, price, credits, max_upload_size, api_access, bulk_verification, support_level, verification_speed, teams_allowed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [pid, pname, pprice, pcredits, pmax_up, papi, pbulk, psupport, pspeed, pteams])
        except Exception:
            # Plan already exists
            pass


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
        "ALTER TABLE users ADD COLUMN firebase_uid VARCHAR DEFAULT NULL",
        "ALTER TABLE users ADD COLUMN display_name VARCHAR DEFAULT NULL",
        "ALTER TABLE users ADD COLUMN plan VARCHAR DEFAULT 'Free'",
        "ALTER TABLE users ADD COLUMN status VARCHAR DEFAULT 'Active'",
        "ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE",
        "ALTER TABLE users ADD COLUMN admin_id VARCHAR DEFAULT NULL",
        "ALTER TABLE users ADD COLUMN credit_pool INTEGER DEFAULT 0",
        "ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE",
        "ALTER TABLE users ADD COLUMN created_by VARCHAR DEFAULT NULL",
        "ALTER TABLE users ADD COLUMN last_login TIMESTAMP DEFAULT NULL",
        "ALTER TABLE users ADD COLUMN custom_rate_limit INTEGER DEFAULT NULL",
        "ALTER TABLE users ADD COLUMN company VARCHAR DEFAULT NULL",
        "ALTER TABLE users ADD COLUMN phone VARCHAR DEFAULT NULL",
        "ALTER TABLE users ADD COLUMN workspace_id VARCHAR DEFAULT NULL",
        "ALTER TABLE api_keys ADD COLUMN workspace_id VARCHAR DEFAULT NULL",
        "ALTER TABLE verification_jobs ADD COLUMN workspace_id VARCHAR DEFAULT NULL",
        "ALTER TABLE credits_log ADD COLUMN workspace_id VARCHAR DEFAULT NULL",
        "ALTER TABLE subscriptions ADD COLUMN workspace_id VARCHAR DEFAULT NULL",
        "ALTER TABLE payments ADD COLUMN workspace_id VARCHAR DEFAULT NULL",
        "ALTER TABLE credit_transactions ADD COLUMN workspace_id VARCHAR DEFAULT NULL",
        "ALTER TABLE invoices ADD COLUMN workspace_id VARCHAR DEFAULT NULL",
        "ALTER TABLE billing_history ADD COLUMN workspace_id VARCHAR DEFAULT NULL",
        "CREATE INDEX IF NOT EXISTS idx_users_workspace ON users(workspace_id)",
        "CREATE INDEX IF NOT EXISTS idx_jobs_workspace ON verification_jobs(workspace_id)",
        "CREATE INDEX IF NOT EXISTS idx_api_keys_workspace ON api_keys(workspace_id)",
        "CREATE INDEX IF NOT EXISTS idx_credits_workspace ON credits_log(workspace_id)",
        "ALTER TABLE users ADD COLUMN role_id VARCHAR DEFAULT NULL",
        "ALTER TABLE users ADD COLUMN joined_at TIMESTAMP DEFAULT NULL"
    ]
    for sql in migrations:
        try:
            db.execute(sql)
        except Exception:
            pass

    try:
        db.execute("ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL")
    except Exception:
        pass

    try:
        db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_firebase_uid ON users(firebase_uid)")
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

    # RBAC SEEDING
    roles_data = [
        ("role_superadmin", "Super Admin", "superadmin", "Full system access"),
        ("role_companyadmin", "Company Admin", "admin", "Full workspace access"),
        ("role_manager", "Manager", "manager", "Manage team and operations"),
        ("role_teammember", "Team Member", "user", "Standard user access"),
        ("role_viewer", "Viewer", "viewer", "Read-only access")
    ]
    for rid, rname, rslug, rdesc in roles_data:
        try:
            db.execute("INSERT INTO roles (id, name, slug, description) VALUES (?, ?, ?, ?)", [rid, rname, rslug, rdesc])
        except Exception:
            pass

    perms_data = [
        "dashboard.view", "verification.bulk", "verification.single", "verification.download", "verification.history",
        "analytics.view", "team.view", "team.invite", "team.remove", "team.suspend", "team.change_role",
        "workspace.view", "workspace.update", "workspace.settings", "credits.view", "credits.manage",
        "api.view", "api.create", "api.revoke", "notifications.view", "notifications.manage",
        "audit.view", "billing.view", "billing.manage", "admin.view", "admin.manage"
    ]
    
    for p in perms_data:
        try:
            db.execute("INSERT INTO permissions (id, key, description) VALUES (?, ?, ?)", [f"perm_{p}", p, f"Permission for {p}"])
        except Exception:
            pass

    db.execute("DELETE FROM role_permissions")
    
    def add_role_perms(role_id, perms):
        for p in perms:
            db.execute("INSERT INTO role_permissions (role_id, permission_id) VALUES (?, ?)", [role_id, f"perm_{p}"])
            
    add_role_perms("role_superadmin", perms_data)
    add_role_perms("role_companyadmin", [p for p in perms_data if not p.startswith("admin.")])
    add_role_perms("role_manager", [
        "dashboard.view", "verification.bulk", "verification.single", "verification.download", "verification.history",
        "analytics.view", "team.view", "team.invite", "team.suspend", "workspace.view", "credits.view", "notifications.view", "notifications.manage"
    ])
    add_role_perms("role_teammember", [
        "dashboard.view", "verification.bulk", "verification.single", "verification.download", "verification.history",
        "analytics.view", "team.view", "workspace.view", "credits.view", "api.view", "notifications.view"
    ])
    add_role_perms("role_viewer", [
        "dashboard.view", "verification.history", "analytics.view", "team.view", "workspace.view", "credits.view", "api.view", "notifications.view"
    ])

    try:
        db.execute("UPDATE users SET role_id = 'role_superadmin' WHERE role = 'superadmin' AND role_id IS NULL")
        db.execute("UPDATE users SET role_id = 'role_companyadmin' WHERE role = 'admin' AND role_id IS NULL")
        db.execute("UPDATE users SET role_id = 'role_teammember' WHERE role = 'user' AND role_id IS NULL")
        db.execute("UPDATE users SET joined_at = created_at WHERE joined_at IS NULL")
    except Exception:
        pass
