from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import uuid
import pandas as pd
import io
import csv
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from datetime import datetime, timezone, timedelta

from auth import (
    get_current_user, UserResponse, require_superadmin, require_admin, require_user, 
    get_password_hash, create_access_token, get_api_user
)
from middleware.rbac import require_permission
from config import settings
from engine import verify_single_email
from database import get_db, get_db_write_lock
from worker import background_worker
import secrets
import hashlib

router = APIRouter(prefix="/api/verify", tags=["verify"])
job_router = APIRouter(prefix="/api/jobs", tags=["jobs"])
dashboard_router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])
admin_router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])
superadmin_router = APIRouter(prefix="/api/superadmin", tags=["superadmin"], dependencies=[Depends(require_superadmin)])

class VerifyRequest(BaseModel):
    email: str

@router.post("")
async def verify_email_api(req: VerifyRequest, current_user: UserResponse = Depends(require_permission("verification.single"))):
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Account suspended")
    db = get_db()
    
    if current_user.credit_pool < 1:
        raise HTTPException(status_code=402, detail="Insufficient credits")
        
    db.execute("UPDATE users SET credit_pool = credit_pool - 1 WHERE id = ?", [current_user.id])
    db.execute("INSERT INTO credits_log (id, user_id, credits_used) VALUES (?, ?, ?)", [str(uuid.uuid4()), current_user.id, 1])
    
    result = await verify_single_email(req.email)
    return result

@job_router.post("/upload")
async def upload_list(background_tasks: BackgroundTasks, file: UploadFile = File(...), current_user: UserResponse = Depends(require_permission("verification.bulk"))):
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Account suspended")
        
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

    email_col = None
    for col in df.columns:
        if 'email' in str(col).lower():
            email_col = col
            break
            
    if not email_col:
        email_col = df.columns[0]
        
    emails = df[email_col].dropna().astype(str).str.strip().unique().tolist()
    
    if not emails:
        raise HTTPException(status_code=400, detail="No emails found in file")
        
    if len(emails) > 5_000_000:
        raise HTTPException(status_code=400, detail="Maximum 5,000,000 emails per job exceeded")
        
    if current_user.credit_pool < len(emails):
        raise HTTPException(status_code=402, detail=f"Insufficient credits. Required: {len(emails)}, Available: {current_user.credit_pool}")
        
    db = get_db()
    
    # Do NOT deduct credits here, worker.py now handles the deduction on completion, as instructed.
    
    job_id = str(uuid.uuid4())
    db.execute("""
    INSERT INTO verification_jobs (id, user_id, file_name, total_emails) 
    VALUES (?, ?, ?, ?)
    """, [job_id, current_user.id, file.filename, len(emails)])
    
    db.execute("INSERT INTO credits_log (id, user_id, credits_used, job_id) VALUES (?, ?, ?, ?)", [str(uuid.uuid4()), current_user.id, len(emails), job_id])
    
    background_tasks.add_task(background_worker, job_id, emails)
    
    return {"message": "Job created", "job_id": job_id, "total_emails": len(emails)}

def _get_job_with_auth(db, job_id: str, user: UserResponse):
    if user.role == "superadmin":
        job = db.execute("SELECT id, file_name, total_emails, processed_emails, status, created_at, completed_at FROM verification_jobs WHERE id = ?", [job_id]).fetchone()
    elif user.role == "admin":
        job = db.execute("""
            SELECT j.id, j.file_name, j.total_emails, j.processed_emails, j.status, j.created_at, j.completed_at 
            FROM verification_jobs j JOIN users u ON j.user_id = u.id 
            WHERE j.id = ? AND (u.admin_id = ? OR j.user_id = ?)
        """, [job_id, user.id, user.id]).fetchone()
    else:
        job = db.execute("SELECT id, file_name, total_emails, processed_emails, status, created_at, completed_at FROM verification_jobs WHERE id = ? AND user_id = ?", [job_id, user.id]).fetchone()
    return job

