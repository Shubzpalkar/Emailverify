from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class WorkspaceResponse(BaseModel):
    id: str
    company_name: str
    workspace_slug: str
    company_logo: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    website: Optional[str] = None
    country: Optional[str] = None
    timezone: Optional[str] = None
    language: str
    plan: str
    credits_remaining: int
    credits_used: int
    workspace_status: str
    owner_user_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class WorkspaceSettingsUpdate(BaseModel):
    company_name: Optional[str] = None
    company_logo: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    website: Optional[str] = None
    country: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
