from fastapi import Depends, HTTPException, status, APIRouter, Response, Request, Header, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
import uuid
import hashlib
import secrets
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature

from config import settings
from database import get_db
from email_service import EmailService

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto", pbkdf2_sha256__rounds=30000)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)

router = APIRouter(prefix="/api/auth", tags=["auth"])
serializer = URLSafeTimedSerializer(settings.SECRET_KEY)

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class UserCreate(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    admin_id: str | None = None
    credit_pool: int
    is_active: bool
    tier: str | None = None

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(request: Request, token: str | None = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Fallback to cookie if token is not in header
    if not token:
        token = request.cookies.get("access_token")
        
    if not token:
        # Check if the token is in the header but oauth2_scheme failed to find it
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            
    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    db = get_db()
    user = db.execute("SELECT id, email, role, admin_id, credit_pool, is_active, tier FROM users WHERE id = ?", [user_id]).fetchone()
    if user is None:
        raise credentials_exception
    if not user[5]:
        raise HTTPException(status_code=403, detail="Account suspended")
        
    return UserResponse(id=user[0], email=user[1], role=user[2], admin_id=user[3], credit_pool=user[4], is_active=user[5], tier=user[6])

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
    
    # Hash the provided key to compare with stored hash
    hashed_key = hashlib.sha256(x_api_key.encode()).hexdigest()
    
    db = get_db()
    api_key_record = db.execute("""
        SELECT user_id, id FROM api_keys WHERE key_hash = ?
    """, [hashed_key]).fetchone()
    
    if not api_key_record:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    
    user_id, key_id = api_key_record
    
    # Correctly handle datetime as DuckDB might require strings or datetime objects depending on its configuration
    # but since database.py uses datetime.now(timezone.utc), we follow that.
    db.execute("UPDATE api_keys SET last_used = ? WHERE id = ?", [datetime.now(timezone.utc), key_id])
    
    user = db.execute("SELECT id, email, role, admin_id, credit_pool, is_active, tier FROM users WHERE id = ?", [user_id]).fetchone()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User associated with this key no longer exists")
    if not user[5]:
        raise HTTPException(status_code=403, detail="Account associated with this key is suspended")
        
    return UserResponse(id=user[0], email=user[1], role=user[2], admin_id=user[3], credit_pool=user[4], is_active=user[5], tier=user[6])

@router.post("/signup", response_model=UserResponse)
def signup(user: UserCreate, background_tasks: BackgroundTasks):
    db = get_db()
    existing_user = db.execute("SELECT id FROM users WHERE email = ?", [user.email]).fetchone()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    hashed_password = get_password_hash(user.password)
    # Default 100 credits for testing
    db.execute(
        "INSERT INTO users (id, email, password_hash, credit_pool, role, tier) VALUES (?, ?, ?, ?, ?, ?)",
        [user_id, user.email, hashed_password, 100, 'user', 'standard']
    )
    
    # Send welcome email
    background_tasks.add_task(EmailService.sendWelcomeEmail, user.email)
    
    return UserResponse(id=user_id, email=user.email, role='user', credit_pool=100, is_active=True, tier='standard')

@router.post("/login")
def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    db = get_db()
    user = db.execute("SELECT id, email, password_hash, role, credit_pool, admin_id, tier, is_active FROM users WHERE email = ?", [form_data.username]).fetchone()
    if not user or not verify_password(form_data.password, user[2]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user[7]:
        raise HTTPException(status_code=403, detail="Account suspended")
        
    # Update last_login
    db.execute("UPDATE users SET last_login = ? WHERE id = ?", [datetime.now(timezone.utc), user[0]])
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user[0], "role": user[3], "admin_id": user[5]}, expires_delta=access_token_expires
    )
    
    # Remove redundant "Bearer " prefix and set secure=False for local development
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", path="/")
    
    return {"access_token": access_token, "token_type": "bearer", "user": {"id": user[0], "email": user[1], "role": user[3], "credit_pool": user[4], "admin_id": user[5], "tier": user[6], "is_active": user[7]}}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserResponse)
def get_me(current_user: UserResponse = Depends(get_current_user)):
    return current_user

@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest, background_tasks: BackgroundTasks):
    db = get_db()
    user = db.execute("SELECT id, email FROM users WHERE email = ?", [req.email]).fetchone()
    if not user:
        # Avoid user enumeration by returning a success message even if email isn't found
        return {"message": "If that email is registered, you will receive a reset link shortly."}
    
    user_id, email = user
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    
    token_id = str(uuid.uuid4())
    db.execute("""
        INSERT INTO password_reset_tokens (id, user_id, token, expires_at, used)
        VALUES (?, ?, ?, ?, FALSE)
    """, [token_id, user_id, token, expires_at])
    
    reset_url = f"http://localhost:5173/reset-password?token={token}"
    
    # Send reset email
    background_tasks.add_task(EmailService.sendPasswordResetEmail, email, reset_url)
    
    return {"message": "If that email is registered, you will receive a reset link shortly."}

@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest):
    db = get_db()
    
    token_record = db.execute("""
        SELECT id, user_id, expires_at, used FROM password_reset_tokens
        WHERE token = ?
    """, [req.token]).fetchone()
    
    if not token_record:
        raise HTTPException(status_code=400, detail="Invalid reset token.")
        
    t_id, user_id, expires_at, used = token_record
    
    now = datetime.now(timezone.utc)
    if expires_at.tzinfo is None:
        now = datetime.now()
        
    if used or expires_at < now:
        raise HTTPException(status_code=400, detail="Reset token has expired or already been used.")
        
    user = db.execute("SELECT id FROM users WHERE id = ?", [user_id]).fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    hashed_password = get_password_hash(req.new_password)
    db.execute("UPDATE users SET password_hash = ? WHERE id = ?", [hashed_password, user_id])
    
    # Delete token to make it single-use
    db.execute("DELETE FROM password_reset_tokens WHERE token = ?", [req.token])
    
    return {"message": "Your password has been reset successfully. Please log in with your new password."}
