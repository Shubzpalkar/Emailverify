from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
from auth import get_current_user, UserResponse
from middleware.rbac import require_permission, can_manage_role, can_assign_role, ROLE_MAP
from database import get_db
from schemas.member import PaginatedMembersResponse, MemberResponse, MemberCreate, MemberUpdate
import uuid
import math
from datetime import datetime

router = APIRouter(prefix="/api/members", tags=["members"])

def log_audit(db, workspace_id: str, actor_id: str, action: str, target_id: str, details: str):
    log_id = str(uuid.uuid4())
    db.execute("""
        INSERT INTO audit_logs (id, workspace_id, actor_id, action, target_id, details)
        VALUES (?, ?, ?, ?, ?, ?)
    """, [log_id, workspace_id, actor_id, action, target_id, details])

@router.get("", response_model=PaginatedMembersResponse)
def get_members(
    current_user: UserResponse = Depends(require_permission("team.view")),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    department: Optional[str] = None,
    sort_by: Optional[str] = Query("created_at"),
    sort_desc: bool = Query(True)
):
    if not current_user.workspace_id:
        raise HTTPException(status_code=400, detail="User does not belong to a workspace")
        
    db = get_db()
    
    query = '''
        SELECT id, email, display_name, role, department, status, last_login, created_at 
        FROM users 
        WHERE workspace_id = ?
        UNION ALL
        SELECT id, email, NULL as display_name, role, department, status, NULL as last_login, created_at 
        FROM invitations 
        WHERE workspace_id = ? AND status = 'Pending'
    '''
    params = [current_user.workspace_id, current_user.workspace_id]
    
    if search:
        query += " AND (LOWER(email) LIKE ? OR LOWER(display_name) LIKE ?)"
        search_term = f"%{search.lower()}%"
        params.extend([search_term, search_term])
        
    if role:
        query += " AND role = ?"
        params.append(role)
        
    if status:
        query += " AND status = ?"
        params.append(status)
        
    if department:
        query += " AND department = ?"
        params.append(department)
        
    # Count total
    count_query = f"SELECT count(*) FROM ({query})"
    total = db.execute(count_query, params).fetchone()[0]
    
    # Sorting
    allowed_sorts = ["display_name", "email", "role", "department", "status", "last_login", "created_at"]
    if sort_by not in allowed_sorts:
        sort_by = "created_at"
        
    order = "DESC" if sort_desc else "ASC"
    query += f" ORDER BY {sort_by} {order}"
    
    # Pagination
    query += " LIMIT ? OFFSET ?"
    params.extend([size, (page - 1) * size])
    
    rows = db.execute(query, params).fetchall()
    
    items = []
    for row in rows:
        items.append({
            "id": row[0],
            "email": row[1],
            "display_name": row[2],
            "role": row[3],
            "department": row[4],
            "status": row[5],
            "last_login": row[6],
            "created_at": row[7],
            "avatar_url": None
        })
        
    pages = math.ceil(total / size) if size > 0 else 0
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }

@router.post("", response_model=MemberResponse)
def add_member(
    member: MemberCreate,
    current_user: UserResponse = Depends(require_permission("team.invite"))
):
    if not current_user.workspace_id:
        raise HTTPException(status_code=400, detail="User does not belong to a workspace")
        
    if not can_assign_role(current_user.role, member.role):
        raise HTTPException(status_code=403, detail="Cannot assign this role")
        
    db = get_db()
    
    # Check if user exists
    existing = db.execute("SELECT id FROM users WHERE email = ?", [member.email]).fetchone()
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")
        
    user_id = str(uuid.uuid4())
    now = datetime.utcnow()
    role_id = ROLE_MAP.get(member.role, "role_teammember")
    
    db.execute("""
        INSERT INTO users (id, email, display_name, role, role_id, department, workspace_id, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'Active', ?)
    """, [user_id, member.email, member.display_name, member.role, role_id, member.department, current_user.workspace_id, now])
    
    log_audit(db, current_user.workspace_id, current_user.id, "member.added", user_id, f"Added user {member.email} with role {member.role}")
    
    return {
        "id": user_id,
        "email": member.email,
        "display_name": member.display_name,
        "role": member.role,
        "department": member.department,
        "status": 'Active',
        "last_login": None,
        "created_at": now,
        "avatar_url": None
    }

