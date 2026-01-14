from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update

from core.database import get_db
from core.rbac import require_role
from models.pharmacist_notification import PharmacistNotification


router = APIRouter(prefix="/pharmacist-notifications", tags=["Pharmacist Notifications"])


@router.get("/")
async def list_notifications(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("pharmacist"))
):
    # ✅ fetch all notifications
    result = await db.execute(
        select(PharmacistNotification).order_by(PharmacistNotification.created_at.desc())
    )
    notifs = result.scalars().all()

    # ✅ mark all unseen as seen (when pharmacist opens notifications)
    await db.execute(
        update(PharmacistNotification)
        .where(PharmacistNotification.is_seen == False)
        .values(is_seen=True)
    )
    await db.commit()

    return [
        {
            "id": n.id,
            "refund_request_id": n.refund_request_id,
            "title": n.title,
            "message": n.message,
            "is_seen": True,  # ✅ after GET always show seen=true
            "created_at": n.created_at
        }
        for n in notifs
    ]
