from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, cast, Date

from core.database import get_db
from core.rbac import require_role

from models.order import Order, OrderStatus
from models.delivery import Delivery
from models.user import User

router = APIRouter(prefix="/admin/analytics", tags=["Admin Analytics"])


# ======================================================
# 1️⃣ DASHBOARD SUMMARY
# ======================================================
@router.get("/summary")
async def analytics_summary(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("admin"))
):
    total_orders = await db.scalar(
        select(func.count()).select_from(Order)
    )

    total_revenue = await db.scalar(
        select(func.sum(Order.total))
        .where(Order.status == OrderStatus.DELIVERED)
    )

    pending_orders = await db.scalar(
        select(func.count())
        .where(Order.status != OrderStatus.DELIVERED)
    )

    delivered_orders = await db.scalar(
        select(func.count())
        .where(Order.status == OrderStatus.DELIVERED)
    )

    return {
        "total_orders": total_orders or 0,
        "delivered_orders": delivered_orders or 0,
        "pending_orders": pending_orders or 0,
        "total_revenue": total_revenue or 0
    }


# ======================================================
# 2️⃣ ORDERS BY STATUS
# ======================================================
@router.get("/orders-by-status")
async def orders_by_status(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("admin"))
):
    result = await db.execute(
        select(Order.status, func.count())
        .group_by(Order.status)
    )

    return {status.value: count for status, count in result.all()}


# ======================================================
# 3️⃣ DAILY REVENUE
# ======================================================
@router.get("/revenue/daily")
async def daily_revenue(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("admin"))
):
    result = await db.execute(
        select(
            cast(Order.created_at, Date),
            func.sum(Order.total)
        )
        .where(Order.status == OrderStatus.DELIVERED)
        .group_by(cast(Order.created_at, Date))
        .order_by(cast(Order.created_at, Date))
    )

    return [
        {"date": str(date), "revenue": revenue or 0}
        for date, revenue in result.all()
    ]


# ======================================================
# 4️⃣ MONTHLY REVENUE
# ======================================================
@router.get("/revenue/monthly")
async def monthly_revenue(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("admin"))
):
    month_col = func.date_trunc("month", Order.created_at).label("month")

    result = await db.execute(
        select(
            month_col,
            func.sum(Order.total).label("revenue")
        )
        .where(Order.status == OrderStatus.DELIVERED)
        .group_by(month_col)
        .order_by(month_col)
    )

    return [
        {
            "month": month.strftime("%Y-%m"),
            "revenue": revenue or 0
        }
        for month, revenue in result.all()
    ]

# ======================================================
# 5️⃣ DELIVERY STATUS ANALYTICS
# ======================================================
@router.get("/deliveries/summary")
async def delivery_summary(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("admin"))
):
    total = await db.scalar(select(func.count()).select_from(Delivery))

    assigned = await db.scalar(
        select(func.count()).where(Delivery.status == "ASSIGNED")
    )

    delivered = await db.scalar(
        select(func.count()).where(Delivery.status == "DELIVERED")
    )

    return {
        "total_deliveries": total or 0,
        "assigned": assigned or 0,
        "delivered": delivered or 0
    }


# ======================================================
# 6️⃣ TOP DELIVERY AGENTS (PERFORMANCE)
# ======================================================
@router.get("/delivery-agents/top")
async def top_delivery_agents(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("admin"))
):
    result = await db.execute(
        select(
            User.id,
            User.full_name,
            func.count(Delivery.id).label("deliveries")
        )
        .join(Delivery, Delivery.delivery_user_id == User.id)
        .where(User.role == "delivery_agent")
        .group_by(User.id)
        .order_by(func.count(Delivery.id).desc())
        .limit(10)
    )

    return [
        {
            "agent_id": agent_id,
            "agent_name": name,
            "deliveries": deliveries
        }
        for agent_id, name, deliveries in result.all()
    ]


# ======================================================
# 7️⃣ ACTIVE DELIVERY AGENTS (LIVE MAP)
# ======================================================
@router.get("/delivery-agents/live")
async def live_delivery_agents(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("admin"))
):
    result = await db.execute(
        select(
            User.id,
            User.full_name,
            User.last_latitude,
            User.last_longitude,
            User.last_location_at
        )
        .where(
            User.role == "delivery_agent",
            User.is_active == True,
            User.last_latitude.isnot(None),
            User.last_longitude.isnot(None),
        )
    )

    return [
        {
            "agent_id": id,
            "name": name,
            "lat": lat,
            "lng": lng,
            "last_updated": str(last_at)
        }
        for id, name, lat, lng, last_at in result.all()
    ]
