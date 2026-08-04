from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request, status
from auth import get_current_user, UserResponse
from schemas.profile import (
    FullProfileResponse, PersonalInfoResponse, PersonalInfoUpdate,
    UserPreferencesResponse, UserPreferencesUpdate, SessionResponse, LoginHistoryResponse
)
from services import profile_service

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("", response_model=FullProfileResponse)
async def get_profile(current_user: UserResponse = Depends(get_current_user)):
    try:
        return profile_service.get_full_profile(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("", response_model=PersonalInfoResponse)
async def update_profile(
    data: PersonalInfoUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    try:
        return profile_service.update_personal_profile(current_user.id, data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user)
):
    try:
        file_bytes = await file.read()
        avatar_url = profile_service.save_user_avatar(current_user.id, file_bytes, file.filename)
        return {"status": "success", "avatar_url": avatar_url}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload avatar: {str(e)}")


@router.get("/preferences", response_model=UserPreferencesResponse)
async def get_preferences(current_user: UserResponse = Depends(get_current_user)):
    try:
        from database import get_db
        return profile_service.get_user_preferences_internal(get_db(), current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/preferences", response_model=UserPreferencesResponse)
async def update_preferences(
    data: UserPreferencesUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    try:
        return profile_service.update_user_preferences(current_user.id, data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions", response_model=list[SessionResponse])
async def get_sessions(
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    try:
        client_ip = request.client.host if request.client else "127.0.0.1"
        user_agent = request.headers.get("User-Agent", "")
        return profile_service.get_active_sessions(current_user.id, client_ip, user_agent)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    try:
        profile_service.revoke_session(current_user.id, session_id)
        return {"status": "success", "message": "Session revoked"}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/login-history", response_model=list[LoginHistoryResponse])
async def get_login_history(current_user: UserResponse = Depends(get_current_user)):
    try:
        return profile_service.get_user_login_history(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/change-password")
async def record_password_change(current_user: UserResponse = Depends(get_current_user)):
    try:
        return profile_service.record_password_changed(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
