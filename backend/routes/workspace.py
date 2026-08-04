from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from auth import get_current_user, UserResponse, require_superadmin
from middleware.rbac import require_permission
from database import get_db
from schemas.workspace import (
    WorkspaceResponse, WorkspaceSettingsUpdate, WorkspaceGeneralUpdate,
    WorkspaceBrandingUpdate, WorkspaceVerificationSettingsUpdate,
    WorkspaceNotificationSettingsUpdate, WorkspaceSecuritySettingsUpdate,
    WorkspaceDeleteRequest, WorkspaceTeamSummaryResponse, WorkspaceCreditSummaryResponse,
    FullWorkspaceSettingsResponse
)
from services import workspace_service

router = APIRouter(prefix="/api/workspace", tags=["workspace"])


@router.get("/full-settings", response_model=FullWorkspaceSettingsResponse)
async def get_full_workspace_settings(current_user: UserResponse = Depends(require_permission("workspace.view"))):
    if not current_user.workspace_id:
        raise HTTPException(status_code=404, detail="Workspace not found for user")
    try:
        return workspace_service.get_full_workspace_settings(current_user.workspace_id, current_user.role)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=WorkspaceResponse)
async def get_workspace(current_user: UserResponse = Depends(require_permission("workspace.view"))):
    if not current_user.workspace_id:
        raise HTTPException(status_code=404, detail="Workspace not found for user")
    try:
        return workspace_service.get_workspace_row_by_id(get_db(), current_user.workspace_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/settings", response_model=WorkspaceResponse)
async def get_workspace_settings(current_user: UserResponse = Depends(require_permission("workspace.settings"))):
    return await get_workspace(current_user)


@router.put("/general", response_model=WorkspaceResponse)
async def update_general_settings(
    data: WorkspaceGeneralUpdate,
    current_user: UserResponse = Depends(require_permission("workspace.update"))
):
    if not current_user.workspace_id:
        raise HTTPException(status_code=404, detail="Workspace not found")
    try:
        return workspace_service.update_general_settings(current_user.workspace_id, current_user.id, data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/branding/logo")
async def upload_workspace_logo(
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(require_permission("workspace.update"))
):
    if not current_user.workspace_id:
        raise HTTPException(status_code=404, detail="Workspace not found")
    try:
        file_bytes = await file.read()
        logo_url = workspace_service.save_workspace_branding_logo(current_user.workspace_id, current_user.id, file_bytes, file.filename)
        return {"status": "success", "logo_url": logo_url}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/branding", response_model=WorkspaceResponse)
async def update_branding_settings(
    data: WorkspaceBrandingUpdate,
    current_user: UserResponse = Depends(require_permission("workspace.update"))
):
    if not current_user.workspace_id:
        raise HTTPException(status_code=404, detail="Workspace not found")
    try:
        return workspace_service.update_branding_settings(current_user.workspace_id, current_user.id, data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/verification-settings", response_model=WorkspaceVerificationSettingsUpdate)
async def update_verification_settings(
    data: WorkspaceVerificationSettingsUpdate,
    current_user: UserResponse = Depends(require_permission("workspace.update"))
):
    if not current_user.workspace_id:
        raise HTTPException(status_code=404, detail="Workspace not found")
    try:
        return workspace_service.update_verification_settings(current_user.workspace_id, current_user.id, data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/notification-settings", response_model=WorkspaceNotificationSettingsUpdate)
async def update_notification_settings(
    data: WorkspaceNotificationSettingsUpdate,
    current_user: UserResponse = Depends(require_permission("workspace.update"))
):
    if not current_user.workspace_id:
        raise HTTPException(status_code=404, detail="Workspace not found")
    try:
        return workspace_service.update_notification_settings(current_user.workspace_id, current_user.id, data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/security-settings", response_model=WorkspaceResponse)
async def update_security_settings(
    data: WorkspaceSecuritySettingsUpdate,
    current_user: UserResponse = Depends(require_permission("workspace.update"))
):
    if not current_user.workspace_id:
        raise HTTPException(status_code=404, detail="Workspace not found")
    try:
        return workspace_service.update_security_settings(current_user.workspace_id, current_user.id, data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/force-logout-all")
async def force_logout_all_users(current_user: UserResponse = Depends(require_permission("workspace.update"))):
    if not current_user.workspace_id:
        raise HTTPException(status_code=404, detail="Workspace not found")
    try:
        return workspace_service.force_logout_all_users(current_user.workspace_id, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/team-summary", response_model=WorkspaceTeamSummaryResponse)
async def get_team_summary(current_user: UserResponse = Depends(require_permission("workspace.view"))):
    if not current_user.workspace_id:
        raise HTTPException(status_code=404, detail="Workspace not found")
    try:
        return workspace_service.get_team_summary_internal(get_db(), current_user.workspace_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/credit-summary", response_model=WorkspaceCreditSummaryResponse)
async def get_credit_summary(current_user: UserResponse = Depends(require_permission("workspace.view"))):
    if not current_user.workspace_id:
        raise HTTPException(status_code=404, detail="Workspace not found")
    try:
        return workspace_service.get_credit_summary_internal(get_db(), current_user.workspace_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/audit-summary")
async def get_audit_summary(current_user: UserResponse = Depends(require_permission("workspace.view"))):
    if not current_user.workspace_id:
        raise HTTPException(status_code=404, detail="Workspace not found")
    try:
        return workspace_service.get_audit_summary(current_user.workspace_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/delete-danger")
async def delete_workspace_danger(
    req: WorkspaceDeleteRequest,
    current_user: UserResponse = Depends(require_superadmin)
):
    if not current_user.workspace_id:
        raise HTTPException(status_code=404, detail="Workspace not found")
    try:
        workspace_service.delete_workspace(current_user.workspace_id, current_user.id, req.password, req.workspace_name_confirmation)
        return {"status": "success", "message": "Workspace deleted successfully"}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/settings", response_model=WorkspaceResponse)
async def update_workspace_settings(
    settings: WorkspaceSettingsUpdate,
    current_user: UserResponse = Depends(require_permission("workspace.update"))
):
    gen_data = WorkspaceGeneralUpdate(
        company_name=settings.company_name,
        website=settings.website,
        industry=settings.industry,
        company_size=settings.company_size,
        country=settings.country,
        timezone=settings.timezone,
        language=settings.language
    )
    return workspace_service.update_general_settings(current_user.workspace_id, current_user.id, gen_data)


@router.put("", response_model=WorkspaceResponse)
async def update_workspace(
    settings: WorkspaceSettingsUpdate,
    current_user: UserResponse = Depends(require_permission("workspace.update"))
):
    return await update_workspace_settings(settings, current_user)
