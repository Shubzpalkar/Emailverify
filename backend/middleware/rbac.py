from fastapi import Depends, HTTPException
from auth import get_current_user, UserResponse
from database import get_db
import uuid
import logging

logger = logging.getLogger("rbac")

def log_audit(db, workspace_id: str, actor_id: str, action: str, target_id: str, details: str):
    log_id = str(uuid.uuid4())
    db.execute("""
        INSERT INTO audit_logs (id, workspace_id, actor_id, action, target_id, details)
        VALUES (?, ?, ?, ?, ?, ?)
    """, [log_id, workspace_id, actor_id, action, target_id, details])

def require_permission(permission_key: str):
    async def permission_checker(current_user: UserResponse = Depends(get_current_user)):
        db = get_db()
        
        # 1. Ensure user has a role_id
        role_id = db.execute("SELECT role_id FROM users WHERE id = ?", [current_user.id]).fetchone()
        
        # Fallback to map role string to role_id if migration hasn't completed or if newly added
        if not role_id or not role_id[0]:
            if current_user.role == 'superadmin':
                role_id = 'role_superadmin'
            elif current_user.role == 'admin':
                role_id = 'role_companyadmin'
            elif current_user.role == 'manager':
                role_id = 'role_manager'
            elif current_user.role == 'viewer':
                role_id = 'role_viewer'
            else:
                role_id = 'role_teammember'
        else:
            role_id = role_id[0]

        # 2. Check if the role_id has the required permission
        has_perm = db.execute("""
            SELECT 1 
            FROM role_permissions rp
            JOIN permissions p ON rp.permission_id = p.id
            WHERE rp.role_id = ? AND p.key = ?
        """, [role_id, permission_key]).fetchone()

        if not has_perm:
            # 3. Log the failed authorization
            details = f"Denied {permission_key}"
            logger.warning(f"Permission Denied: User {current_user.id} attempted {permission_key}")
            try:
                log_audit(db, current_user.workspace_id or 'SYSTEM', current_user.id, "permission.denied", permission_key, details)
            except Exception as e:
                logger.error(f"Failed to write audit log: {e}")
                
            raise HTTPException(status_code=403, detail="Permission Denied")

        return current_user
    return permission_checker
