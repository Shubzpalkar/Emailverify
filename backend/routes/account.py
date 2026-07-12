from fastapi import APIRouter, Depends, HTTPException, status
from auth import get_current_user, UserResponse
from schemas.account import AccountUpdate
from services import account_service

router = APIRouter(prefix="/api/account", tags=["account"])

@router.put("/profile", response_model=UserResponse)
async def update_profile(
    update_data: AccountUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    try:
        updated_user = account_service.update_user_profile(current_user.id, update_data)
        return updated_user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/api-summary")
async def get_api_summary(current_user: UserResponse = Depends(get_current_user)):
    return account_service.get_api_summary(current_user.id)

@router.get("/usage")
async def get_usage_summary(current_user: UserResponse = Depends(get_current_user)):
    return account_service.get_usage_summary(current_user.id)

@router.delete("/")
async def delete_account(current_user: UserResponse = Depends(get_current_user)):
    success = account_service.delete_user_account(current_user.id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete account")
    return {"status": "success", "message": "Account deleted successfully"}
