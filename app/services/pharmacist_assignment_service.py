from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from models.user import User
from models.order import Order, OrderStatus
from models.pharmacist_order import PharmacistOrder
from core.websocket_manager import manager
from services.redis_geo_service import RedisGeoService
from core.redis import get_redis

async def assign_nearest_pharmacists(db: AsyncSession, order_id: int):
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.address))
        .where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        return

    pharmacist_ids = []

    # 1️⃣ Try GEO-based matching (BEST)
    if order.address and order.address.latitude and order.address.longitude:
        redis = await get_redis()
        pharmacist_ids = await RedisGeoService.find_nearest_pharmacists(
            redis,
            latitude=order.address.latitude,
            longitude=order.address.longitude
        )

    # 2️⃣ 🔥 FALLBACK — ALWAYS ASSIGN
    if not pharmacist_ids:
        result = await db.execute(
            select(User.id)
            .where(
                User.role == "pharmacist",
                User.is_active == True
            )
        )
        pharmacist_ids = [row[0] for row in result.all()]

    # 3️⃣ Create assignments safely
    for pid in pharmacist_ids:
        exists = await db.execute(
            select(PharmacistOrder)
            .where(
                PharmacistOrder.order_id == order_id,
                PharmacistOrder.pharmacist_id == pid
            )
        )
        if exists.scalar_one_or_none():
            continue

        db.add(
            PharmacistOrder(
                order_id=order_id,
                pharmacist_id=pid,
                status="PENDING"
            )
        )

        await manager.send_pharmacist(
            pid,
            {
                "event": "NEW_ORDER",
                "order_id": order_id,
                "status": "WAITING_PHARMACIST"
            }
        )

    await db.commit()

                

async def notify_next_pharmacist(db: AsyncSession, order_id: int):
    result = await db.execute(
        select(PharmacistOrder)
        .where(
            PharmacistOrder.order_id == order_id,
            PharmacistOrder.status == "PENDING"
        )
        .limit(1)
    )
    po = result.scalar_one_or_none()

    if po:
        await manager.send_pharmacist(
            po.pharmacist_id,
            {
                "event": "NEW_ORDER",
                "order_id": order_id
            }
        )
