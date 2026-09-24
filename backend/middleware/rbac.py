from fastapi import Depends, HTTPException
from auth import get_current_user, UserResponse
from database import get_db
import uuid
import logging

logger = logging.getLogger("rbac")

ROLE_HIERARCHY = {
    "viewer": 1,
    "user": 2,
    "manager": 3,
    "admin": 4,
    "superadmin": 5
}

ROLE_MAP = {
    "superadmin": "role_superadmin",
    "admin": "role_companyadmin",
    "manager": "role_manager",
    "user": "role_teammember",
    "viewer": "role_viewer"
}

def get_role_level(role: str) -> int:
    return ROLE_HIERARCHY.get(str(role).lower().strip(), 0)

def can_manage_role(actor_role: str, target_role: str) -> bool:
    """Actor can only manage targets with lower role in hierarchy (admins can manage workspace roles <= 4)."""
    actor_level = get_role_level(actor_role)
    target_level = get_role_level(target_role)
    if actor_level == 5:  # superadmin can manage all
        return True
    if actor_level == 4:  # admin can manage admin, manager, user, viewer
        return 1 <= target_level <= 4
    if actor_level == 3:  # manager can strictly manage user and viewer (< 3)
        return 1 <= target_level < 3
    return False

def can_assign_role(actor_role: str, new_role: str) -> bool:
    """Actor cannot assign superadmin (unless superadmin). Managers can only assign user/viewer."""
    new_level = get_role_level(new_role)
    if new_level <= 0 or new_level >= 5:
        return False
    actor_level = get_role_level(actor_role)
    if actor_level == 5:  # superadmin
        return True
    if actor_level == 4:  # admin can assign admin, manager, user, viewer
        return new_level <= 4
    if actor_level == 3:  # manager can assign user, viewer
        return new_level < 3
    return False

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
            role_id = ROLE_MAP.get(current_user.role, "role_teammember")
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
            logger.warning(f"Permission Denied: User {current_user.id} (role: {current_user.role}) attempted {permission_key}")
            try:
                log_audit(db, current_user.workspace_id or 'SYSTEM', current_user.id, "permission.denied", permission_key, details)
            except Exception as e:
                logger.error(f"Failed to write audit log: {e}")
                
            raise HTTPException(status_code=403, detail="Permission Denied")

        return current_user
    return permission_checker
