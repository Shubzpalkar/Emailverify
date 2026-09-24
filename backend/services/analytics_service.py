import time
from datetime import datetime, timezone, timedelta
from database import get_db

def _build_time_cutoff(timeframe: str) -> datetime:
    now = datetime.now(timezone.utc)
    if timeframe == "today":
        return datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    elif timeframe == "yesterday":
        return datetime(now.year, now.month, now.day, tzinfo=timezone.utc) - timedelta(days=1)
    elif timeframe == "7days":
        return now - timedelta(days=7)
    elif timeframe == "30days":
        return now - timedelta(days=30)
    elif timeframe == "month":
        return datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    elif timeframe == "year":
        return datetime(now.year, 1, 1, tzinfo=timezone.utc)
    return now - timedelta(days=30)


def _build_auth_filter(user_id: str, workspace_id: str, role: str, prefix: str = "vj") -> tuple[str, list]:
    p = f"{prefix}." if prefix else ""
    if role == "superadmin":
        return "1=1", []
    elif role in ["admin", "manager"] and workspace_id:
        return f"{p}workspace_id = ?", [workspace_id]
    elif workspace_id:
        return f"({p}workspace_id = ? OR {p}user_id = ?)", [workspace_id, user_id]
    else:
        return f"{p}user_id = ?", [user_id]


def get_analytics_overview(user_id: str, workspace_id: str, role: str, timeframe: str = "30days") -> dict:
    db = get_db()
    auth_clause, params = _build_auth_filter(user_id, workspace_id, role)
    cutoff = _build_time_cutoff(timeframe)

    row = db.execute(f"""
        SELECT
            COALESCE(SUM(total_emails), 0) as total_emails,
            COALESCE(SUM(deliverable_count), 0) as deliv,
            COALESCE(SUM(protected_count), 0) as prot,
            COALESCE(SUM(catch_all_count), 0) as catch,
            COALESCE(SUM(invalid_count), 0) as inv,
            COALESCE(SUM(unknown_count), 0) as unk,
            COALESCE(SUM(credits_used), 0) as creds,
            COALESCE(AVG(processing_time_ms), 0) as avg_time
        FROM verification_jobs vj
        WHERE {auth_clause} AND vj.created_at >= ? AND COALESCE(vj.is_deleted, FALSE) = FALSE
    """, params + [cutoff]).fetchone()

    total = row[0] or 0
    deliv = row[1] or 0
    prot = row[2] or 0
    catch = row[3] or 0
    inv = row[4] or 0
    unk = row[5] or 0

    return {
        "total_emails_verified": total,
        "deliverable_percentage": round((deliv / total * 100), 1) if total > 0 else 0.0,
        "protected_percentage": round((prot / total * 100), 1) if total > 0 else 0.0,
        "catch_all_percentage": round((catch / total * 100), 1) if total > 0 else 0.0,
        "invalid_percentage": round((inv / total * 100), 1) if total > 0 else 0.0,
        "unknown_percentage": round((unk / total * 100), 1) if total > 0 else 0.0,
        "credits_used": row[6] or 0,
        "avg_verification_time_ms": round(row[7] or 0.0, 1),
        "monthly_growth": 0.0
    }


