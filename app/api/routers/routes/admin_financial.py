from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract, and_
import pytz
from core.database import get_db
from core.rbac import require_role
from models.order import Order, OrderStatus

IST = pytz.timezone("Asia/Kolkata")

router = APIRouter(
    prefix="/admin/financial",
    tags=["Admin Financial"]
)

@router.get("/platform-revenue")
async def platform_revenue(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("admin")),
):
    # ✅ Use IST instead of UTC
    now = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(IST)

    current_month_filter = and_(
        extract("year", Order.created_at) == now.year,
        extract("month", Order.created_at) == now.month,
        Order.status == OrderStatus.DELIVERED
    )

    result = await db.execute(
        select(func.coalesce(func.sum(Order.total), 0))
        .where(current_month_filter)
    )

    revenue = float(result.scalar() or 0)

    # ✅ Month format: Jan 2026
    month_label = now.strftime("%b %Y")

    return {
        "title": "Platform Revenue",
        "amount": revenue,
        "period": month_label,
        "currency": "INR"
    }

@router.get("/pharmacy-payouts")
async def pharmacy_payouts(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("admin")),
):
    now = datetime.utcnow()

    current_month_filter = and_(
        extract("year", Order.created_at) == now.year,
        extract("month", Order.created_at) == now.month,
        Order.status == OrderStatus.DELIVERED
    )

    result = await db.execute(
        select(func.coalesce(func.sum(Order.total), 0))
        .where(current_month_filter)
    )

    total_revenue = float(result.scalar() or 0)

    payouts = round(total_revenue * 0.80, 2)

    return {
        "title": "Pharmacy Payouts",
        "amount": payouts,
        "status": "Settled",
        "currency": "INR"
    }

@router.get("/rider-payments")
async def rider_payments(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("admin")),
):
    now = datetime.utcnow()

    current_month_filter = and_(
        extract("year", Order.created_at) == now.year,
        extract("month", Order.created_at) == now.month,
        Order.status == OrderStatus.DELIVERED
    )

    result = await db.execute(
        select(func.count(Order.id))
        .where(current_month_filter)
    )

    delivered_orders = result.scalar() or 0

    rider_total = delivered_orders * 40  # ₹40 per delivery

    return {
        "title": "Rider Payments",
        "amount": rider_total,
        "period": "This Cycle",
        "currency": "INR"
    }

@router.get("/pending-disputes")
async def pending_disputes(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("admin")),
):
    result = await db.execute(
        select(func.count(Order.id))
        .where(Order.status == OrderStatus.DISPUTED)
    )

    disputes = result.scalar() or 0

    return {
        "title": "Pending Disputes",
        "count": disputes,
        "status": "Under Review"
    }