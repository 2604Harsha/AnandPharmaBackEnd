from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from core.database import get_db
from core.rbac import require_role
from schemas.notification import NotificationOut
from services.notification_service import get_user_notifications

router = APIRouter(
    prefix="/user/notifications",
    tags=["Notifications"],
)


# =====================================================
# FETCH MY NOTIFICATIONS
# =====================================================

@router.get("/", response_model=List[NotificationOut])
async def fetch_my_notifications(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("user"))
):
    return await get_user_notifications(db, current_user.id)