def get_analytics_trends(user_id: str, workspace_id: str, role: str, timeframe: str = "30days") -> dict:
    db = get_db()
    auth_clause, params = _build_auth_filter(user_id, workspace_id, role)
    now = datetime.now(timezone.utc)

    trend = []
    num_days = 7 if timeframe == "7days" else 14 if timeframe == "30days" else 30
    for i in range(num_days - 1, -1, -1):
        day_date = (now - timedelta(days=i)).strftime("%b %d")
        d_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc) - timedelta(days=i)
        d_end = d_start + timedelta(days=1)

        row = db.execute(f"""
            SELECT
                COALESCE(SUM(total_emails), 0),
                COALESCE(SUM(credits_used), 0),
                COALESCE(SUM(deliverable_count), 0),
                COALESCE(SUM(invalid_count), 0),
                COALESCE(AVG(processing_time_ms), 0)
            FROM verification_jobs vj
            WHERE {auth_clause} AND vj.created_at >= ? AND vj.created_at < ? AND COALESCE(vj.is_deleted, FALSE) = FALSE
        """, params + [d_start, d_end]).fetchone()

        tot = row[0] or 0
        deliv = row[2] or 0
        inv = row[3] or 0

        deliv_pct = round((deliv / tot * 100), 1) if tot > 0 else 0.0
        inv_pct = round((inv / tot * 100), 1) if tot > 0 else 0.0

        trend.append({
            "label": day_date,
            "emails_verified": tot,
            "credits_used": row[1] or 0,
            "deliverability_pct": deliv_pct,
            "invalid_rate_pct": inv_pct,
            "processing_time_ms": round(row[4] or 0.0, 1)
        })

    return {"timeframe": timeframe, "trend": trend}


def get_analytics_breakdown(user_id: str, workspace_id: str, role: str, timeframe: str = "30days") -> dict:
    db = get_db()
    auth_clause, params = _build_auth_filter(user_id, workspace_id, role)
    cutoff = _build_time_cutoff(timeframe)

    row = db.execute(f"""
        SELECT
            COALESCE(SUM(deliverable_count), 0),
            COALESCE(SUM(protected_count), 0),
            COALESCE(SUM(catch_all_count), 0),
            COALESCE(SUM(disposable_count), 0),
            COALESCE(SUM(role_count), 0),
            COALESCE(SUM(unknown_count), 0),
            COALESCE(SUM(duplicate_count), 0),
            COALESCE(SUM(invalid_count), 0)
        FROM verification_jobs vj
        WHERE {auth_clause} AND vj.created_at >= ? AND COALESCE(vj.is_deleted, FALSE) = FALSE
    """, params + [cutoff]).fetchone()

    counts = {
        "deliverable": row[0] or 0,
        "protected": row[1] or 0,
        "catch_all": row[2] or 0,
        "disposable": row[3] or 0,
        "role_accounts": row[4] or 0,
        "unknown": row[5] or 0,
        "duplicates": row[6] or 0,
        "invalid": row[7] or 0
    }
    total = sum(counts.values())

    return {
        "counts": counts,
        "total": total,
        "percentages": {k: (round((v / total * 100), 1) if total > 0 else 0.0) for k, v in counts.items()}
    }


def get_domain_analytics(user_id: str, workspace_id: str, role: str, timeframe: str = "30days") -> dict:
    db = get_db()
    auth_clause, params = _build_auth_filter(user_id, workspace_id, role)
    cutoff = _build_time_cutoff(timeframe)

    rows = db.execute(f"""
        SELECT vr.domain, COUNT(*) as verified,
               COUNT(CASE WHEN vr.status = 'valid' THEN 1 END) as deliv,
               COUNT(CASE WHEN vr.status = 'invalid' THEN 1 END) as inv,
               COUNT(CASE WHEN vr.status = 'risky' THEN 1 END) as prot,
               COUNT(CASE WHEN vr.status = 'catch_all' THEN 1 END) as catch
        FROM verification_results vr
        JOIN verification_jobs vj ON vr.job_id = vj.id
        WHERE {auth_clause} AND vj.created_at >= ? AND COALESCE(vj.is_deleted, FALSE) = FALSE AND vr.domain IS NOT NULL AND vr.domain != ''
        GROUP BY vr.domain
        ORDER BY verified DESC
        LIMIT 5
    """, params + [cutoff]).fetchall()

    top_domains = []
    for r in rows:
        v_cnt = r[1] or 1
        top_domains.append({
            "domain": r[0],
            "verified": r[1],
            "deliverable_pct": round(((r[2] or 0) / v_cnt * 100), 1),
            "invalid_pct": round(((r[3] or 0) / v_cnt * 100), 1),
            "protected_pct": round(((r[4] or 0) / v_cnt * 100), 1),
            "catch_all_pct": round(((r[5] or 0) / v_cnt * 100), 1),
            "avg_time_ms": 0
        })

    return {
        "top_domains": top_domains,
        "worst_domains": [],
        "highest_invalid_rate_domain": top_domains[0]["domain"] if top_domains else None,
        "fastest_provider": None
    }


