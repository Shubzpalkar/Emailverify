from database import get_db
from schemas.account import AccountUpdate
from auth import _select_user_by_id, _row_to_user, UserResponse
from firebase.firebase import initialize_firebase
import firebase_admin.auth

def update_user_profile(user_id: str, update_data: AccountUpdate) -> UserResponse:
    db = get_db()
    updates = []
    params = []
    
    if update_data.display_name is not None:
        updates.append("display_name = ?")
        params.append(update_data.display_name)
    if update_data.company is not None:
        updates.append("company = ?")
        params.append(update_data.company)
    if update_data.phone is not None:
        updates.append("phone = ?")
        params.append(update_data.phone)
        
    if updates:
        sql = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
        params.append(user_id)
        db.execute(sql, params)
        
    user_row = _select_user_by_id(db, user_id)
    return _row_to_user(user_row)

def get_api_summary(user_id: str):
    # Placeholder for API Summary data
    return {
        "api_enabled": True,
        "api_key_count": 0,
        "requests_today": 0,
        "requests_month": 0
    }

def get_usage_summary(user_id: str, workspace_id: str = None, role: str = "user"):
    from datetime import datetime, timezone
    db = get_db()
    now_utc = datetime.now(timezone.utc)
    today_start = datetime(now_utc.year, now_utc.month, now_utc.day, tzinfo=timezone.utc)
    month_start = datetime(now_utc.year, now_utc.month, 1, tzinfo=timezone.utc)

    if role == "superadmin":
        where_clause = "1=1"
        params = []
    elif workspace_id:
        where_clause = "(vj.workspace_id = ? OR vj.user_id = ?)"
        params = [workspace_id, user_id]
    else:
        where_clause = "vj.user_id = ?"
        params = [user_id]

    query = f"""
        SELECT
            COUNT(*) as total_jobs,
            COALESCE(SUM(CASE WHEN vj.created_at >= ? THEN vj.processed_emails ELSE 0 END), 0) as today_verified,
            COALESCE(SUM(CASE WHEN vj.created_at >= ? THEN vj.processed_emails ELSE 0 END), 0) as month_verified,
            COALESCE(SUM(vj.processed_emails), 0) as total_verified,
            COALESCE(SUM(vj.deliverable_count), 0) as total_deliverable,
            MAX(COALESCE(vj.completed_at, vj.created_at)) as last_verif
        FROM verification_jobs vj
        WHERE {where_clause} AND COALESCE(vj.is_deleted, FALSE) = FALSE
    """
    row = db.execute(query, [today_start, month_start] + params).fetchone()

    total_jobs = row[0] or 0
    today_verified = row[1] or 0
    month_verified = row[2] or 0
    total_verified = row[3] or 0
    total_deliverable = row[4] or 0
    last_verification = row[5]

    success_rate = round((total_deliverable / total_verified * 100), 1) if total_verified > 0 else 0.0

    return {
        "verifications_today": today_verified,
        "verifications_month": month_verified,
        "total_verified": total_verified,
        "success_rate": success_rate,
        "last_verification": last_verification.isoformat() if hasattr(last_verification, 'isoformat') else (str(last_verification) if last_verification else None),
        "recent_jobs": total_jobs
    }

def delete_user_account(user_id: str):
    db = get_db()
    user = _select_user_by_id(db, user_id)
    if not user:
        return False
        
    firebase_uid = user[1] # firebase_uid is at index 1 based on _select_user_by_id query

    # Delete related data first
    db.execute("DELETE FROM verification_results WHERE job_id IN (SELECT id FROM verification_jobs WHERE user_id = ?)", [user_id])
    db.execute("DELETE FROM verification_jobs WHERE user_id = ?", [user_id])
    db.execute("DELETE FROM api_keys WHERE user_id = ?", [user_id])
    db.execute("DELETE FROM password_reset_tokens WHERE user_id = ?", [user_id])
    db.execute("DELETE FROM subscriptions WHERE user_id = ?", [user_id])
    db.execute("DELETE FROM payments WHERE user_id = ?", [user_id])
    db.execute("DELETE FROM credit_transactions WHERE user_id = ?", [user_id])
    db.execute("DELETE FROM invoices WHERE user_id = ?", [user_id])
    db.execute("DELETE FROM billing_history WHERE user_id = ?", [user_id])
    
    # Finally, delete user
    db.execute("DELETE FROM users WHERE id = ?", [user_id])
    
    # Delete from Firebase Auth
    if firebase_uid:
        try:
            initialize_firebase()
            firebase_admin.auth.delete_user(firebase_uid)
        except Exception as e:
            # We log but continue, as the DB deletion is the primary concern here
            print(f"Failed to delete Firebase User: {e}")
            
    return True
