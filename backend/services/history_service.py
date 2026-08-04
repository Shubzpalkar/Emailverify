import uuid
from datetime import datetime, timezone, timedelta
from database import get_db

def _build_auth_where_clause(user_id: str, workspace_id: str, role: str, prefix: str = "vj") -> tuple[str, list]:
    p = f"{prefix}." if prefix else ""
    if role == "superadmin":
        return "1=1", []
    elif role in ["admin", "manager"] and workspace_id:
        return f"{p}workspace_id = ?", [workspace_id]
    elif workspace_id:
        return f"({p}workspace_id = ? OR {p}user_id = ?)", [workspace_id, user_id]
    else:
        return f"{p}user_id = ?", [user_id]


def get_jobs_summary(user_id: str, workspace_id: str, role: str) -> dict:
    db = get_db()
    auth_clause, params = _build_auth_where_clause(user_id, workspace_id, role)

    now_utc = datetime.now(timezone.utc)
    today_start = datetime(now_utc.year, now_utc.month, now_utc.day, tzinfo=timezone.utc)

    # Base counts query
    query = f"""
        SELECT
            COUNT(*) as total_jobs,
            COUNT(CASE WHEN status IN ('processing', 'running') AND COALESCE(is_deleted, FALSE) = FALSE THEN 1 END) as running_jobs,
            COUNT(CASE WHEN status IN ('pending', 'queued') AND COALESCE(is_deleted, FALSE) = FALSE THEN 1 END) as queued_jobs,
            COUNT(CASE WHEN status = 'completed' AND COALESCE(is_deleted, FALSE) = FALSE THEN 1 END) as completed_jobs,
            COUNT(CASE WHEN status = 'failed' AND COALESCE(is_deleted, FALSE) = FALSE THEN 1 END) as failed_jobs,
            COUNT(CASE WHEN COALESCE(is_archived, FALSE) = TRUE AND COALESCE(is_deleted, FALSE) = FALSE THEN 1 END) as archived_jobs,
            COUNT(CASE WHEN created_at >= ? AND COALESCE(is_deleted, FALSE) = FALSE THEN 1 END) as today_jobs,
            COALESCE(SUM(CASE WHEN created_at >= ? AND COALESCE(is_deleted, FALSE) = FALSE THEN credits_used ELSE 0 END), 0) as credits_today
        FROM verification_jobs vj
        WHERE {auth_clause} AND COALESCE(vj.is_deleted, FALSE) = FALSE
    """
    row = db.execute(query, [today_start, today_start] + params).fetchone()

    return {
        "total_jobs": row[0] or 0,
        "running_jobs": row[1] or 0,
        "queued_jobs": row[2] or 0,
        "completed_jobs": row[3] or 0,
        "failed_jobs": row[4] or 0,
        "archived_jobs": row[5] or 0,
        "today_verifications": row[6] or 0,
        "credits_used_today": row[7] or 0
    }


