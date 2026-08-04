from fastapi import APIRouter, Depends, HTTPException, Query
from auth import get_current_user, UserResponse
from middleware.rbac import require_permission
from services import dashboard_service

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/welcome")
async def get_welcome_widget(current_user: UserResponse = Depends(require_permission("dashboard.view"))):
    try:
        return dashboard_service.get_welcome_data(current_user.id, current_user.workspace_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/kpi")
async def get_kpi_widget(current_user: UserResponse = Depends(require_permission("dashboard.view"))):
    try:
        return dashboard_service.get_kpi_data(current_user.id, current_user.workspace_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/credits")
async def get_credits_widget(current_user: UserResponse = Depends(require_permission("credits.view"))):
    try:
        return dashboard_service.get_credit_summary(current_user.id, current_user.workspace_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/verification-summary")
async def get_verification_summary_widget(current_user: UserResponse = Depends(require_permission("dashboard.view"))):
    try:
        return dashboard_service.get_verification_summary(current_user.id, current_user.workspace_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/jobs")
async def get_jobs_widget(current_user: UserResponse = Depends(require_permission("dashboard.view"))):
    try:
        return dashboard_service.get_recent_jobs(current_user.id, current_user.workspace_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/analytics")
async def get_analytics_widget(
    timeframe: str = Query("daily"),
    current_user: UserResponse = Depends(require_permission("analytics.view"))
):
    try:
        return dashboard_service.get_analytics_data(current_user.id, current_user.workspace_id, timeframe)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/activity")
async def get_activity_widget(current_user: UserResponse = Depends(require_permission("dashboard.view"))):
    try:
        return dashboard_service.get_recent_activity(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/workspace-activity")
async def get_workspace_activity_widget(current_user: UserResponse = Depends(require_permission("workspace.view"))):
    if not current_user.workspace_id:
        return []
    try:
        return dashboard_service.get_workspace_activity(current_user.workspace_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/notifications")
async def get_notifications_widget(current_user: UserResponse = Depends(require_permission("notifications.view"))):
    try:
        return dashboard_service.get_notifications(current_user.id, current_user.workspace_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/system-health")
async def get_system_health_widget(current_user: UserResponse = Depends(require_permission("dashboard.view"))):
    try:
        return dashboard_service.get_system_health()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/workspace")
async def get_workspace_summary_widget(current_user: UserResponse = Depends(require_permission("workspace.view"))):
    if not current_user.workspace_id:
        return {}
    try:
        return dashboard_service.get_workspace_summary(current_user.workspace_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
