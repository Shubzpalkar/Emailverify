import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Email Verification Portal"
    SUPERADMIN_EMAIL: str = "superadmin@system.local"
    SUPERADMIN_PASSWORD: str = "SuperAdmin@123"
    DATABASE_PATH: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "email_verifier.db")
    SECRET_KEY: str = "super_secret_key_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    
    # Verification Limits
    MAX_FILE_SIZE_MB: int = 500
    MAX_EMAILS_PER_JOB: int = 5_000_000
    
    # --- Concurrency & rate limiting ---
    GLOBAL_RATE_PER_MIN: int = 5000          # was 100 — raise the default
    GLOBAL_MAX_CONCURRENT: int = 500         # max asyncio coroutines alive at once
    PER_DOMAIN_CONCURRENT: int = 10          # max concurrent per domain (Exchange allows 20, stay at 10)

    # --- Per-user tier rate allocations (verifications/min) ---
    RATE_TIER_FREE: int = 200
    RATE_TIER_STANDARD: int = 1000
    RATE_TIER_POWER: int = 2500
    RATE_TIER_ENTERPRISE: int = 5000

    # --- Per-domain-type concurrent caps ---
    CONCURRENT_EXCHANGE_ONLINE: int = 10
    CONCURRENT_EXCHANGE_ONPREM: int = 10
    CONCURRENT_GATEWAY: int = 3              # Mimecast/Proofpoint — just need 1 to detect catch-all
    CONCURRENT_GOOGLE_WORKSPACE: int = 5
    CONCURRENT_POSTFIX_OTHER: int = 15       # most permissive — default Postfix has no limit

    # --- SMTP timeouts (seconds) ---
    SMTP_CONNECT_TIMEOUT: int = 10
    SMTP_COMMAND_TIMEOUT: int = 8
    SMTP_HARD_TIMEOUT: int = 30              # asyncio.wait_for wrapper around full handshake

    # --- DNS ---
    DNS_RESOLVERS: list = ["8.8.8.8", "1.1.1.1", "8.8.4.4", "1.0.0.1"]
    DNS_LOOKUP_TIMEOUT: int = 8
    DNS_MAX_CONCURRENT_PREFETCH: int = 100   # parallel DNS lookups during job pre-scan

    # --- DuckDB batch writing ---
    DB_WRITE_BATCH_SIZE: int = 500           # buffer this many results before one executemany
    DB_FLUSH_INTERVAL_SECS: int = 5         # flush buffer every N seconds regardless of size

    # --- Cache TTLs (seconds) ---
    EMAIL_CACHE_TTL: int = 604800            # 7 days
    DOMAIN_INTELLIGENCE_TTL: int = 86400    # 24 hours
    
    # --- Retry Config ---
    RETRY_DELAYS: list = [5, 30, 120]
    
    # Worker configuration
    CONCURRENT_WORKERS: int = 20
    
    # Download configuration
    DOWNLOAD_CHUNK_SIZE: int = 1000  # rows fetched per DuckDB chunk
    
    # SMTP Email Configuration
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_SENDER: str = "noreply@system.local"
    SMTP_USE_TLS: bool = False
    
    class Config:
        env_file = ".env"

settings = Settings()
