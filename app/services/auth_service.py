from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from schemas.user import DeliveryAgentUpdate
from models.user import User
from core.security import hash_password, verify_password


# ======================================================
# GET USER BY EMAIL
# ======================================================
async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


# ======================================================
# CREATE NORMAL USER
# ======================================================
async def create_user(db: AsyncSession, user):
    new_user = User(
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        password=hash_password(user.password),
        role=user.role,

        address=user.address,
        city=user.city,
        state=user.state,
        pincode=user.pincode,

        # ⭐ important defaults
        is_active=False,
        is_verified=False,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


# ======================================================
# CREATE PHARMACIST
# ======================================================
async def create_pharmacist(db: AsyncSession, data):
    result = await db.execute(select(User).where(User.email == data.email))
    exists = result.scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        full_name=data.full_name,
        email=data.email,
        phone=data.phone,
        password=hash_password(data.password),
        role="pharmacist",

        pharmacy_name=data.pharmacy_name,
        license_no=data.license_no,
        shop_no=data.shop_no,

        # ⭐ defaults
        is_active=False,
        is_verified=False,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


# ======================================================
# CREATE DELIVERY AGENT
# ======================================================
async def create_delivery_agent(db: AsyncSession, data):
    result = await db.execute(select(User).where(User.email == data.email))
    exists = result.scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        full_name=data.full_name,
        email=data.email,
        phone=data.phone,
        password=hash_password(data.password),
        role="delivery_agent",

        vehicle_number=data.vehicle_number,
        vehicle_type=data.vehicle_type,
        rc_no=data.rc_no,
        driving_license_no=data.driving_license_no,

        # ⭐ defaults
        is_active=False,
        is_verified=False,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


# ======================================================
# AUTHENTICATE USER (IMPROVED)
# ======================================================
async def authenticate_user(db: AsyncSession, email: str, password: str):
    user = await get_user_by_email(db, email)

    if not user or not verify_password(password, user.password):
        return None

    if not user.is_verified:
        raise HTTPException(
            status_code=403,
            detail="Email not verified"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Account is inactive"
        )

    return user


# ======================================================
# UPDATE DELIVERY AGENT
# ======================================================
async def update_delivery_agent(db: AsyncSession, user_id: int, data: DeliveryAgentUpdate):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Delivery agent not found")

    if user.role != "delivery_agent":
        raise HTTPException(status_code=400, detail="User is not a delivery agent")

    update_data = data.dict(exclude_unset=True)

    for field, value in update_data.items():
        if field == "password":
            value = hash_password(value)
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    return user