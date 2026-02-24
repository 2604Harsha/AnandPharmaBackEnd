from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func

from core.database import async_session_maker
from models.user import User
from models.notification import Notification


# =====================================================
# SEND CAMPAIGN NOTIFICATION (BACKGROUND SAFE)
# =====================================================

async def send_campaign_notification(title: str, message: str):
    """
    Sends notification to all users with role='user'
    Background-task safe (creates its own DB session)
    """

    async with async_session_maker() as db:
        # ✅ CASE-INSENSITIVE ROLE MATCH (VERY IMPORTANT)
        result = await db.execute(
            select(User.id).where(func.lower(User.role) == "user")
        )
        user_ids = result.scalars().all()

        if not user_ids:
            print("⚠️ No users found with role=user")
            return

        notifications = [
            Notification(
                user_id=user_id,
                title=title,
                message=message,
            )
            for user_id in user_ids
        ]

        db.add_all(notifications)

        # ✅ IMPORTANT FOR ASYNC SQLALCHEMY
        await db.flush()
        await db.commit()

        print(f"✅ Sent {len(notifications)} notifications")

async def get_user_notifications(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
    )
    notifications = result.scalars().all()

    return notifications