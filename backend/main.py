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

logger = logging.getLogger("api_errors")

from database import get_db, init_db
from config import settings
from auth import router as auth_router
from worker import _flush_result_buffer

async def _periodic_flush():
    while True:
        await asyncio.sleep(settings.DB_FLUSH_INTERVAL_SECS)
        db = get_db()
        await _flush_result_buffer(db)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the DuckDB database
    init_db()
    print("Database initialized")
    
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
from routes import router as verify_router, job_router, dashboard_router, admin_router, superadmin_router, api_keys_router
app.include_router(verify_router)
app.include_router(job_router)
app.include_router(dashboard_router)
app.include_router(admin_router)
app.include_router(superadmin_router)
app.include_router(api_keys_router)

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
