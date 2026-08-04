from fastapi import APIRouter, Depends, HTTPException, status
from auth import get_current_user, UserResponse
from middleware.rbac import require_permission
from database import get_db
from schemas.workspace import WorkspaceResponse, WorkspaceSettingsUpdate

router = APIRouter(prefix="/api/workspace", tags=["workspace"])

def _row_to_workspace(row) -> WorkspaceResponse:
    if not row:
        return None
    return WorkspaceResponse(
        id=row[0],
        company_name=row[1],
        workspace_slug=row[2],
        company_logo=row[3],
        industry=row[4],
        company_size=row[5],
        website=row[6],
        country=row[7],
        timezone=row[8],
        language=row[9],
        plan=row[10],
        credits_remaining=row[11],
        credits_used=row[12],
        workspace_status=row[13],
        owner_user_id=row[14],
        created_at=row[15],
        updated_at=row[16]
    )

@router.get("", response_model=WorkspaceResponse)
async def get_workspace(current_user: UserResponse = Depends(require_permission("workspace.view"))):
    db = get_db()
    if not current_user.workspace_id:
        raise HTTPException(status_code=404, detail="Workspace not found for this user")
    
    row = db.execute("""
        SELECT id, company_name, workspace_slug, company_logo, industry, company_size, website, country, timezone, language, plan, credits_remaining, credits_used, workspace_status, owner_user_id, created_at, updated_at
        FROM workspaces
        WHERE id = ?
    """, [current_user.workspace_id]).fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    return _row_to_workspace(row)


@router.get("/settings", response_model=WorkspaceResponse)
async def get_workspace_settings(current_user: UserResponse = Depends(require_permission("workspace.settings"))):
    # Settings and general info are essentially all fetched from the same table right now
    return await get_workspace(current_user)


@router.put("/settings", response_model=WorkspaceResponse)
async def update_workspace_settings(
    settings: WorkspaceSettingsUpdate,
    current_user: UserResponse = Depends(require_permission("workspace.update"))
):
    db = get_db()
    if not current_user.workspace_id:
        raise HTTPException(status_code=404, detail="Workspace not found for this user")

    # Get workspace to check ownership
    workspace = db.execute("SELECT owner_user_id FROM workspaces WHERE id = ?", [current_user.workspace_id]).fetchone()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    update_fields = []
    params = []
    
    settings_dict = settings.model_dump(exclude_unset=True)
    if not settings_dict:
        return await get_workspace(current_user)
        
    for key, value in settings_dict.items():
        update_fields.append(f"{key} = ?")
        params.append(value)
        
    params.append(current_user.workspace_id)
    
    set_clause = ", ".join(update_fields)
    
    db.execute(f"""
        UPDATE workspaces
        SET {set_clause}, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, params)
    
    return await get_workspace(current_user)

@router.put("", response_model=WorkspaceResponse)
async def update_workspace(
    settings: WorkspaceSettingsUpdate,
    current_user: UserResponse = Depends(require_permission("workspace.update"))
):
    return await update_workspace_settings(settings, current_user)
