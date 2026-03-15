import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Email Verification Portal"
    DATABASE_PATH: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "email_verifier.db")
    SECRET_KEY: str = "super_secret_key_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    
    # Verification Limits
    MAX_FILE_SIZE_MB: int = 500
    MAX_EMAILS_PER_JOB: int = 5_000_000
    
    # Worker configuration
    CONCURRENT_WORKERS: int = 20
    
    class Config:
        env_file = ".env"

settings = Settings()
