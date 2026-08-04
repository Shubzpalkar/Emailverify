from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class WorkspaceResponse(BaseModel):
    id: str
    company_name: str
    workspace_name: Optional[str] = None
    workspace_slug: str
    company_logo: Optional[str] = None
    workspace_logo: Optional[str] = None
    brand_color: Optional[str] = "#3b82f6"
    favicon_url: Optional[str] = None
    email_logo: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    website: Optional[str] = None
    country: Optional[str] = None
    timezone: Optional[str] = "UTC"
    language: str = "en"
    plan: str = "Free"
    credits_remaining: int = 0
    credits_used: int = 0
    low_credit_threshold: int = 1000
    workspace_status: str = "Active"
    require_email_verification: bool = True
    allow_google_login: bool = True
    session_timeout: str = "24h"
    last_security_update: Optional[datetime] = None
    owner_user_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class WorkspaceSettingsUpdate(BaseModel):
    company_name: Optional[str] = None
    workspace_name: Optional[str] = None
    company_logo: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    website: Optional[str] = None
    country: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None

class WorkspaceGeneralUpdate(BaseModel):
    company_name: Optional[str] = Field(None, max_length=100)
    workspace_name: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = Field(None, max_length=200)
    industry: Optional[str] = Field(None, max_length=100)
    company_size: Optional[str] = Field(None, max_length=50)
    country: Optional[str] = Field(None, max_length=100)
    timezone: Optional[str] = Field("UTC", max_length=50)
    language: Optional[str] = Field("en", max_length=10)

class WorkspaceBrandingUpdate(BaseModel):
    brand_color: Optional[str] = Field("#3b82f6", pattern="^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$")
    favicon_url: Optional[str] = Field(None, max_length=500)
    email_logo: Optional[str] = Field(None, max_length=500)

class WorkspaceVerificationSettingsUpdate(BaseModel):
    verification_mode: Optional[str] = Field("standard", pattern="^(standard|deep)$")
    download_format: Optional[str] = Field("CSV", pattern="^(CSV|XLSX|JSON)$")
    duplicate_handling: Optional[str] = Field("remove", pattern="^(keep|remove)$")
    catch_all_handling: Optional[str] = Field("include", pattern="^(include|exclude)$")
    role_account_handling: Optional[str] = Field("include", pattern="^(include|exclude)$")
    disposable_handling: Optional[str] = Field("exclude", pattern="^(include|exclude)$")
    confidence_threshold: Optional[int] = Field(70, ge=0, le=100)

class WorkspaceNotificationSettingsUpdate(BaseModel):
    notify_verification_completed: Optional[bool] = True
    notify_credits_low: Optional[bool] = True
    notify_team_invitations: Optional[bool] = True
    notify_security_alerts: Optional[bool] = True
    notify_weekly_reports: Optional[bool] = False
    notify_monthly_reports: Optional[bool] = True
    notify_api_usage_alerts: Optional[bool] = True

class WorkspaceSecuritySettingsUpdate(BaseModel):
    require_email_verification: Optional[bool] = True
    allow_google_login: Optional[bool] = True
    session_timeout: Optional[str] = Field("24h", pattern="^(30m|1h|4h|8h|24h)$")
    low_credit_threshold: Optional[int] = Field(1000, ge=0)

class WorkspaceDeleteRequest(BaseModel):
    password: str
    workspace_name_confirmation: str

class WorkspaceTeamSummaryResponse(BaseModel):
    total_members: int = 1
    active_members: int = 1
    pending_invitations: int = 0
    suspended_members: int = 0

class WorkspaceCreditSummaryResponse(BaseModel):
    total_credits: int = 0
    used_credits: int = 0
    remaining_credits: int = 0
    monthly_usage: int = 0
    low_credit_threshold: int = 1000

class FullWorkspaceSettingsResponse(BaseModel):
    general: WorkspaceResponse
    verification_settings: WorkspaceVerificationSettingsUpdate
    notification_settings: WorkspaceNotificationSettingsUpdate
    team_summary: WorkspaceTeamSummaryResponse
    credit_summary: WorkspaceCreditSummaryResponse
    can_edit: bool = False
    is_superadmin: bool = False
