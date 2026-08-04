from datetime import datetime, timedelta, timezone
import hashlib
import uuid

from fastapi import Depends, Header, HTTPException, APIRouter, Response, status
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from config import settings
from database import get_db
from middleware.firebase_auth import FirebaseUser, verify_firebase_token

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto", pbkdf2_sha256__rounds=30000)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class UserResponse(BaseModel):
    id: str
    firebase_uid: str | None = None
    email: str
    display_name: str | None = None
    role: str
    plan: str = "Free"
    credits: int = 0
    status: str = "Active"
    created_at: datetime | None = None
    last_login: datetime | None = None
    email_verified: bool = False
    admin_id: str | None = None
    credit_pool: int
    is_active: bool
    tier: str | None = None
    company: str | None = None
    phone: str | None = None
    workspace_id: str | None = None


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def _row_to_user(row) -> UserResponse:
    return UserResponse(
        id=row[0],
        firebase_uid=row[1],
        email=row[2],
        display_name=row[3],
        role=row[4],
        plan=row[5] or "Free",
        credits=row[6] or 0,
        status=row[7] or "Active",
        created_at=row[8],
        last_login=row[9],
        email_verified=bool(row[10]),
        admin_id=row[11],
        credit_pool=row[12] or 0,
        is_active=bool(row[13]),
        tier=row[14],
        company=row[15] if len(row) > 15 else None,
        phone=row[16] if len(row) > 16 else None,
        workspace_id=row[17] if len(row) > 17 else None,
    )


def _select_user_by_id(db, user_id: str):
    return db.execute("""
        SELECT id, firebase_uid, email, display_name, role, plan, credits, status,
               created_at, last_login, email_verified, admin_id, credit_pool,
               is_active, tier, company, phone, workspace_id
        FROM users
        WHERE id = ?
    """, [user_id]).fetchone()


def _select_user_by_firebase_or_email(db, firebase_user: FirebaseUser):
    user = db.execute("""
        SELECT id, firebase_uid, email, display_name, role, plan, credits, status,
               created_at, last_login, email_verified, admin_id, credit_pool,
               is_active, tier, company, phone, workspace_id
        FROM users
        WHERE firebase_uid = ?
    """, [firebase_user.firebase_uid]).fetchone()
    if user:
        return user

    return db.execute("""
        SELECT id, firebase_uid, email, display_name, role, plan, credits, status,
               created_at, last_login, email_verified, admin_id, credit_pool,
               is_active, tier, company, phone, workspace_id
        FROM users
        WHERE lower(email) = lower(?)
    """, [firebase_user.email]).fetchone()


def sync_firebase_user(firebase_user: FirebaseUser) -> UserResponse:
    db = get_db()
    now = datetime.now(timezone.utc)
    existing = _select_user_by_firebase_or_email(db, firebase_user)

    if existing:
        user_id = existing[0]
        current_fb_uid = existing[1]
        workspace_id = existing[17] if len(existing) > 17 else None

        if not workspace_id:
            workspace_id = str(uuid.uuid4())
            slug = f"{firebase_user.display_name or 'workspace'}-{str(uuid.uuid4())[:8]}".lower().replace(" ", "-")
            db.execute("""
                INSERT INTO workspaces (id, company_name, workspace_slug, owner_user_id, credits_remaining, plan)
                VALUES (?, ?, ?, ?, 100, 'Free')
            """, [workspace_id, firebase_user.display_name or "My Workspace", slug, user_id])
            db.execute("UPDATE users SET workspace_id = ? WHERE id = ?", [workspace_id, user_id])

        if current_fb_uid is None:
            try:
                db.execute("""
                    UPDATE users
                    SET firebase_uid = ?,
                        display_name = COALESCE(?, display_name),
                        last_login = ?,
                        email_verified = ?,
                        status = CASE WHEN is_active THEN 'Active' ELSE 'Suspended' END
                    WHERE id = ?
                """, [
                    firebase_user.firebase_uid,
                    firebase_user.display_name,
                    now,
                    firebase_user.email_verified,
                    user_id,
                ])
            except Exception as e:
                db.execute("""
                    UPDATE users
                    SET display_name = COALESCE(?, display_name),
                        last_login = ?,
                        email_verified = ?
                    WHERE id = ?
                """, [
                    firebase_user.display_name,
                    now,
                    firebase_user.email_verified,
                    user_id,
                ])
        else:
            db.execute("""
                UPDATE users
                SET display_name = COALESCE(?, display_name),
                    last_login = ?,
                    email_verified = ?,
                    status = CASE WHEN is_active THEN 'Active' ELSE 'Suspended' END
                WHERE id = ?
            """, [
                firebase_user.display_name,
                now,
                firebase_user.email_verified,
                user_id,
            ])





        return _row_to_user(_select_user_by_id(db, user_id))

    user_id = str(uuid.uuid4())
    workspace_id = str(uuid.uuid4())
    slug = f"{firebase_user.display_name or 'workspace'}-{str(uuid.uuid4())[:8]}".lower().replace(" ", "-")

    db.execute("""
        INSERT INTO workspaces (id, company_name, workspace_slug, owner_user_id, credits_remaining, plan)
        VALUES (?, ?, ?, ?, 100, 'Free')
    """, [workspace_id, firebase_user.display_name or "My Workspace", slug, user_id])

    db.execute("""
        INSERT INTO users (
            id, firebase_uid, email, display_name, role, plan, credits,
            credit_pool, status, is_active, tier, created_at, last_login,
            email_verified, password_hash, workspace_id
        )
        VALUES (?, ?, ?, ?, 'user', 'Free', 100, 100, 'Active', TRUE, 'free', ?, ?, ?, '', ?)
    """, [
        user_id,
        firebase_user.firebase_uid,
        firebase_user.email,
        firebase_user.display_name,
        now,
        now,
        firebase_user.email_verified,
        workspace_id
    ])
    return _row_to_user(_select_user_by_id(db, user_id))