@job_router.get("/{job_id}")
async def get_job_status(job_id: str, current_user: UserResponse = Depends(require_permission("verification.history"))):
    db = get_db()
    job = _get_job_with_auth(db, job_id, current_user)
    
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

@job_router.get("/{job_id}/results")
async def get_job_results_stats(job_id: str, current_user: UserResponse = Depends(require_permission("verification.history"))):
    db = get_db()
    job = _get_job_with_auth(db, job_id, current_user)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    stats = db.execute("""
        SELECT status, COUNT(*) as count 
        FROM verification_results 
        WHERE job_id = ? 
        GROUP BY status
    """, [job_id]).fetchall()
    
    return {row[0]: row[1] for row in stats}

@job_router.post("/{job_id}/cancel")
async def cancel_job(job_id: str, current_user: UserResponse = Depends(require_permission("verification.bulk"))):
    db = get_db()
    job = _get_job_with_auth(db, job_id, current_user)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    from worker import cancel_running_job
    cancel_running_job(job_id)

    db.execute("UPDATE verification_jobs SET status = 'cancelled', completed_at = CURRENT_TIMESTAMP WHERE id = ?", [job_id])
    return {"status": "cancelled", "message": "Job cancelled successfully"}

# --- DOWNLOAD ROUTES & HELPERS ---

ALL_EXPORT_COLUMNS = ["email", "status", "domain", "is_role", "is_disposable", "smtp_result", "created_at"]

def _verify_job_ownership(job_id: str, current_user: UserResponse, db):
    """Raise 404 if job does not exist or does not belong to this user."""
    if current_user.role == "superadmin":
        job = db.execute(
            "SELECT id FROM verification_jobs WHERE id = ?", [job_id]
        ).fetchone()
    elif current_user.role == "admin":
        # Admin can download any job from their users
        job = db.execute("""
            SELECT vj.id FROM verification_jobs vj
            JOIN users u ON vj.user_id = u.id
            WHERE vj.id = ? AND (u.admin_id = ? OR vj.user_id = ?)
        """, [job_id, current_user.id, current_user.id]).fetchone()
    else:
        # User can only download their own jobs
        job = db.execute(
            "SELECT id FROM verification_jobs WHERE id = ? AND user_id = ?",
            [job_id, current_user.id]
        ).fetchone()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")


def _parse_columns(columns_param: Optional[str], all_cols: list) -> list:
    """Parse and validate requested columns. Return subset of all_cols in correct order."""
    if not columns_param:
        return all_cols
    requested = [c.strip() for c in columns_param.split(",")]
    # Preserve order from ALL_COLUMNS, ignore unknown column names
    valid = [c for c in all_cols if c in requested]
    # Always include email as first column if not explicitly excluded or if nothing valid selected
    if "email" not in valid:
        valid.insert(0, "email")
    return valid


def _parse_statuses(statuses_param: Optional[str]) -> Optional[list]:
    """Parse status filter. Returns None meaning no filter (all statuses)."""
    valid_statuses = {"valid", "invalid", "risky", "catch_all", "disposable", "role_based", "unknown"}
    if not statuses_param:
        return None
    requested = [s.strip().lower() for s in statuses_param.split(",")]
    filtered = [s for s in requested if s in valid_statuses]
    return filtered if filtered else None


def _fetch_chunk(db, job_id: str, columns: list, status_filter: Optional[list],
                 offset: int) -> list:
    """Fetch one chunk of rows from DuckDB. Returns list of tuples."""
    col_sql = ", ".join(columns)

    if status_filter:
        placeholders = ", ".join(["?" for _ in status_filter])
        query = f"""
            SELECT {col_sql}
            FROM verification_results
            WHERE job_id = ?
              AND status IN ({placeholders})
            ORDER BY rowid
            LIMIT {settings.DOWNLOAD_CHUNK_SIZE}
            OFFSET ?
        """
        params = [job_id] + status_filter + [offset]
    else:
        query = f"""
            SELECT {col_sql}
            FROM verification_results
            WHERE job_id = ?
            ORDER BY rowid
            LIMIT {settings.DOWNLOAD_CHUNK_SIZE}
            OFFSET ?
        """
        params = [job_id, offset]

    return db.execute(query, params).fetchall()