@router.put("/{member_id}", response_model=MemberResponse)
def update_member(
    member_id: str,
    update_data: MemberUpdate,
    current_user: UserResponse = Depends(require_permission("team.change_role"))
):
    if not current_user.workspace_id:
        raise HTTPException(status_code=400, detail="User does not belong to a workspace")
        
    db = get_db()
    
    # Check member exists in this workspace
    member = db.execute("SELECT id, email, display_name, role, department, status, last_login, created_at FROM users WHERE id = ? AND workspace_id = ?", [member_id, current_user.workspace_id]).fetchone()
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
        
    if member_id == current_user.id and update_data.role and update_data.role != member[3]:
        raise HTTPException(status_code=400, detail="Cannot change your own role")
        
    if member_id == current_user.id and update_data.status and update_data.status != member[5]:
        raise HTTPException(status_code=400, detail="Cannot change your own status")
        
    # Role hierarchy: check if actor can manage target's current role
    if not can_manage_role(current_user.role, member[3]):
        raise HTTPException(status_code=403, detail="Cannot modify a member with equal or higher role")
        
    # Role hierarchy: check if actor can assign new role
    if update_data.role is not None:
        if not can_assign_role(current_user.role, update_data.role):
            raise HTTPException(status_code=403, detail="Cannot assign this role")
        
    workspace = db.execute("SELECT owner_user_id FROM workspaces WHERE id = ?", [current_user.workspace_id]).fetchone()
    
    if update_data.role and update_data.role != member[3]:
        # Prevent demoting the workspace owner
        if workspace and workspace[0] == member_id:
            raise HTTPException(status_code=400, detail="Cannot change the role of the workspace owner")
            
        # Prevent demoting the last admin
        if member[3] == "admin":
            admin_count = db.execute("SELECT count(*) FROM users WHERE workspace_id = ? AND role = 'admin' AND status != 'Suspended'", [current_user.workspace_id]).fetchone()[0]
            if admin_count <= 1:
                raise HTTPException(status_code=400, detail="Cannot demote the last admin of the workspace")
        
    # Update fields
    updates = []
    params = []
    
    if update_data.role is not None:
        updates.append("role = ?")
        params.append(update_data.role)
        role_id = ROLE_MAP.get(update_data.role, "role_teammember")
        updates.append("role_id = ?")
        params.append(role_id)
    if update_data.department is not None:
        updates.append("department = ?")
        params.append(update_data.department)
    if update_data.status is not None:
        updates.append("status = ?")
        params.append(update_data.status)
        
    if updates:
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = ? AND workspace_id = ?"
        params.extend([member_id, current_user.workspace_id])
        db.execute(query, params)
        
        log_details = f"Updated: {', '.join([k for k, v in update_data.model_dump(exclude_unset=True).items()])}"
        log_audit(db, current_user.workspace_id, current_user.id, "member.updated", member_id, log_details)
        
    updated_member = db.execute("SELECT id, email, display_name, role, department, status, last_login, created_at FROM users WHERE id = ? AND workspace_id = ?", [member_id, current_user.workspace_id]).fetchone()
    
    return {
        "id": updated_member[0],
        "email": updated_member[1],
        "display_name": updated_member[2],
        "role": updated_member[3],
        "department": updated_member[4],
        "status": updated_member[5],
        "last_login": updated_member[6],
        "created_at": updated_member[7],
        "avatar_url": None
    }

@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    member_id: str,
    current_user: UserResponse = Depends(require_permission("team.remove"))
):
    if not current_user.workspace_id:
        raise HTTPException(status_code=400, detail="User does not belong to a workspace")
        
    if member_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot remove yourself")
        
    db = get_db()
    
    member = db.execute("SELECT email, role FROM users WHERE id = ? AND workspace_id = ?", [member_id, current_user.workspace_id]).fetchone()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
        
    if not can_manage_role(current_user.role, member[1]):
        raise HTTPException(status_code=403, detail="Cannot remove a member with equal or higher role")
        
    workspace = db.execute("SELECT owner_user_id FROM workspaces WHERE id = ?", [current_user.workspace_id]).fetchone()
    if workspace and workspace[0] == member_id:
        raise HTTPException(status_code=400, detail="Cannot remove the workspace owner")
        
    if member[1] == "admin":
        admin_count = db.execute("SELECT count(*) FROM users WHERE workspace_id = ? AND role = 'admin' AND status != 'Suspended'", [current_user.workspace_id]).fetchone()[0]
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="Cannot remove the last admin of the workspace")
        
    db.execute("UPDATE users SET workspace_id = NULL WHERE id = ?", [member_id])
    
    log_audit(db, current_user.workspace_id, current_user.id, "member.removed", member_id, f"Removed user {member[0]} from workspace")
    return None