async def get_current_user(firebase_user: FirebaseUser = Depends(verify_firebase_token)):
    user = sync_firebase_user(firebase_user)
    if not user.is_active or user.status.lower() != "active":
        raise HTTPException(status_code=403, detail="Account suspended")
    if not user.email_verified:
        raise HTTPException(status_code=403, detail="Email not verified")
    return user


async def require_superadmin(current_user: UserResponse = Depends(get_current_user)):
    if current_user.role != "superadmin":
        raise HTTPException(status_code=403, detail="Superadmin access required")
    return current_user


async def require_admin(current_user: UserResponse = Depends(get_current_user)):
    if current_user.role not in ("superadmin", "admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


async def require_user(current_user: UserResponse = Depends(get_current_user)):
    return current_user


async def get_api_user(x_api_key: str = Header(None)):
    """Dependency to authenticate users via X-API-Key header."""
    if not x_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="X-API-Key header is missing")

    hashed_key = hashlib.sha256(x_api_key.encode()).hexdigest()
    db = get_db()
    api_key_record = db.execute("""
        SELECT user_id, id FROM api_keys WHERE key_hash = ?
    """, [hashed_key]).fetchone()

    if not api_key_record:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

    user_id, key_id = api_key_record
    db.execute("UPDATE api_keys SET last_used = ? WHERE id = ?", [datetime.now(timezone.utc), key_id])

    user = _select_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User associated with this key no longer exists")

    response = _row_to_user(user)
    if not response.is_active:
        raise HTTPException(status_code=403, detail="Account associated with this key is suspended")
    return response


@router.post("/sync-user", response_model=UserResponse)
async def sync_user(firebase_user: FirebaseUser = Depends(verify_firebase_token)):
    try:
        return sync_firebase_user(firebase_user)
    except Exception as e:
        import traceback
        print(f"[SYNC-USER ERROR]\n{traceback.format_exc()}", flush=True)
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")




@router.get("/me", response_model=UserResponse)
async def get_me(firebase_user: FirebaseUser = Depends(verify_firebase_token)):
    user = sync_firebase_user(firebase_user)
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account suspended")
    return user

@router.get("/permissions")
async def get_my_permissions(current_user: UserResponse = Depends(get_current_user)):
    db = get_db()
    
    role_id = db.execute("SELECT role_id FROM users WHERE id = ?", [current_user.id]).fetchone()
    
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
        
    perms = db.execute("""
        SELECT p.key 
        FROM role_permissions rp
        JOIN permissions p ON rp.permission_id = p.id
        WHERE rp.role_id = ?
    """, [role_id]).fetchall()
    
    return [p[0] for p in perms]


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Logged out successfully"}


@router.post("/refresh")
async def refresh_token(firebase_user: FirebaseUser = Depends(verify_firebase_token)):
    user = sync_firebase_user(firebase_user)
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account suspended")
    return {"status": "ok", "user": user}