@job_router.get("/{job_id}/download/count")
async def download_count(
    job_id: str,
    statuses: Optional[str] = Query(None),
    current_user: UserResponse = Depends(require_permission("verification.download")),
    db = Depends(get_db)
):
    _verify_job_ownership(job_id, current_user, db)
    status_filter = _parse_statuses(statuses)

    # Always get full breakdown by status
    rows = db.execute("""
        SELECT status, COUNT(*) as cnt
        FROM verification_results
        WHERE job_id = ?
        GROUP BY status
        ORDER BY cnt DESC
    """, [job_id]).fetchall()

    by_status = {row[0]: row[1] for row in rows}
    all_statuses = {"valid", "invalid", "risky", "catch_all", "disposable", "role_based", "unknown"}
    for s in all_statuses:
        by_status.setdefault(s, 0)

    if status_filter:
        total = sum(by_status.get(s, 0) for s in status_filter)
    else:
        total = sum(by_status.values())

    return {"total": total, "by_status": by_status}


@job_router.get("/{job_id}/download/csv")
async def download_csv(
    job_id: str,
    statuses: Optional[str] = Query(None),
    columns: Optional[str] = Query(None),
    current_user: UserResponse = Depends(require_permission("verification.download")),
    db = Depends(get_db)
):
    _verify_job_ownership(job_id, current_user, db)
    requested_cols = _parse_columns(columns, ALL_EXPORT_COLUMNS)
    status_filter = _parse_statuses(statuses)

    job_row = db.execute(
        "SELECT file_name FROM verification_jobs WHERE id = ?", [job_id]
    ).fetchone()
    original_name = job_row[0].rsplit(".", 1)[0] if job_row else job_id
    download_filename = f"{original_name}_verified.csv"

    def csv_stream():
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([c.replace("_", " ").title() for c in requested_cols])
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)

        offset = 0
        while True:
            rows = _fetch_chunk(db, job_id, requested_cols, status_filter, offset)
            if not rows:
                break
            for row in rows:
                writer.writerow(row)
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)
            offset += settings.DOWNLOAD_CHUNK_SIZE

    return StreamingResponse(
        csv_stream(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{download_filename}"',
            "X-Accel-Buffering": "no",
        }
    )


@job_router.get("/{job_id}/download/xlsx")
async def download_xlsx(
    job_id: str,
    statuses: Optional[str] = Query(None),
    columns: Optional[str] = Query(None),
    current_user: UserResponse = Depends(require_permission("verification.download")),
    db = Depends(get_db)
):
    _verify_job_ownership(job_id, current_user, db)
    requested_cols = _parse_columns(columns, ALL_EXPORT_COLUMNS)
    status_filter = _parse_statuses(statuses)

    job_row = db.execute(
        "SELECT file_name FROM verification_jobs WHERE id = ?", [job_id]
    ).fetchone()
    original_name = job_row[0].rsplit(".", 1)[0] if job_row else job_id
    download_filename = f"{original_name}_verified.xlsx"

    def xlsx_stream():
        wb = openpyxl.Workbook(write_only=True)
        ws = wb.create_sheet("Results")

        header_font = Font(bold=True, shadow=None) # White color removed for simplicity as fill isn't set yet
        # Re-adding styles as per prompt
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1D9E75", end_color="1D9E75", fill_type="solid")
        
        header_row = []
        for col in requested_cols:
            cell = openpyxl.cell.WriteOnlyCell(ws, value=col.replace("_", " ").title())
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")
            header_row.append(cell)
        ws.append(header_row)

        STATUS_COLORS = {
            "valid":       "4CAF82",
            "invalid":     "E8707A",
            "risky":       "F5A623",
            "catch_all":   "7B8FD4",
            "disposable":  "B0A0E0",
            "role_based":  "85C1E9",
            "unknown":     "C8C8C8",
        }
        status_col_idx = requested_cols.index("status") if "status" in requested_cols else None

        offset = 0
        while True:
            rows = _fetch_chunk(db, job_id, requested_cols, status_filter, offset)
            if not rows:
                break
            for row in rows:
                cells = []
                for i, val in enumerate(row):
                    cell = openpyxl.cell.WriteOnlyCell(ws, value=val)
                    if i == status_col_idx and val in STATUS_COLORS:
                        cell.fill = PatternFill(
                            start_color=STATUS_COLORS[val],
                            end_color=STATUS_COLORS[val],
                            fill_type="solid"
                        )
                        cell.font = Font(color="FFFFFF", bold=True)
                    cells.append(cell)
                ws.append(cells)
            offset += settings.DOWNLOAD_CHUNK_SIZE

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        yield buffer.read()

    return StreamingResponse(
        xlsx_stream(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{download_filename}"',
            "X-Accel-Buffering": "no",
        }
    )