from schemas.member import InviteCreate, InviteResponse, AcceptInviteRequest
from email_service import EmailService
import secrets
from datetime import timedelta
import firebase_admin.auth

@router.post("/invite", response_model=InviteResponse)
async def invite_member(
    invite: InviteCreate,
    current_user: UserResponse = Depends(require_permission("team.invite"))
):
    if not current_user.workspace_id:
        raise HTTPException(status_code=400, detail="User does not belong to a workspace")
        
    if not can_assign_role(current_user.role, invite.role):
        raise HTTPException(status_code=403, detail="Cannot invite with this role")
        
    db = get_db()
    
    # Check if user already in workspace
    existing_user = db.execute("SELECT id FROM users WHERE email = ? AND workspace_id = ?", [invite.email, current_user.workspace_id]).fetchone()
    if existing_user:
        raise HTTPException(status_code=400, detail="User is already in this workspace")
        
    # Check if pending invite exists
    existing_invite = db.execute("SELECT id FROM invitations WHERE email = ? AND workspace_id = ? AND status = 'Pending'", [invite.email, current_user.workspace_id]).fetchone()
    if existing_invite:
        raise HTTPException(status_code=400, detail="A pending invitation already exists for this email")
        
    invite_id = str(uuid.uuid4())
    token = secrets.token_hex(16)
    now = datetime.utcnow()
    expires_at = now + timedelta(days=7)
    
    db.execute('''
        INSERT INTO invitations (id, workspace_id, email, role, department, token, status, created_by, expires_at, created_at)
        VALUES (?, ?, ?, ?, ?, ?, 'Pending', ?, ?, ?)
    ''', [invite_id, current_user.workspace_id, invite.email, invite.role, invite.department, token, current_user.id, expires_at, now])
    
    log_audit(db, current_user.workspace_id, current_user.id, "invite.created", invite_id, f"Invited {invite.email} as {invite.role}")
    
    # Send email
    workspace_name = db.execute("SELECT company_name FROM workspaces WHERE id = ?", [current_user.workspace_id]).fetchone()[0]
    invite_url = f"http://localhost:5173/accept-invite?token={token}"
    await EmailService.sendInvitationEmail(invite.email, current_user.display_name or current_user.email, workspace_name, invite_url)
    
    return {
        "id": invite_id,
        "email": invite.email,
        "role": invite.role,
        "department": invite.department,
        "status": "Pending",
        "token": token,
        "expires_at": expires_at,
        "created_at": now
    }

@router.post("/resend/{invite_id}", response_model=InviteResponse)
async def resend_invite(
    invite_id: str,
    current_user: UserResponse = Depends(require_permission("team.invite"))
):
    if not current_user.workspace_id:
        raise HTTPException(status_code=400, detail="User does not belong to a workspace")
        
    db = get_db()
    
    invite_row = db.execute("SELECT id, email, role, department, token, expires_at, created_at FROM invitations WHERE id = ? AND workspace_id = ? AND status = 'Pending'", [invite_id, current_user.workspace_id]).fetchone()
    if not invite_row:
        raise HTTPException(status_code=404, detail="Pending invite not found")
        
    # Extend expiration
    now = datetime.utcnow()
    new_expires_at = now + timedelta(days=7)
    db.execute("UPDATE invitations SET expires_at = ? WHERE id = ?", [new_expires_at, invite_id])
    
    workspace_name = db.execute("SELECT company_name FROM workspaces WHERE id = ?", [current_user.workspace_id]).fetchone()[0]
    invite_url = f"http://localhost:5173/accept-invite?token={invite_row[4]}"
    await EmailService.sendInvitationEmail(invite_row[1], current_user.display_name or current_user.email, workspace_name, invite_url)
    
    return {
        "id": invite_row[0],
        "email": invite_row[1],
        "role": invite_row[2],
        "department": invite_row[3],
        "status": "Pending",
        "token": invite_row[4],
        "expires_at": new_expires_at,
        "created_at": invite_row[6]
    }

