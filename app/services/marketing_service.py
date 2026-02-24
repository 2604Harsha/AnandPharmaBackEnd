from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, date

from models.campaign import Campaign
from models.promo_code import PromoCode
from models.notification import Notification
from models.order import Order


# =====================================================
# ACTIVE CAMPAIGNS
# =====================================================

async def get_active_campaigns_count(db: AsyncSession):
    result = await db.execute(
        select(func.count()).where(Campaign.is_active == 1)  # ✅ FIX
    )
    return result.scalar() or 0


# =====================================================
# PUSH SENT TODAY
# =====================================================

async def get_push_sent_today(db: AsyncSession):
    today_start = datetime.combine(date.today(), datetime.min.time())

    result = await db.execute(
        select(func.count()).where(Notification.created_at >= today_start)
    )
    return result.scalar() or 0


# =====================================================
# ACTIVE COUPONS
# =====================================================

async def get_active_coupons_count(db: AsyncSession):
    result = await db.execute(
        select(func.count()).where(PromoCode.status == "active")  # ✅ FIX
    )
    return result.scalar() or 0


# =====================================================
# CONVERSION RATE
# =====================================================

async def get_conversion_rate(db: AsyncSession):
    total_orders_result = await db.execute(
        select(func.count()).select_from(Order)
    )
    total_orders = total_orders_result.scalar() or 0

    converted_orders_result = await db.execute(
        select(func.count()).where(Order.promo_code_id.is_not(None))
    )
    converted_orders = converted_orders_result.scalar() or 0

    if total_orders == 0:
        return 0.0

    return round((converted_orders / total_orders) * 100, 1)