@dashboard_router.get("/metrics")
async def get_dashboard_metrics(current_user: UserResponse = Depends(require_permission("dashboard.view"))):
    db = get_db()
    jobs = db.execute("SELECT id, file_name, total_emails, processed_emails, status, created_at FROM verification_jobs WHERE user_id = ? ORDER BY created_at DESC LIMIT 10", [current_user.id]).fetchall()
    
    total_verified = db.execute("SELECT COALESCE(SUM(processed_emails), 0) FROM verification_jobs WHERE user_id = ?", [current_user.id]).fetchone()[0]
    
    jobs_list = []
    for j in jobs:
        # Fetch counts for this job to support the download modal
        stats_rows = db.execute("""
            SELECT status, COUNT(*) as cnt
            FROM verification_results
            WHERE job_id = ?
            GROUP BY status
        """, [j[0]]).fetchall()
        counts = {row[0]: row[1] for row in stats_rows}
        
        # Ensure all possible statuses are present in counts
        all_statuses = {"valid", "invalid", "risky", "catch_all", "disposable", "role_based", "unknown"}
        for s in all_statuses:
            counts.setdefault(s, 0)

        actual_processed = max(j[3], sum(counts.values()))

        jobs_list.append({
            "id": j[0],
            "file_name": j[1],
            "total_emails": j[2],
            "processed_emails": actual_processed,
            "status": j[4],
            "created_at": j[5],
            "progress_percentage": round(actual_processed / j[2] * 100, 2) if j[2] > 0 else 0,
            "counts": counts
        })
        
    return {
        "credit_pool": current_user.credit_pool,
        "total_verified": total_verified,
        "recent_jobs": jobs_list
    }

# --- SUPERADMIN ROUTES ---

class AdminCreate(BaseModel):
    email: EmailStr
    password: str
    credit_pool: int

class AdminRateLimit(BaseModel):
    rate_per_min: int
    
class CreditUpdate(BaseModel):
    amount: int

class TierUpdate(BaseModel):
    tier: str

@superadmin_router.get("/dashboard")
async def sa_dashboard():
    db = get_db()
    total_admins = db.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'").fetchone()[0]
    total_users = db.execute("SELECT COUNT(*) FROM users WHERE role = 'user'").fetchone()[0]
    total_jobs = db.execute("SELECT COUNT(*) FROM verification_jobs").fetchone()[0]
    total_credits = db.execute("SELECT COALESCE(SUM(credit_pool), 0) FROM users WHERE role = 'admin'").fetchone()[0]
    
    stats = db.execute("SELECT status, COUNT(*) FROM verification_results GROUP BY status").fetchall()
    verification_counts = {row[0]: row[1] for row in stats}
    
    return {
        "total_admins": total_admins,
        "total_users": total_users,
        "total_jobs": total_jobs,
        "total_credits_allocated": total_credits,
        "verification_counts": verification_counts
    }