@router.delete("/invite/{invite_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_invite(
    invite_id: str,
    current_user: UserResponse = Depends(require_permission("team.invite"))
):
    if not current_user.workspace_id:
        raise HTTPException(status_code=400, detail="User does not belong to a workspace")
        
    db = get_db()
    
    invite_row = db.execute("SELECT email FROM invitations WHERE id = ? AND workspace_id = ? AND status = 'Pending'", [invite_id, current_user.workspace_id]).fetchone()
    if not invite_row:
        raise HTTPException(status_code=404, detail="Pending invite not found")
        
    db.execute("UPDATE invitations SET status = 'Cancelled' WHERE id = ?", [invite_id])
    log_audit(db, current_user.workspace_id, current_user.id, "invite.cancelled", invite_id, f"Cancelled invite for {invite_row[0]}")
    return None

@router.get("/invite/validate/{token}")
def validate_invite(token: str):
    db = get_db()
    
    # Check if valid
    invite = db.execute("SELECT id, workspace_id, email, role, expires_at, status FROM invitations WHERE token = ?", [token]).fetchone()
    if not invite:
        raise HTTPException(status_code=404, detail="Invalid token")
        
    if invite[5] != 'Pending':
        raise HTTPException(status_code=400, detail=f"Invitation is already {invite[5]}")
        
    if invite[4] < datetime.utcnow():
        db.execute("UPDATE invitations SET status = 'Expired' WHERE id = ?", [invite[0]])
        raise HTTPException(status_code=400, detail="Invitation has expired")
        
    workspace_name = db.execute("SELECT company_name FROM workspaces WHERE id = ?", [invite[1]]).fetchone()[0]
    
    # Check if user already exists in Firebase
    user_exists = False
    try:
        firebase_admin.auth.get_user_by_email(invite[2])
        user_exists = True
    except:
        pass
        
    return {
        "email": invite[2],
        "workspace_name": workspace_name,
        "role": invite[3],
        "user_exists": user_exists
    }

@router.post("/invite/{token}/accept")
def accept_invite(token: str, req: AcceptInviteRequest):
    db = get_db()
    
    invite = db.execute("SELECT id, workspace_id, email, role, department, expires_at, status FROM invitations WHERE token = ?", [token]).fetchone()
    if not invite:
        raise HTTPException(status_code=404, detail="Invalid token")
        
    if invite[6] != 'Pending':
        raise HTTPException(status_code=400, detail=f"Invitation is already {invite[6]}")
        
    if invite[5] < datetime.utcnow():
        db.execute("UPDATE invitations SET status = 'Expired' WHERE id = ?", [invite[0]])
        raise HTTPException(status_code=400, detail="Invitation has expired")
        
    assigned_role = str(invite[3]).lower().strip()
    if assigned_role == "superadmin" or assigned_role not in ["admin", "manager", "user", "viewer"]:
        raise HTTPException(status_code=400, detail="Invalid invitation role")
        
    # Verify the firebase token sent by the frontend
    try:
        decoded_token = firebase_admin.auth.verify_id_token(req.firebase_token, clock_skew_seconds=300)
        firebase_uid = decoded_token['uid']
        firebase_email = decoded_token.get('email', '')
        display_name = decoded_token.get('name', '')
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
        
    if firebase_email.lower() != invite[2].lower():
        raise HTTPException(status_code=400, detail="Authenticated email does not match invitation email")
        
    # Check if user already in DB
    existing_user = db.execute("SELECT id, workspace_id FROM users WHERE firebase_uid = ? OR email = ?", [firebase_uid, invite[2]]).fetchone()
    now = datetime.utcnow()
    role_id = ROLE_MAP.get(assigned_role, "role_teammember")
    
    if existing_user:
        user_id = existing_user[0]
        # Update workspace and role
        db.execute("UPDATE users SET workspace_id = ?, role = ?, role_id = ?, department = ?, status = 'Active', firebase_uid = ? WHERE id = ?", 
                   [invite[1], assigned_role, role_id, invite[4], firebase_uid, user_id])
    else:
        user_id = str(uuid.uuid4())
        db.execute('''
            INSERT INTO users (id, firebase_uid, email, display_name, role, role_id, department, workspace_id, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Active', ?)
        ''', [user_id, firebase_uid, invite[2], display_name, assigned_role, role_id, invite[4], invite[1], now])
        
    # Mark invite accepted
    db.execute("UPDATE invitations SET status = 'Accepted' WHERE id = ?", [invite[0]])
    log_audit(db, invite[1], user_id, "invite.accepted", invite[0], f"Accepted invite to join workspace")
    
    return {"status": "success", "user_id": user_id, "workspace_id": invite[1]}
