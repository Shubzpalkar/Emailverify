from fastapi import Depends, HTTPException, status, APIRouter, Response, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
import uuid

from config import settings
from database import get_db

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto", pbkdf2_sha256__rounds=30000)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)

router = APIRouter(prefix="/api/auth", tags=["auth"])

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    role: str
    credits: int

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
    user = db.execute("SELECT id, email, role, credits FROM users WHERE id = ?", [user_id]).fetchone()
    if user is None:
        raise credentials_exception
    return UserResponse(id=user[0], email=user[1], role=user[2], credits=user[3])

@router.post("/signup", response_model=UserResponse)
def signup(user: UserCreate):
    db = get_db()
    existing_user = db.execute("SELECT id FROM users WHERE email = ?", [user.email]).fetchone()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    hashed_password = get_password_hash(user.password)
    # Default 100 credits for testing
    db.execute(
        "INSERT INTO users (id, email, password_hash, credits, role) VALUES (?, ?, ?, ?, ?)",
        [user_id, user.email, hashed_password, 100, 'user']
    )
    
    return UserResponse(id=user_id, email=user.email, role='user', credits=100)

@router.post("/login")
def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    db = get_db()
    user = db.execute("SELECT id, email, password_hash, role, credits FROM users WHERE email = ?", [form_data.username]).fetchone()
    if not user or not verify_password(form_data.password, user[2]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user[0]}, expires_delta=access_token_expires
    )
    
    # Remove redundant "Bearer " prefix and set secure=False for local development
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", path="/")
    
    return {"access_token": access_token, "token_type": "bearer", "user": {"id": user[0], "email": user[1], "role": user[3], "credits": user[4]}}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserResponse)
def get_me(current_user: UserResponse = Depends(get_current_user)):
    return current_user
