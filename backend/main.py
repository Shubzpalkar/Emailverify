import asyncio
try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import logging

# Configure logging so verification logs show in terminal
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)

logging.getLogger("watchfiles").setLevel(logging.WARNING)
logging.getLogger("watchfiles.main").setLevel(logging.WARNING)

logger = logging.getLogger("api_errors")

from database import get_db, init_db
from config import settings
from auth import router as auth_router
from firebase.firebase import initialize_firebase
from worker import _flush_result_buffer

async def _periodic_flush():
    while True:
        await asyncio.sleep(settings.DB_FLUSH_INTERVAL_SECS)
        db = get_db()
        await _flush_result_buffer(db)

def seed_superadmin_in_firebase():
    from firebase_admin import auth as firebase_admin_auth
    from database import get_db
    
    email = settings.SUPERADMIN_EMAIL
    password = settings.SUPERADMIN_PASSWORD
    
    try:
        try:
            fb_user = firebase_admin_auth.get_user_by_email(email)
            print(f"[BOOT] Superadmin already exists in Firebase Auth: {fb_user.uid}")
            fb_uid = fb_user.uid
        except firebase_admin_auth.UserNotFoundError:
            print(f"[BOOT] Creating superadmin in Firebase Auth...")
            fb_user = firebase_admin_auth.create_user(
                email=email,
                password=password,
                email_verified=True,
                display_name="Super Admin"
            )
            fb_uid = fb_user.uid
            print(f"[BOOT] Created superadmin in Firebase Auth: {fb_uid}")
            
        db = get_db()
        row = db.execute("SELECT id, firebase_uid FROM users WHERE lower(email) = lower(?)", [email]).fetchone()
        if row:
            db_id, current_fb_uid = row
            if current_fb_uid != fb_uid:
                db.execute("UPDATE users SET firebase_uid = ? WHERE id = ?", [fb_uid, db_id])
                print(f"[BOOT] Linked superadmin in DuckDB with Firebase UID: {fb_uid}")
        else:
            import uuid
            from datetime import datetime, timezone
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
            hashed = pwd_context.hash(password)
            db_id = str(uuid.uuid4())
            db.execute("""
                INSERT INTO users (id, firebase_uid, email, password_hash, role, credit_pool, is_active, created_at, email_verified)
                VALUES (?, ?, ?, ?, 'superadmin', 999999999, TRUE, ?, TRUE)
            """, [db_id, fb_uid, email, hashed, datetime.now(timezone.utc)])
            print(f"[BOOT] Created and linked superadmin in DuckDB: {fb_uid}")
            
    except Exception as e:
        print(f"[BOOT] Error seeding superadmin in Firebase: {e}")

def cleanup_stuck_jobs():
    try:
        db = get_db()
        db.execute("""
            UPDATE verification_jobs 
            SET status = 'cancelled', completed_at = CURRENT_TIMESTAMP 
            WHERE status IN ('processing', 'pending')
        """)
        print("[BOOT] Cleared orphaned / interrupted jobs from database")
    except Exception as e:
        print(f"[BOOT] Warning during orphan job cleanup: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the DuckDB database
    init_db()
    print("Database initialized")
    initialize_firebase()
    seed_superadmin_in_firebase()
    cleanup_stuck_jobs()
    
    flush_task = asyncio.create_task(_periodic_flush())

    
    logger = logging.getLogger("verifier.startup")
    logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info(f"🚀 Email Verifier starting up")
    logger.info(f"   Global rate  : {settings.GLOBAL_RATE_PER_MIN}/min")
    logger.info(f"   Max concurrent: {settings.GLOBAL_MAX_CONCURRENT} coroutines")
    logger.info(f"   Per-domain cap: {settings.PER_DOMAIN_CONCURRENT}")
    logger.info(f"   DB batch size : {settings.DB_WRITE_BATCH_SIZE}")
    logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    yield
    
    flush_task.cancel()
    # Cleanup code if necessary
    db = get_db()
    db.close()
    print("Database connection closed")

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
from routes.verify import router as verify_router, job_router, dashboard_router, admin_router, superadmin_router, api_keys_router
from routes.account import router as account_router
from billing import router as billing_router

app.include_router(verify_router)
app.include_router(job_router)
app.include_router(dashboard_router)
app.include_router(admin_router)
app.include_router(superadmin_router)
app.include_router(api_keys_router)
app.include_router(billing_router)
app.include_router(account_router)


# Healthcheck
@app.get("/api/health")
def healthcheck():
    return {"status": "healthy"}

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_details = exc.errors()
    logger.error(f"Validation error for {request.method} {request.url.path}: {error_details}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": error_details, "body": exc.body},
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
