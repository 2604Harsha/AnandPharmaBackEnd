# services/promo_service.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.promo_code import PromoCode
from schemas.promo_code import PromoCodeCreate, PromoCodeUpdate


async def create_promo(db: AsyncSession, data: PromoCodeCreate):
    promo = PromoCode(**data.dict())
    db.add(promo)
    await db.commit()
    await db.refresh(promo)
    return promo


async def get_all_promos(db: AsyncSession):
    result = await db.execute(select(PromoCode))
    return result.scalars().all()


async def get_promo_by_id(db: AsyncSession, promo_id: int):
    result = await db.execute(
        select(PromoCode).where(PromoCode.id == promo_id)
    )
    return result.scalar_one_or_none()


async def update_promo(db: AsyncSession, promo_id: int, data: PromoCodeUpdate):
    promo = await get_promo_by_id(db, promo_id)
    if not promo:
        return None

    for key, value in data.dict(exclude_unset=True).items():
        setattr(promo, key, value)

    await db.commit()
    await db.refresh(promo)
    return promo


async def delete_promo(db: AsyncSession, promo_id: int):
    promo = await get_promo_by_id(db, promo_id)
    if not promo:
        return None

    await db.delete(promo)
    await db.commit()
    return True