from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File
from pydantic import BaseModel, EmailStr
from typing import List
import uuid
import pandas as pd
import io

from auth import get_current_user, UserResponse
from engine import verify_single_email
from database import get_db
from worker import background_worker

router = APIRouter(prefix="/api/verify", tags=["verify"])
job_router = APIRouter(prefix="/api/jobs", tags=["jobs"])

class VerifyRequest(BaseModel):
    email: EmailStr

@router.post("")
async def verify_email_api(req: VerifyRequest, current_user: UserResponse = Depends(get_current_user)):
    db = get_db()
    # Check credits
    if current_user.credits < 1:
        raise HTTPException(status_code=402, detail="Insufficient credits")
        
    # Deduct credit
    db.execute("UPDATE users SET credits = credits - 1 WHERE id = ?", [current_user.id])
    db.execute("INSERT INTO credits_log (id, user_id, credits_used) VALUES (?, ?, ?)", [str(uuid.uuid4()), current_user.id, 1])
    
    # Process
    result = await verify_single_email(req.email)
    
    # Note: we may optionally log single request results in a lightweight table or directly in results if we link a dummy job.
    return result

@job_router.post("/upload")
async def upload_list(background_tasks: BackgroundTasks, file: UploadFile = File(...), current_user: UserResponse = Depends(get_current_user)):
    # Read file content
    contents = await file.read()
    
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(io.BytesIO(contents))
        elif file.filename.endswith('.txt'):
            df = pd.read_csv(io.BytesIO(contents), header=None, names=["email"])
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing file: {str(e)}")

    # Try to find email column
    email_col = None
    for col in df.columns:
        if 'email' in str(col).lower():
            email_col = col
            break
            
    if not email_col:
        # Assume first column if no header named email
        email_col = df.columns[0]
        
    # Extract unique emails
    emails = df[email_col].dropna().astype(str).str.strip().unique().tolist()
    
    if not emails:
        raise HTTPException(status_code=400, detail="No emails found in file")
        
    # Check limits
    if len(emails) > 5_000_000:
        raise HTTPException(status_code=400, detail="Maximum 5,000,000 emails per job exceeded")
        
    # Check credits
    if current_user.credits < len(emails):
        raise HTTPException(status_code=402, detail=f"Insufficient credits. Required: {len(emails)}, Available: {current_user.credits}")
        
    db = get_db()
    
    # Deduct credits
    db.execute("UPDATE users SET credits = credits - ? WHERE id = ?", [len(emails), current_user.id])
    
    # Create Job
    job_id = str(uuid.uuid4())
    db.execute("""
    INSERT INTO verification_jobs (id, user_id, file_name, total_emails) 
    VALUES (?, ?, ?, ?)
    """, [job_id, current_user.id, file.filename, len(emails)])
    
    db.execute("INSERT INTO credits_log (id, user_id, credits_used, job_id) VALUES (?, ?, ?, ?)", [str(uuid.uuid4()), current_user.id, len(emails), job_id])
    
    # Start background task
    background_tasks.add_task(background_worker, job_id, emails)
    
    return {"message": "Job created", "job_id": job_id, "total_emails": len(emails)}

@job_router.get("/{job_id}")
async def get_job_status(job_id: str, current_user: UserResponse = Depends(get_current_user)):
    db = get_db()
    job = db.execute("SELECT id, file_name, total_emails, processed_emails, status, created_at, completed_at FROM verification_jobs WHERE id = ? AND user_id = ?", [job_id, current_user.id]).fetchone()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return {
        "job_id": job[0],
        "file_name": job[1],
        "total_emails": job[2],
        "processed_emails": job[3],
        "status": job[4],
        "created_at": job[5],
        "completed_at": job[6],
        "progress_percentage": round(job[3] / job[2] * 100, 2) if job[2] > 0 else 0
    }

from fastapi.responses import StreamingResponse

@job_router.get("/{job_id}/results")
async def get_job_results_stats(job_id: str, current_user: UserResponse = Depends(get_current_user)):
    # Verify owner
    db = get_db()
    job = db.execute("SELECT id FROM verification_jobs WHERE id = ? AND user_id = ?", [job_id, current_user.id]).fetchone()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    # Get stats
    stats = db.execute("""
        SELECT status, COUNT(*) as count 
        FROM verification_results 
        WHERE job_id = ? 
        GROUP BY status
    """, [job_id]).fetchall()
    
    return {row[0]: row[1] for row in stats}

@job_router.get("/{job_id}/export")
async def export_job_results(job_id: str, format: str = "csv", current_user: UserResponse = Depends(get_current_user)):
    db = get_db()
    job = db.execute("SELECT file_name FROM verification_jobs WHERE id = ? AND user_id = ?", [job_id, current_user.id]).fetchone()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    # Stream query
    query = f"SELECT email, status, domain, is_role, is_disposable, smtp_result FROM verification_results WHERE job_id = '{job_id}'"
    df = db.execute(query).df()
    
    stream = io.StringIO()
    df.to_csv(stream, index=False)
    
    response = StreamingResponse(iter([stream.getvalue()]),
                                 media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename=results_{job_id}.csv"
    return response

# --- Dashboard & Admin Routes ---

dashboard_router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@dashboard_router.get("/metrics")
async def get_dashboard_metrics(current_user: UserResponse = Depends(get_current_user)):
    db = get_db()
    jobs = db.execute("SELECT id, file_name, total_emails, processed_emails, status, created_at FROM verification_jobs WHERE user_id = ? ORDER BY created_at DESC LIMIT 10", [current_user.id]).fetchall()
    
    total_verified = db.execute("SELECT COALESCE(SUM(processed_emails), 0) FROM verification_jobs WHERE user_id = ?", [current_user.id]).fetchone()[0]
    
    jobs_list = []
    for j in jobs:
        jobs_list.append({
            "id": j[0],
            "file_name": j[1],
            "total_emails": j[2],
            "processed_emails": j[3],
            "status": j[4],
            "created_at": j[5],
            "progress_percentage": round(j[3] / j[2] * 100, 2) if j[2] > 0 else 0
        })
        
    return {
        "credits": current_user.credits,
        "total_verified": total_verified,
        "recent_jobs": jobs_list
    }

admin_router = APIRouter(prefix="/api/admin", tags=["admin"])

def require_admin(current_user: UserResponse = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

@admin_router.get("/users")
async def get_all_users(admin: UserResponse = Depends(require_admin)):
    db = get_db()
    cols = "id, email, credits, role, created_at"
    users = db.execute(f"SELECT {cols} FROM users ORDER BY created_at DESC").fetchall()
    return [{"id": u[0], "email": u[1], "credits": u[2], "role": u[3], "created_at": u[4]} for u in users]

@admin_router.post("/users/{user_id}/credits")
async def add_credits(user_id: str, amount: int, admin: UserResponse = Depends(require_admin)):
    db = get_db()
    db.execute("UPDATE users SET credits = credits + ? WHERE id = ?", [amount, user_id])
    return {"message": f"Added {amount} credits to user {user_id}"}


@admin_router.post("/users/{user_id}/tier")
async def set_user_tier(
    user_id: str,
    tier: str,
    admin: UserResponse = Depends(require_admin)
):
    from database import get_db_write_lock
    if tier not in ("free", "standard", "power", "enterprise"):
        raise HTTPException(status_code=400, detail="Invalid tier")
    db = get_db()
    async with get_db_write_lock():
        db.execute("UPDATE users SET tier = ? WHERE id = ?", [tier, user_id])
    return {"message": f"User {user_id} tier set to {tier}"}