@superadmin_router.get("/admins")
async def sa_get_admins():
    db = get_db()
    cols = "id, email, is_active, credit_pool, created_at, last_login"
    admins = db.execute(f"SELECT {cols} FROM users WHERE role = 'admin'").fetchall()
    result = []
    for a in admins:
        users_cnt = db.execute("SELECT COUNT(*) FROM users WHERE admin_id = ?", [a[0]]).fetchone()[0]
        jobs_cnt = db.execute("SELECT COUNT(*) FROM verification_jobs j JOIN users u ON j.user_id = u.id WHERE u.admin_id = ? OR j.user_id = ?", [a[0], a[0]]).fetchone()[0]
        credits_used = db.execute("SELECT COALESCE(SUM(credit_pool), 0) FROM users WHERE admin_id = ?", [a[0]]).fetchone()[0]
        result.append({
            "id": a[0], "email": a[1], "is_active": a[2], "credit_pool": a[3],
            "credits_used": credits_used, "user_count": users_cnt, "job_count": jobs_cnt,
            "created_at": a[4], "last_login": a[5]
        })
    return result

@superadmin_router.post("/admins")
async def sa_create_admin(data: AdminCreate, request_user: UserResponse = Depends(require_superadmin)):
    db = get_db()
    if db.execute("SELECT id FROM users WHERE email = ?", [data.email]).fetchone():
        raise HTTPException(status_code=400, detail="Email already exists")
    firebase_user = _ensure_firebase_user(str(data.email), data.password, str(data.email))
    admin_id = str(uuid.uuid4())
    db.execute("""
        INSERT INTO users (id, firebase_uid, email, display_name, role, plan, credits, credit_pool, status, created_by, is_active, email_verified)
        VALUES (?, ?, ?, ?, 'admin', 'Free', ?, ?, 'Active', ?, TRUE, FALSE)
    """, [admin_id, firebase_user.uid, data.email, firebase_user.display_name, data.credit_pool, data.credit_pool, request_user.id])
    return {"message": "Admin created", "id": admin_id}

@superadmin_router.patch("/admins/{admin_id}/credits")
async def sa_update_admin_credits(admin_id: str, data: CreditUpdate):
    db = get_db()
    admin_row = db.execute("SELECT credit_pool FROM users WHERE id = ? AND role = 'admin'", [admin_id]).fetchone()
    if not admin_row:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    credits_given_to_users = db.execute("SELECT COALESCE(SUM(credit_pool), 0) FROM users WHERE admin_id = ?", [admin_id]).fetchone()[0]
    new_pool = admin_row[0] + data.amount
    if new_pool < credits_given_to_users:
        raise HTTPException(400, "Cannot reduce pool below already-allocated user credits")
        
    db.execute("UPDATE users SET credit_pool = ? WHERE id = ?", [new_pool, admin_id])
    return {"message": "Credits updated"}

@superadmin_router.patch("/admins/{admin_id}/suspend")
async def sa_suspend_admin(admin_id: str):
    db = get_db()
    admin = db.execute("SELECT is_active FROM users WHERE id = ? AND role = 'admin'", [admin_id]).fetchone()
    if not admin:
        raise HTTPException(404, "Admin not found")
    new_status = not admin[0]
    db.execute("UPDATE users SET is_active = ? WHERE id = ?", [new_status, admin_id])
    if not new_status:
        db.execute("UPDATE users SET is_active = FALSE WHERE admin_id = ?", [admin_id])
    return {"message": "Suspension toggled"}

@superadmin_router.patch("/admins/{admin_id}/rate-limit")
async def sa_rate_limit(admin_id: str, data: AdminRateLimit):
    db = get_db()
    db.execute("UPDATE users SET custom_rate_limit = ? WHERE id = ?", [data.rate_per_min, admin_id])
    return {"message": "Rate limit updated"}

@superadmin_router.get("/admins/{admin_id}/users")
async def sa_admin_users(admin_id: str):
    db = get_db()
    cols = "id, email, role, tier, credit_pool, is_active, created_at, last_login"
    users = db.execute(f"SELECT {cols} FROM users WHERE admin_id = ?", [admin_id]).fetchall()
    return [{"id": u[0], "email": u[1], "role": u[2], "tier": u[3], "credit_pool": u[4], "is_active": u[5], "created_at": u[6], "last_login": u[7]} for u in users]

