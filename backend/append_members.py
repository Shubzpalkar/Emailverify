import os

code_to_append = """
from schemas.member import InviteCreate, InviteResponse, AcceptInviteRequest
from email_service import EmailService
import secrets
from datetime import timedelta
import firebase_admin.auth

@router.post("/invite", response_model=InviteResponse)
async def invite_member(
    invite: InviteCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    if not current_user.workspace_id:
        raise HTTPException(status_code=400, detail="User does not belong to a workspace")
        
    if current_user.role not in ["superadmin", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized to invite members")
        
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
    current_user: UserResponse = Depends(get_current_user)
):
    if not current_user.workspace_id:
        raise HTTPException(status_code=400, detail="User does not belong to a workspace")
        
    if current_user.role not in ["superadmin", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized to resend invites")
        
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
    current_user: UserResponse = Depends(get_current_user)
):
    if not current_user.workspace_id:
        raise HTTPException(status_code=400, detail="User does not belong to a workspace")
        
    if current_user.role not in ["superadmin", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized to cancel invites")
        
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
        
    # Verify the firebase token sent by the frontend
    try:
        decoded_token = firebase_admin.auth.verify_id_token(req.firebase_token)
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
    
    if existing_user:
        user_id = existing_user[0]
        # Update workspace and role
        db.execute("UPDATE users SET workspace_id = ?, role = ?, department = ?, status = 'Active', firebase_uid = ? WHERE id = ?", 
                   [invite[1], invite[3], invite[4], firebase_uid, user_id])
    else:
        user_id = str(uuid.uuid4())
        db.execute('''
            INSERT INTO users (id, firebase_uid, email, display_name, role, department, workspace_id, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Active', ?)
        ''', [user_id, firebase_uid, invite[2], display_name, invite[3], invite[4], invite[1], now])
        
    # Mark invite accepted
    db.execute("UPDATE invitations SET status = 'Accepted' WHERE id = ?", [invite[0]])
    log_audit(db, invite[1], user_id, "invite.accepted", invite[0], f"Accepted invite to join workspace")
    
    return {"status": "success", "user_id": user_id, "workspace_id": invite[1]}
"""

with open("c:/Users/CW250413/Desktop/tool/Emailverify/backend/routes/members.py", "a") as f:
    f.write(code_to_append)

print("Appended members endpoints successfully!")
