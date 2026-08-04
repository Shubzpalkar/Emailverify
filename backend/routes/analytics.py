from fastapi import APIRouter, Depends, HTTPException, Query
from auth import get_current_user, UserResponse
from middleware.rbac import require_permission
from services import analytics_service

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/overview")
async def get_analytics_overview(
    timeframe: str = Query("30days"),
    current_user: UserResponse = Depends(require_permission("analytics.view"))
):
    try:
        return analytics_service.get_analytics_overview(current_user.id, current_user.workspace_id, current_user.role, timeframe)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/trends")
async def get_analytics_trends(
    timeframe: str = Query("30days"),
    current_user: UserResponse = Depends(require_permission("analytics.view"))
):
    try:
        return analytics_service.get_analytics_trends(current_user.id, current_user.workspace_id, current_user.role, timeframe)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/breakdown")
async def get_analytics_breakdown(
    timeframe: str = Query("30days"),
    current_user: UserResponse = Depends(require_permission("analytics.view"))
):
    try:
        return analytics_service.get_analytics_breakdown(current_user.id, current_user.workspace_id, current_user.role, timeframe)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/domain")
async def get_domain_analytics(
    timeframe: str = Query("30days"),
    current_user: UserResponse = Depends(require_permission("analytics.view"))
):
    try:
        return analytics_service.get_domain_analytics(current_user.id, current_user.workspace_id, current_user.role, timeframe)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/provider")
async def get_provider_analytics(
    timeframe: str = Query("30days"),
    current_user: UserResponse = Depends(require_permission("analytics.view"))
):
    try:
        return analytics_service.get_provider_analytics(current_user.id, current_user.workspace_id, current_user.role, timeframe)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/credits")
async def get_credit_analytics(
    timeframe: str = Query("30days"),
    current_user: UserResponse = Depends(require_permission("analytics.view"))
):
    try:
        return analytics_service.get_credit_analytics(current_user.id, current_user.workspace_id, current_user.role, timeframe)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/team")
async def get_team_analytics(current_user: UserResponse = Depends(require_permission("analytics.view"))):
    if not current_user.workspace_id:
        return {"leaderboard": []}
    try:
        return analytics_service.get_team_analytics(current_user.workspace_id, current_user.role)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/performance")
async def get_performance_analytics(current_user: UserResponse = Depends(require_permission("analytics.view"))):
    try:
        return analytics_service.get_performance_analytics(current_user.id, current_user.workspace_id, current_user.role)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/files")
async def get_file_analytics(current_user: UserResponse = Depends(require_permission("analytics.view"))):
    try:
        return analytics_service.get_file_analytics(current_user.id, current_user.workspace_id, current_user.role)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/comparison")
async def compare_jobs(
    job_a: str = Query(..., description="Job A ID"),
    job_b: str = Query(..., description="Job B ID"),
    current_user: UserResponse = Depends(require_permission("analytics.view"))
):
    try:
        return analytics_service.compare_jobs(job_a, job_b, current_user.id, current_user.workspace_id, current_user.role)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/heatmaps")
async def get_activity_heatmaps(current_user: UserResponse = Depends(require_permission("analytics.view"))):
    try:
        return analytics_service.get_activity_heatmaps(current_user.id, current_user.workspace_id, current_user.role)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/workspace")
async def get_workspace_analytics(current_user: UserResponse = Depends(require_permission("analytics.view"))):
    if not current_user.workspace_id:
        return {}
    try:
        return analytics_service.get_workspace_analytics(current_user.workspace_id, current_user.role)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/system")
async def get_system_analytics(current_user: UserResponse = Depends(require_permission("analytics.view"))):
    try:
        return analytics_service.get_system_analytics(current_user.role)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/export")
async def export_analytics_report(
    format: str = Query("csv"),
    timeframe: str = Query("30days"),
    current_user: UserResponse = Depends(require_permission("analytics.view"))
):
    try:
        overview = analytics_service.get_analytics_overview(current_user.id, current_user.workspace_id, current_user.role, timeframe)
        return {
            "status": "success",
            "format": format,
            "export_url": "/api/analytics/download-report",
            "summary": overview
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