@superadmin_router.get("/users")
async def sa_all_users():
    db = get_db()
    users = db.execute("""
        SELECT u.id, u.email, u.role, u.tier, u.credit_pool, u.is_active, u.created_at, u.last_login, a.email
        FROM users u LEFT JOIN users a ON u.admin_id = a.id
        WHERE u.role = 'user'
    """).fetchall()
    return [{"id": u[0], "email": u[1], "role": u[2], "tier": u[3], "credit_pool": u[4], "is_active": u[5], "created_at": u[6], "last_login": u[7], "admin_email": u[8]} for u in users]

@superadmin_router.delete("/admins/{admin_id}")
async def sa_delete_admin(admin_id: str):
    db = get_db()
    db.execute("UPDATE users SET is_active = FALSE WHERE id = ? OR admin_id = ?", [admin_id, admin_id])
    return {"message": "Admin deleted (soft)"}

@superadmin_router.get("/impersonate/{user_id}")
async def sa_impersonate(user_id: str, response: StreamingResponse, request_user: UserResponse = Depends(require_superadmin)):
    db = get_db()
    user = db.execute("SELECT id, email, role, admin_id, credit_pool, tier, is_active FROM users WHERE id = ?", [user_id]).fetchone()
    if not user:
        raise HTTPException(404, "User not found")
        
    access_token_expires = timedelta(minutes=15)
    access_token = create_access_token(
        data={"sub": user[0], "role": user[2], "admin_id": user[3], "impersonated_by": request_user.id}, expires_delta=access_token_expires
    )
    # Set cookie for impersonation
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", path="/")
    return {"access_token": access_token, "token_type": "bearer", "user": {"id": user[0], "email": user[1], "role": user[2]}}

# --- ADMIN ROUTES ---

def admin_scope_filter(current_user: UserResponse):
    if current_user.role == "superadmin":
        return None
    return current_user.id

@admin_router.get("/dashboard")
async def a_dashboard(current_user: UserResponse = Depends(require_admin)):
    db = get_db()
    admin_clause = ""
    params = []
    scope_id = admin_scope_filter(current_user)
    if scope_id:
        admin_clause = "WHERE admin_id = ?"
        params = [scope_id]
        
    total_users = db.execute(f"SELECT COUNT(*) FROM users {admin_clause}", params).fetchone()[0]
    
    if scope_id:
        allocated = db.execute("SELECT COALESCE(SUM(credit_pool), 0) FROM users WHERE admin_id = ?", [scope_id]).fetchone()[0]
        remaining = current_user.credit_pool - allocated
        jobs_query = "SELECT COUNT(*) FROM verification_jobs j JOIN users u ON j.user_id = u.id WHERE u.admin_id = ?"
        total_jobs = db.execute(jobs_query, [scope_id]).fetchone()[0]
        stats = db.execute("SELECT v.status, COUNT(*) FROM verification_results v JOIN verification_jobs j ON v.job_id = j.id JOIN users u ON j.user_id = u.id WHERE u.admin_id = ? GROUP BY v.status", [scope_id]).fetchall()
    else:
        remaining = 999999999
        total_jobs = db.execute("SELECT COUNT(*) FROM verification_jobs").fetchone()[0]
        stats = db.execute("SELECT status, COUNT(*) FROM verification_results GROUP BY status").fetchall()
        
    return {
        "total_users": total_users,
        "credits_remaining": remaining,
        "total_jobs": total_jobs,
        "verification_counts": {row[0]: row[1] for row in stats}
    }

class UserCreate(BaseModel):
    email: EmailStr
    password: Optional[str] = None
    initial_credits: int = 0