def get_provider_analytics(user_id: str, workspace_id: str, role: str, timeframe: str = "30days") -> list[dict]:
    return []


def get_credit_analytics(user_id: str, workspace_id: str, role: str, timeframe: str = "30days") -> dict:
    db = get_db()
    auth_clause, params = _build_auth_filter(user_id, workspace_id, role)
    now_utc = datetime.now(timezone.utc)
    today_start = datetime(now_utc.year, now_utc.month, now_utc.day, tzinfo=timezone.utc)
    week_start = now_utc - timedelta(days=7)
    month_start = datetime(now_utc.year, now_utc.month, 1, tzinfo=timezone.utc)

    today_credits = db.execute(f"""
        SELECT COALESCE(SUM(credits_used), 0) FROM verification_jobs vj WHERE {auth_clause} AND created_at >= ? AND COALESCE(is_deleted, FALSE) = FALSE
    """, params + [today_start]).fetchone()[0] or 0

    weekly_credits = db.execute(f"""
        SELECT COALESCE(SUM(credits_used), 0) FROM verification_jobs vj WHERE {auth_clause} AND created_at >= ? AND COALESCE(is_deleted, FALSE) = FALSE
    """, params + [week_start]).fetchone()[0] or 0

    monthly_credits = db.execute(f"""
        SELECT COALESCE(SUM(credits_used), 0) FROM verification_jobs vj WHERE {auth_clause} AND created_at >= ? AND COALESCE(is_deleted, FALSE) = FALSE
    """, params + [month_start]).fetchone()[0] or 0

    return {
        "credits_today": today_credits,
        "weekly_credits": weekly_credits,
        "monthly_credits": monthly_credits,
        "credits_per_workspace": monthly_credits,
        "avg_credits_per_job": 0,
        "consumption_trend": "Stable"
    }


def get_team_analytics(workspace_id: str, role: str) -> dict:
    db = get_db()
    rows = db.execute("""
        SELECT u.display_name, u.email, u.role, COUNT(vj.id), COALESCE(SUM(vj.total_emails), 0), COALESCE(SUM(vj.credits_used), 0)
        FROM users u
        LEFT JOIN verification_jobs vj ON u.id = vj.user_id AND COALESCE(vj.is_deleted, FALSE) = FALSE
        WHERE u.workspace_id = ?
        GROUP BY u.id, u.display_name, u.email, u.role
        ORDER BY COALESCE(SUM(vj.total_emails), 0) DESC
    """, [workspace_id]).fetchall()

    leaderboard = []
    for r in rows:
        tot_emails = r[4] or 0
        leaderboard.append({
            "name": r[0] or r[1] or "User",
            "role": r[2],
            "jobs_count": r[3],
            "emails_verified": tot_emails,
            "credits_used": r[5],
            "success_rate": 0.0
        })

    return {"leaderboard": leaderboard}


def get_performance_analytics(user_id: str, workspace_id: str, role: str) -> dict:
    return {
        "avg_smtp_time_ms": 0.0,
        "avg_dns_time_ms": 0.0,
        "avg_queue_time_ms": 0.0,
        "avg_verification_time_ms": 0.0,
        "emails_per_second": 0.0,
        "jobs_per_hour": 0,
        "processing_efficiency": 0.0
    }


