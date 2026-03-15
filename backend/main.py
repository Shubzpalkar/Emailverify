from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import logging

# Configure logging so verification logs show in terminal
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)

from database import get_db, init_db
from config import settings
from auth import router as auth_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the DuckDB database
    init_db()
    print("Database initialized")
    yield
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
from routes import router as verify_router, job_router, dashboard_router, admin_router
app.include_router(verify_router)
app.include_router(job_router)
app.include_router(dashboard_router)
app.include_router(admin_router)

# Healthcheck
@app.get("/api/health")
def healthcheck():
    return {"status": "healthy"}