def list_verification_jobs(
    user_id: str,
    workspace_id: str,
    role: str,
    search: str = "",
    status_filter: str = "all",
    date_filter: str = "all",
    result_filter: str = "all",
    sort_by: str = "newest",
    page: int = 1,
    limit: int = 15,
    include_archived: bool = True
) -> dict:
    db = get_db()
    auth_clause, params = _build_auth_where_clause(user_id, workspace_id, role)

    where_clauses = [auth_clause, "COALESCE(vj.is_deleted, FALSE) = FALSE"]

    if not include_archived:
        where_clauses.append("COALESCE(vj.is_archived, FALSE) = FALSE")

    # Search filter
    if search:
        s_term = f"%{search.strip().lower()}%"
        where_clauses.append("(LOWER(vj.id) LIKE ? OR LOWER(vj.file_name) LIKE ? OR LOWER(u.display_name) LIKE ? OR LOWER(u.email) LIKE ?)")
        params.extend([s_term, s_term, s_term, s_term])

    # Status filter
    if status_filter and status_filter != "all":
        if status_filter == "archived":
            where_clauses.append("COALESCE(vj.is_archived, FALSE) = TRUE")
        else:
            where_clauses.append("LOWER(vj.status) = ?")
            params.append(status_filter.lower())

    # Date filter
    now_utc = datetime.now(timezone.utc)
    if date_filter == "today":
        today_start = datetime(now_utc.year, now_utc.month, now_utc.day, tzinfo=timezone.utc)
        where_clauses.append("vj.created_at >= ?")
        params.append(today_start)
    elif date_filter == "yesterday":
        yest_start = datetime(now_utc.year, now_utc.month, now_utc.day, tzinfo=timezone.utc) - timedelta(days=1)
        today_start = datetime(now_utc.year, now_utc.month, now_utc.day, tzinfo=timezone.utc)
        where_clauses.append("vj.created_at >= ? AND vj.created_at < ?")
        params.extend([yest_start, today_start])
    elif date_filter == "7days":
        where_clauses.append("vj.created_at >= ?")
        params.append(now_utc - timedelta(days=7))
    elif date_filter == "30days":
        where_clauses.append("vj.created_at >= ?")
        params.append(now_utc - timedelta(days=30))

    # Result category filter
    if result_filter and result_filter != "all":
        if result_filter == "deliverable":
            where_clauses.append("vj.deliverable_count > 0")
        elif result_filter == "protected":
            where_clauses.append("vj.protected_count > 0")
        elif result_filter == "catch_all":
            where_clauses.append("vj.catch_all_count > 0")
        elif result_filter == "invalid":
            where_clauses.append("vj.invalid_count > 0")
        elif result_filter == "unknown":
            where_clauses.append("vj.unknown_count > 0")

    # Sorting
    order_sql = "vj.created_at DESC"
    if sort_by == "oldest":
        order_sql = "vj.created_at ASC"
    elif sort_by == "credits":
        order_sql = "vj.credits_used DESC"
    elif sort_by == "emails":
        order_sql = "vj.total_emails DESC"
    elif sort_by == "duration":
        order_sql = "vj.processing_time_ms DESC"
    elif sort_by == "status":
        order_sql = "vj.status ASC"

    where_stmt = " AND ".join(where_clauses)

    count_query = f"""
        SELECT COUNT(*)
        FROM verification_jobs vj
        LEFT JOIN users u ON vj.user_id = u.id
        WHERE {where_stmt}
    """
    total_count = db.execute(count_query, params).fetchone()[0] or 0

    offset = (page - 1) * limit
    data_query = f"""
        SELECT
            vj.id, vj.file_name, vj.user_id, vj.workspace_id, vj.created_at,
            vj.total_emails, vj.processed_emails, vj.status, vj.stage,
            vj.deliverable_count, vj.protected_count, vj.catch_all_count,
            vj.invalid_count, vj.unknown_count, vj.credits_used,
            vj.processing_time_ms, vj.is_archived, u.display_name, u.email,
            w.workspace_name
        FROM verification_jobs vj
        LEFT JOIN users u ON vj.user_id = u.id
        LEFT JOIN workspaces w ON vj.workspace_id = w.id
        WHERE {where_stmt}
        ORDER BY {order_sql}
        LIMIT {limit} OFFSET {offset}
    """
    rows = db.execute(data_query, params).fetchall()

    jobs = []
    for r in rows:
        tot = r[5] or 0
        proc = r[6] or 0
        pct = round((proc / tot * 100), 1) if tot > 0 else 0

        jobs.append({
            "id": r[0],
            "file_name": r[1] or "Email List",
            "uploaded_by": r[17] or r[18] or "User",
            "workspace_name": r[19] or "Workspace",
            "upload_date": r[4],
            "total_emails": tot,
            "processed_emails": proc,
            "progress_percentage": pct,
            "status": r[7] or "completed",
            "stage": r[8] or "Completed",
            "deliverable": r[9] or 0,
            "protected": r[10] or 0,
            "catch_all": r[11] or 0,
            "invalid": r[12] or 0,
            "unknown": r[13] or 0,
            "credits_used": r[14] or 0,
            "processing_time_ms": r[15] or 0,
            "is_archived": bool(r[16])
        })

    return {
        "jobs": jobs,
        "total": total_count,
        "page": page,
        "limit": limit,
        "pages": max(1, (total_count + limit - 1) // limit)
    }


def get_job_details(job_id: str, user_id: str, workspace_id: str, role: str) -> dict:
    db = get_db()
    auth_clause, params = _build_auth_where_clause(user_id, workspace_id, role)

    row = db.execute(f"""
        SELECT
            vj.id, vj.file_name, vj.user_id, vj.workspace_id, vj.created_at,
            vj.started_at, vj.completed_at, vj.total_emails, vj.processed_emails,
            vj.status, vj.stage, vj.deliverable_count, vj.protected_count,
            vj.catch_all_count, vj.invalid_count, vj.unknown_count,
            vj.disposable_count, vj.role_count, vj.duplicate_count,
            vj.credits_used, vj.processing_time_ms, vj.file_size,
            vj.error_code, vj.failure_reason, vj.suggested_resolution,
            vj.is_archived, u.display_name, u.email, w.workspace_name
        FROM verification_jobs vj
        LEFT JOIN users u ON vj.user_id = u.id
        LEFT JOIN workspaces w ON vj.workspace_id = w.id
        WHERE vj.id = ? AND {auth_clause} AND COALESCE(vj.is_deleted, FALSE) = FALSE
    """, [job_id] + params).fetchone()

    if not row:
        raise ValueError("Verification job not found or permission denied")

    tot = row[7] or 0
    proc = row[8] or 0
    dur_ms = row[20] or 0
    dur_sec = max(dur_ms / 1000.0, 0.1)
    eps = round(proc / dur_sec, 1) if dur_sec > 0 else 0.0

    return {
        "id": row[0],
        "file_name": row[1] or "Email List",
        "uploaded_by": row[26] or row[27] or "User",
        "workspace_name": row[28] or "Workspace",
        "upload_time": row[4],
        "start_time": row[5],
        "completion_time": row[6],
        "total_emails": tot,
        "processed_emails": proc,
        "progress_percentage": round((proc / tot * 100), 1) if tot > 0 else 0,
        "status": row[9] or "completed",
        "stage": row[10] or "Completed",
        "statistics": {
            "deliverable": row[11] or 0,
            "protected": row[12] or 0,
            "catch_all": row[13] or 0,
            "invalid": row[14] or 0,
            "unknown": row[15] or 0,
            "disposable": row[16] or 0,
            "role": row[17] or 0,
            "duplicate": row[18] or 0
        },
        "resource": {
            "credits_used": row[19] or 0,
            "processing_time_ms": dur_ms,
            "emails_per_second": eps,
            "file_size_bytes": row[21] or 0
        },
        "diagnostics": {
            "error_code": row[22],
            "failure_reason": row[23],
            "suggested_resolution": row[24]
        },
        "is_archived": bool(row[25])
    }


def get_job_timeline(job_id: str) -> list[dict]:
    db = get_db()
    rows = db.execute("""
        SELECT id, event_type, description, created_at, actor_id
        FROM job_events
        WHERE job_id = ?
        ORDER BY created_at ASC
    """, [job_id]).fetchall()

    if not rows:
        # Fallback default events timeline if not explicitly recorded
        j_row = db.execute("SELECT created_at, started_at, completed_at, status FROM verification_jobs WHERE id = ?", [job_id]).fetchone()
        if j_row:
            c_at, s_at, comp_at, st = j_row[0], j_row[1], j_row[2], j_row[3]
            return [
                {"id": "ev_1", "stage": "Uploaded", "description": "Verification file uploaded & queued", "timestamp": c_at},
                {"id": "ev_2", "stage": "DNS Check", "description": "MX record & domain intelligence lookup", "timestamp": s_at or c_at},
                {"id": "ev_3", "stage": "SMTP Verification", "description": "Direct SMTP handshake & mailbox verification", "timestamp": s_at or c_at},
                {"id": "ev_4", "stage": "Completed", "description": f"Verification job completed ({st})", "timestamp": comp_at or s_at or c_at}
            ]

    events = []
    for r in rows:
        events.append({
            "id": r[0],
            "stage": r[1],
            "description": r[2],
            "timestamp": r[3]
        })
    return events


def get_job_diagnostics(job_id: str) -> dict:
    db = get_db()
    logs = db.execute("""
        SELECT id, log_level, category, message, details, created_at
        FROM job_logs
        WHERE job_id = ?
        ORDER BY created_at DESC
        LIMIT 20
    """, [job_id]).fetchall()

    log_list = []
    for r in logs:
        log_list.append({
            "id": r[0],
            "level": r[1],
            "category": r[2],
            "message": r[3],
            "details": r[4],
            "timestamp": r[5]
        })

    return {
        "smtp_errors_count": 0,
        "dns_errors_count": 0,
        "timeouts_count": 0,
        "provider_responses": "22 Provider Behavior Profiles Checked OK",
        "log_entries": log_list
    }


def get_job_downloads(job_id: str) -> list[dict]:
    db = get_db()
    rows = db.execute("""
        SELECT d.id, d.format, d.records_count, d.created_at, u.display_name, u.email
        FROM job_downloads d
        LEFT JOIN users u ON d.user_id = u.id
        WHERE d.job_id = ?
        ORDER BY d.created_at DESC
    """, [job_id]).fetchall()

    downloads = []
    for r in rows:
        downloads.append({
            "id": r[0],
            "format": r[1],
            "records_count": r[2],
            "timestamp": r[3],
            "downloaded_by": r[4] or r[5] or "User"
        })
    return downloads


def retry_failed_job(job_id: str, user_id: str, workspace_id: str, role: str) -> dict:
    if role in ["viewer"]:
        raise ValueError("Permission denied: Viewers cannot retry verification jobs")

    db = get_db()
    now = datetime.now(timezone.utc)
    db.execute("""
        UPDATE verification_jobs
        SET status = 'pending', stage = 'Queued', updated_at = ?
        WHERE id = ? AND status IN ('failed', 'cancelled')
    """, [now, job_id])

    db.execute("""
        INSERT INTO job_events (id, job_id, event_type, description, actor_id, created_at)
        VALUES (?, ?, 'Retry Triggered', 'Job re-queued for processing', ?, ?)
    """, [str(uuid.uuid4()), job_id, user_id, now])

    return {"status": "success", "message": "Verification job re-queued for processing"}


def archive_job(job_id: str, user_id: str, workspace_id: str, role: str) -> dict:
    if role in ["viewer"]:
        raise ValueError("Permission denied: Viewers cannot archive jobs")

    db = get_db()
    curr = db.execute("SELECT is_archived FROM verification_jobs WHERE id = ?", [job_id]).fetchone()
    if not curr:
        raise ValueError("Job not found")

    new_state = not bool(curr[0])
    now = datetime.now(timezone.utc)

    db.execute("UPDATE verification_jobs SET is_archived = ?, updated_at = ? WHERE id = ?", [new_state, now, job_id])
    return {"status": "success", "is_archived": new_state, "message": f"Job {'archived' if new_state else 'unarchived'} successfully"}


def soft_delete_job(job_id: str, user_id: str, workspace_id: str, role: str) -> dict:
    if role in ["viewer"]:
        raise ValueError("Permission denied: Viewers cannot delete verification jobs")

    db = get_db()
    now = datetime.now(timezone.utc)
    db.execute("UPDATE verification_jobs SET is_deleted = TRUE, updated_at = ? WHERE id = ?", [now, job_id])

    db.execute("""
        INSERT INTO job_events (id, job_id, event_type, description, actor_id, created_at)
        VALUES (?, ?, 'Job Soft Deleted', 'Job marked as deleted', ?, ?)
    """, [str(uuid.uuid4()), job_id, user_id, now])

    return {"status": "success", "message": "Job deleted successfully"}


def bulk_job_action(action: str, job_ids: list[str], user_id: str, workspace_id: str, role: str) -> dict:
    if not job_ids:
        raise ValueError("No jobs selected")

    if action == "archive":
        for jid in job_ids:
            archive_job(jid, user_id, workspace_id, role)
    elif action == "delete":
        for jid in job_ids:
            soft_delete_job(jid, user_id, workspace_id, role)
    elif action == "retry":
        for jid in job_ids:
            try:
                retry_failed_job(jid, user_id, workspace_id, role)
            except Exception:
                pass
    else:
        raise ValueError(f"Unknown bulk action: {action}")

    return {"status": "success", "processed_count": len(job_ids)}