@admin_router.get("/users")
async def a_users(current_user: UserResponse = Depends(require_admin)):
    db = get_db()
    scope = admin_scope_filter(current_user)
    if scope:
        users = db.execute("SELECT id, email, role, tier, credit_pool, is_active, created_at, last_login FROM users WHERE admin_id = ?", [scope]).fetchall()
    else:
        users = db.execute("SELECT id, email, role, tier, credit_pool, is_active, created_at, last_login FROM users WHERE role = 'user'").fetchall()
        
    res = []
    for u in users:
        jobs = db.execute("SELECT COUNT(*), COALESCE(SUM(processed_emails), 0) FROM verification_jobs WHERE user_id = ?", [u[0]]).fetchone()
        res.append({
            "id": u[0], "email": u[1], "role": u[2], "tier": u[3], "credit_pool": u[4],
            "is_active": u[5], "created_at": u[6], "last_login": u[7],
            "job_count": jobs[0], "emails_verified": jobs[1]
        })
    return res

@admin_router.post("/users")
async def a_create_user(data: UserCreate, current_user: UserResponse = Depends(require_admin)):
    db = get_db()
    if db.execute("SELECT id FROM users WHERE email = ?", [data.email]).fetchone():
        raise HTTPException(400, "Email already exists")
        
    if current_user.role != "superadmin":
        allocated = db.execute("SELECT COALESCE(SUM(credit_pool), 0) FROM users WHERE admin_id = ?", [current_user.id]).fetchone()[0]
        if current_user.credit_pool < allocated + data.initial_credits:
            raise HTTPException(400, "Not enough credits in Admin pool")
            
    generated_password = data.password or str(uuid.uuid4())
    firebase_user = _ensure_firebase_user(str(data.email), generated_password, str(data.email))
    u_id = str(uuid.uuid4())
    
    db.execute("""
        INSERT INTO users (id, firebase_uid, email, display_name, role, plan, credits, tier, credit_pool, admin_id, created_by, status, is_active, email_verified)
        VALUES (?, ?, ?, ?, 'user', 'Free', ?, 'standard', ?, ?, ?, 'Active', TRUE, FALSE)
    """, [u_id, firebase_user.uid, data.email, firebase_user.display_name, data.initial_credits, data.initial_credits, current_user.id if current_user.role == 'admin' else None, current_user.id])
    
    return {"message": "User created", "id": u_id, "password_generated": not data.password}

@admin_router.patch("/users/{user_id}/credits")
async def a_user_credits(user_id: str, data: CreditUpdate, current_user: UserResponse = Depends(require_admin)):
    db = get_db()
    tgt = db.execute("SELECT admin_id, credit_pool FROM users WHERE id = ?", [user_id]).fetchone()
    if not tgt: raise HTTPException(404, "User not found")
    
    if current_user.role != "superadmin" and tgt[0] != current_user.id:
        raise HTTPException(403, "Access denied")
        
    if current_user.role != "superadmin":
        allocated = db.execute("SELECT COALESCE(SUM(credit_pool), 0) FROM users WHERE admin_id = ?", [current_user.id]).fetchone()[0]
        if data.amount > 0 and (current_user.credit_pool - allocated) < data.amount:
            raise HTTPException(400, "Not enough credits in Admin pool")
            
    db.execute("UPDATE users SET credit_pool = GREATEST(0, credit_pool + ?) WHERE id = ?", [data.amount, user_id])
    return {"message": "Credits updated"}

@admin_router.patch("/users/{user_id}/tier")
async def a_user_tier(user_id: str, data: TierUpdate, current_user: UserResponse = Depends(require_admin)):
    from database import get_db_write_lock
    if data.tier not in ("free", "standard", "power", "enterprise"):
        raise HTTPException(status_code=400, detail="Invalid tier")
    db = get_db()
    tgt = db.execute("SELECT admin_id FROM users WHERE id = ?", [user_id]).fetchone()
    if not tgt or (current_user.role != "superadmin" and tgt[0] != current_user.id):
        raise HTTPException(404, "Not found or denied")
    async with get_db_write_lock():
        db.execute("UPDATE users SET tier = ? WHERE id = ?", [data.tier, user_id])
    return {"message": "Tier updated"}

