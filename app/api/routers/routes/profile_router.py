from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.rbac import require_role
from core.database import get_db
from schemas.profile_schema import (
    UserProfileResponse,
    UserProfileUpdate,
)
from services.profile_service import (
    get_user_profile,
    update_user_profile,
)
from models.user import User
from core.dependencies import get_current_user  # 🔥 your auth dependency

router = APIRouter(prefix="/profile", tags=["User Profile"])


# ✅ Get Profile
@router.get("/me", response_model=UserProfileResponse)
async def my_profile(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("user"))
):
    user = await get_user_profile(db, current_user.id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


# ✅ Update Profile
@router.put("/me", response_model=UserProfileResponse)
async def update_profile(
    data: UserProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("user"))
):
    user = await update_user_profile(db, current_user, data)
    return user
