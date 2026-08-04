from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from auth import get_current_user, UserResponse
from middleware.rbac import require_permission
from services import history_service

router = APIRouter(prefix="/api/verification/jobs", tags=["verification_history"])


class BulkActionRequest(BaseModel):
    action: str
    job_ids: List[str]


@router.get("/summary")
async def get_jobs_summary(current_user: UserResponse = Depends(require_permission("verification.history"))):
    try:
        return history_service.get_jobs_summary(current_user.id, current_user.workspace_id, current_user.role)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("")
async def list_verification_jobs(
    search: Optional[str] = Query("", description="Search term"),
    status: Optional[str] = Query("all", description="Status filter"),
    date: Optional[str] = Query("all", description="Date filter"),
    result: Optional[str] = Query("all", description="Result filter"),
    sort: Optional[str] = Query("newest", description="Sort order"),
    page: int = Query(1, ge=1),
    limit: int = Query(15, ge=1, le=100),
    include_archived: bool = Query(True),
    current_user: UserResponse = Depends(require_permission("verification.history"))
):
    try:
        return history_service.list_verification_jobs(
            current_user.id, current_user.workspace_id, current_user.role,
            search=search, status_filter=status, date_filter=date,
            result_filter=result, sort_by=sort, page=page, limit=limit,
            include_archived=include_archived
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{job_id}")
async def get_job_details(
    job_id: str,
    current_user: UserResponse = Depends(require_permission("verification.history"))
):
    try:
        return history_service.get_job_details(job_id, current_user.id, current_user.workspace_id, current_user.role)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{job_id}/timeline")
async def get_job_timeline(
    job_id: str,
    current_user: UserResponse = Depends(require_permission("verification.history"))
):
    try:
        return history_service.get_job_timeline(job_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{job_id}/statistics")
async def get_job_statistics(
    job_id: str,
    current_user: UserResponse = Depends(require_permission("verification.history"))
):
    try:
        details = history_service.get_job_details(job_id, current_user.id, current_user.workspace_id, current_user.role)
        return details.get("statistics", {})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{job_id}/diagnostics")
async def get_job_diagnostics(
    job_id: str,
    current_user: UserResponse = Depends(require_permission("verification.history"))
):
    try:
        return history_service.get_job_diagnostics(job_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{job_id}/downloads")
async def get_job_downloads(
    job_id: str,
    current_user: UserResponse = Depends(require_permission("verification.history"))
):
    try:
        return history_service.get_job_downloads(job_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{job_id}/retry")
async def retry_job(
    job_id: str,
    current_user: UserResponse = Depends(require_permission("verification.history"))
):
    try:
        return history_service.retry_failed_job(job_id, current_user.id, current_user.workspace_id, current_user.role)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{job_id}/archive")
async def archive_job(
    job_id: str,
    current_user: UserResponse = Depends(require_permission("verification.history"))
):
    try:
        return history_service.archive_job(job_id, current_user.id, current_user.workspace_id, current_user.role)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{job_id}")
async def soft_delete_job(
    job_id: str,
    current_user: UserResponse = Depends(require_permission("verification.history"))
):
    try:
        return history_service.soft_delete_job(job_id, current_user.id, current_user.workspace_id, current_user.role)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk")
async def bulk_job_action(
    req: BulkActionRequest,
    current_user: UserResponse = Depends(require_permission("verification.history"))
):
    try:
        return history_service.bulk_job_action(req.action, req.job_ids, current_user.id, current_user.workspace_id, current_user.role)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
