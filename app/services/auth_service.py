from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.user import User
from core.security import hash_password, verify_password

async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, user):
    new_user = User(
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        password=hash_password(user.password),
        role=user.role
    )
    db.add(new_user)
    await db.commit()
    return new_user

async def authenticate_user(db: AsyncSession, email: str, password: str):
    user = await get_user_by_email(db, email)

    if not user or not verify_password(password, user.password):
        return None

    if not user.is_active:
        return None

    if not user.is_verified:
        raise HTTPException(
            status_code=403,
            detail="Email not verified"
        )

    return user


