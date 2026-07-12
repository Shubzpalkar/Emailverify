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

def get_usage_summary(user_id: str):
    db = get_db()
    res = db.execute("SELECT COUNT(*) FROM verification_jobs WHERE user_id = ?", [user_id]).fetchone()
    total_jobs = res[0] if res else 0
    return {
        "verifications_today": 0,
        "verifications_month": 0,
        "total_verified": 0,
        "success_rate": 0.0,
        "last_verification": None,
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