def get_file_analytics(user_id: str, workspace_id: str, role: str) -> dict:
    db = get_db()
    auth_clause, params = _build_auth_filter(user_id, workspace_id, role)

    rows = db.execute(f"""
        SELECT file_name, total_emails, deliverable_count, invalid_count, credits_used
        FROM verification_jobs vj
        WHERE {auth_clause} AND COALESCE(vj.is_deleted, FALSE) = FALSE
        ORDER BY total_emails DESC
        LIMIT 5
    """, params).fetchall()

    largest_files = []
    for r in rows:
        tot = r[1] or 1
        deliv = r[2] or 0
        largest_files.append({
            "file_name": r[0] or "Email List",
            "total_emails": tot,
            "deliverable_pct": round((deliv / tot * 100), 1),
            "credits_used": r[4] or 0
        })

    return {
        "largest_files": largest_files,
        "avg_file_size_kb": 0,
        "credits_per_file": 0
    }


def compare_jobs(job_id_a: str, job_id_b: str, user_id: str, workspace_id: str, role: str) -> dict:
    db = get_db()
    auth_clause, params = _build_auth_filter(user_id, workspace_id, role, prefix="vj")
    
    row_a = db.execute(f"SELECT file_name, total_emails, deliverable_count, protected_count, catch_all_count, invalid_count, credits_used, processing_time_ms FROM verification_jobs vj WHERE vj.id = ? AND {auth_clause} AND COALESCE(vj.is_deleted, FALSE) = FALSE", [job_id_a] + params).fetchone()
    row_b = db.execute(f"SELECT file_name, total_emails, deliverable_count, protected_count, catch_all_count, invalid_count, credits_used, processing_time_ms FROM verification_jobs vj WHERE vj.id = ? AND {auth_clause} AND COALESCE(vj.is_deleted, FALSE) = FALSE", [job_id_b] + params).fetchone()

    if not row_a or not row_b:
        raise ValueError("One or both jobs not found or access denied")

    def format_job(r, jid):
        tot = max(r[1] or 1, 1)
        return {
            "id": jid,
            "name": r[0] or jid,
            "total": r[1] or 0,
            "deliverable_pct": round(((r[2] or 0) / tot * 100), 1),
            "protected_pct": round(((r[3] or 0) / tot * 100), 1),
            "catch_all_pct": round(((r[4] or 0) / tot * 100), 1),
            "invalid_pct": round(((r[5] or 0) / tot * 100), 1),
            "credits": r[6] or 0,
            "duration_ms": r[7] or 0
        }

    job_a_data = format_job(row_a, job_id_a)
    job_b_data = format_job(row_b, job_id_b)

    return {
        "job_a": job_a_data,
        "job_b": job_b_data,
        "delta": {
            "deliverable_diff": round(job_b_data["deliverable_pct"] - job_a_data["deliverable_pct"], 1),
            "invalid_diff": round(job_b_data["invalid_pct"] - job_a_data["invalid_pct"], 1)
        }
    }


def get_activity_heatmaps(user_id: str, workspace_id: str, role: str) -> dict:
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    matrix = []
    for d in days:
        matrix.append({"day": d, "hours": [0] * 24})
    return {"days": days, "matrix": matrix}


def get_workspace_analytics(workspace_id: str, role: str) -> dict:
    db = get_db()
    ws_row = db.execute("SELECT company_name, workspace_name, plan, credits_remaining FROM workspaces WHERE id = ?", [workspace_id]).fetchone() if workspace_id else None
    mem_count = db.execute("SELECT COUNT(*) FROM users WHERE workspace_id = ?", [workspace_id]).fetchone()[0] if workspace_id else 1

    return {
        "workspace_name": ws_row[1] or ws_row[0] if ws_row else "Default Workspace",
        "plan": ws_row[2] if ws_row else "Free",
        "members": mem_count,
        "quality_score": 0.0,
        "monthly_trend": "Stable"
    }


def get_system_analytics(role: str) -> dict:
    if role not in ["admin", "superadmin"]:
        return {"status": "Restricted"}

    return {
        "smtp_throughput_eps": 0.0,
        "dns_lookup_success_pct": 100.0,
        "redis_hit_ratio_pct": 0.0,
        "api_gateway_p99_ms": 0.0,
        "database_query_avg_ms": 0.0,
        "queue_backlog_jobs": 0
    }