@admin_router.patch("/users/{user_id}/suspend")
async def a_user_suspend(user_id: str, current_user: UserResponse = Depends(require_admin)):
    db = get_db()
    tgt = db.execute("SELECT admin_id, is_active FROM users WHERE id = ?", [user_id]).fetchone()
    if not tgt or (current_user.role != "superadmin" and tgt[0] != current_user.id):
        raise HTTPException(404, "Not found or denied")
    db.execute("UPDATE users SET is_active = ? WHERE id = ?", [not tgt[1], user_id])
    return {"message": "Suspension toggled"}

@admin_router.get("/users/{user_id}/jobs")
async def a_user_jobs(user_id: str, current_user: UserResponse = Depends(require_admin)):
    db = get_db()
    tgt = db.execute("SELECT admin_id FROM users WHERE id = ?", [user_id]).fetchone()
    if not tgt or (current_user.role != "superadmin" and tgt[0] != current_user.id):
        raise HTTPException(404, "Not found or denied")
    jobs = db.execute("SELECT id, file_name, status, created_at, total_emails, processed_emails FROM verification_jobs WHERE user_id = ?", [user_id]).fetchall()
    return [{"id": j[0], "file_name": j[1], "status": j[2], "created_at": j[3], "progress_percentage": round(j[5]/j[4]*100,2) if j[4]>0 else 0} for j in jobs]

@admin_router.get("/jobs")
async def a_jobs(current_user: UserResponse = Depends(require_admin)):
    db = get_db()
    scope = admin_scope_filter(current_user)
    if scope:
        jobs = db.execute("SELECT j.id, j.file_name, j.status, j.created_at, u.email as user_email FROM verification_jobs j JOIN users u ON j.user_id = u.id WHERE u.admin_id = ?", [scope]).fetchall()
    else:
        jobs = db.execute("SELECT j.id, j.file_name, j.status, j.created_at, u.email as user_email FROM verification_jobs j JOIN users u ON j.user_id = u.id").fetchall()
    return [{"id": j[0], "file_name": j[1], "status": j[2], "created_at": j[3], "user_email": j[4]} for j in jobs]

# --- API Key Management ---
api_keys_router = APIRouter(prefix="/api/settings/keys", tags=["api_keys"])

class APIKeyCreate(BaseModel):
    name: str

@api_keys_router.post("/")
async def create_key(data: APIKeyCreate, current_user: UserResponse = Depends(require_permission("api.create"))):
    db = get_db()
    # Limit to 5 keys per user for now
    existing_count = db.execute("SELECT COUNT(*) FROM api_keys WHERE user_id = ?", [current_user.id]).fetchone()[0]
    if existing_count >= 5:
        raise HTTPException(status_code=400, detail="Maximum of 5 API keys reached. Revoke an old one to create a new one.")
        
    raw_key = f"sk_live_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    # Format: sk_live_...xxxx (last 4 characters)
    prefix = f"sk_live_...{raw_key[-4:]}"
    key_id = str(uuid.uuid4())
    
    db.execute("""
        INSERT INTO api_keys (id, user_id, name, key_hash, prefix)
        VALUES (?, ?, ?, ?, ?)
    """, [key_id, current_user.id, data.name, key_hash, prefix])
    
    return {"id": key_id, "name": data.name, "key": raw_key}

@api_keys_router.get("/")
async def list_keys(current_user: UserResponse = Depends(require_permission("api.view"))):
    db = get_db()
    keys = db.execute("""
        SELECT id, name, prefix, created_at, last_used FROM api_keys WHERE user_id = ?
        ORDER BY created_at DESC
    """, [current_user.id]).fetchall()
    
    return [
        {
            "id": k[0],
            "name": k[1],
            "prefix": k[2],
            "created_at": k[3],
            "last_used": k[4]
        } for k in keys
    ]

@api_keys_router.delete("/{key_id}")
async def delete_key(key_id: str, current_user: UserResponse = Depends(require_permission("api.revoke"))):
    db = get_db()
    db.execute("DELETE FROM api_keys WHERE id = ? AND user_id = ?", [key_id, current_user.id])
    return {"message": "API key revoked successfully"}
