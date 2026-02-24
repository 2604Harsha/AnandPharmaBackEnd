from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.user import User


async def get_user_profile(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def update_user_profile(db: AsyncSession, user: User, data):
    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    return user
