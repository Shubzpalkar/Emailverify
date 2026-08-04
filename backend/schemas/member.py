from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class MemberResponse(BaseModel):
    id: str
    email: str
    display_name: Optional[str] = None
    role: str
    department: Optional[str] = None
    status: str
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None
    avatar_url: Optional[str] = None

class PaginatedMembersResponse(BaseModel):
    items: List[MemberResponse]
    total: int
    page: int
    size: int
    pages: int

class MemberCreate(BaseModel):
    email: EmailStr
    display_name: str
    role: str
    department: Optional[str] = None

class MemberUpdate(BaseModel):
    role: Optional[str] = None
    department: Optional[str] = None
    status: Optional[str] = None

class InviteCreate(BaseModel):
    email: EmailStr
    role: str = "user"
    department: Optional[str] = None

class InviteResponse(BaseModel):
    id: str
    email: str
    role: str
    department: Optional[str]
    status: str
    token: str
    expires_at: datetime
    created_at: datetime

class AcceptInviteRequest(BaseModel):
    firebase_token: str
