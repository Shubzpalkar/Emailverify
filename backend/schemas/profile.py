from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class PersonalInfoUpdate(BaseModel):
    display_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=30)
    job_title: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    employee_id: Optional[str] = Field(None, max_length=50)
    timezone: Optional[str] = Field("UTC", max_length=50)
    language: Optional[str] = Field("en", max_length=10)

class UserPreferencesUpdate(BaseModel):
    theme: Optional[str] = Field("system", pattern="^(light|dark|system)$")
    email_notifications: Optional[bool] = True
    notify_verification_completed: Optional[bool] = True
    notify_credit_alerts: Optional[bool] = True
    notify_team_invites: Optional[bool] = True
    notify_security_alerts: Optional[bool] = True
    download_preference: Optional[str] = Field("CSV", pattern="^(CSV|XLSX|JSON)$")
    verification_preference: Optional[str] = Field("standard", pattern="^(standard|deep)$")

class UserPreferencesResponse(BaseModel):
    theme: str = "system"
    email_notifications: bool = True
    notify_verification_completed: bool = True
    notify_credit_alerts: bool = True
    notify_team_invites: bool = True
    notify_security_alerts: bool = True
    download_preference: str = "CSV"
    verification_preference: str = "standard"
    updated_at: Optional[datetime] = None

class WorkspaceInfoResponse(BaseModel):
    company_name: Optional[str] = "N/A"
    workspace_name: Optional[str] = "N/A"
    current_role: str = "user"
    workspace_plan: str = "Free"
    date_joined: Optional[datetime] = None
    workspace_status: str = "Active"

class AccountMetadataResponse(BaseModel):
    user_id: str
    firebase_uid: Optional[str] = None
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    account_status: str = "Active"
    email_verified: bool = False
    password_last_changed: Optional[datetime] = None

class PersonalInfoResponse(BaseModel):
    id: str
    display_name: Optional[str] = None
    email: str
    phone: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    employee_id: Optional[str] = None
    timezone: str = "UTC"
    language: str = "en"
    avatar_url: Optional[str] = None

class FullProfileResponse(BaseModel):
    personal_info: PersonalInfoResponse
    workspace_info: WorkspaceInfoResponse
    preferences: UserPreferencesResponse
    account_metadata: AccountMetadataResponse

class SessionResponse(BaseModel):
    id: str
    browser: str
    device: str
    ip_address: str
    location: str
    login_time: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    is_current: bool = False

class LoginHistoryResponse(BaseModel):
    id: str
    login_time: Optional[datetime] = None
    browser: str
    device: str
    ip_address: str
    location: str
    status: str
