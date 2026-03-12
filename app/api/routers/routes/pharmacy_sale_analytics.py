from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import extract, select, func

from core.database import get_db
from core.rbac import require_role
from models.order import Order, OrderStatus
from utils.time_filter import get_time_filter

router = APIRouter(
    prefix="/sales/analytics",
    tags=["Pharmacy Sale Analytics"]
)


@router.get("/monthly-revenue")
async def monthly_revenue(
    range: str = Query("month"),
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("pharmacist"))
):

    time_filter = get_time_filter(range, Order.created_at)

    query = select(func.sum(Order.total)).where(
        Order.status == OrderStatus.DELIVERED
    )

    if time_filter is not None:
        query = query.where(time_filter)

    result = await db.execute(query)

    revenue = result.scalar() or 0

    return {
        "range": range,
        "monthly_revenue": revenue
    }

@router.get("/total-orders")
async def total_orders(
    range: str = Query("month"),
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("pharmacist"))
):

    time_filter = get_time_filter(range, Order.created_at)

    query = select(func.count(Order.id))

    if time_filter is not None:
        query = query.where(time_filter)

    result = await db.execute(query)

    count = result.scalar() or 0

    return {
        "range": range,
        "total_orders": count
    }

@router.get("/avg-order")
async def avg_order(
    range: str = Query("month"),
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("pharmacist"))
):

    time_filter = get_time_filter(range, Order.created_at)

    query = select(func.avg(Order.total)).where(
        Order.status == OrderStatus.DELIVERED
    )

    if time_filter is not None:
        query = query.where(time_filter)

    result = await db.execute(query)

    avg = result.scalar() or 0

    return {
        "range": range,
        "avg_order": round(avg, 2)
    }

@router.get("/satisfaction")
async def satisfaction(
    range: str = Query("month"),
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("pharmacist"))
):

    time_filter = get_time_filter(range, Order.created_at)

    total_query = select(func.count(Order.id))
    delivered_query = select(func.count(Order.id)).where(
        Order.status == OrderStatus.DELIVERED
    )

    if time_filter is not None:
        total_query = total_query.where(time_filter)
        delivered_query = delivered_query.where(time_filter)

    total = await db.scalar(total_query)
    delivered = await db.scalar(delivered_query)

    rate = 0
    if total:
        rate = round((delivered / total) * 100, 1)

    return {
        "range": range,
        "satisfaction": rate
    }

@router.get("/revenue-trend")
async def revenue_trend(
    range: str = Query("year"),
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("pharmacist"))
):

    time_filter = get_time_filter(range, Order.created_at)

    query = (
        select(
            extract("month", Order.created_at).label("month"),
            func.sum(Order.total).label("revenue"),
            func.sum(Order.total * 0.3).label("profit")
        )
        .where(Order.status == OrderStatus.DELIVERED)
    )

    if time_filter is not None:
        query = query.where(time_filter)

    query = query.group_by(
        extract("month", Order.created_at)
    ).order_by(
        extract("month", Order.created_at)
    )

    result = await db.execute(query)

    rows = result.all()

    months = [
        "", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
    ]

    data = []

    for r in rows:
        data.append({
            "month": months[int(r.month)],
            "revenue": float(r.revenue or 0),
            "profit": float(r.profit or 0)
        })

    return {
        "range": range,
        "chart": "Revenue Trend",
        "data": data
    }


@router.get("/daily-performance")
async def daily_performance(
    time_range: str = Query("week"),
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("pharmacist"))
):

    # Apply time filter
    time_filter = get_time_filter(time_range, Order.created_at)

    query = (
        select(
            extract("dow", Order.created_at).label("day"),
            func.count(Order.id).label("orders"),
            func.sum(Order.total).label("sales")
        )
        .where(Order.status == OrderStatus.DELIVERED)
    )

    if time_filter is not None:
        query = query.where(time_filter)

    query = query.group_by(
        extract("dow", Order.created_at)
    )

    result = await db.execute(query)
    rows = result.all()

    # PostgreSQL dow: 0=Sunday
    days = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"]

    # initialize all days
    day_data = {i: {"orders": 0, "sales": 0} for i in range(7)}

    for r in rows:
        day_data[int(r.day)] = {
            "orders": int(r.orders or 0),
            "sales": float(r.sales or 0)
        }

    # convert to ordered list
    data = []
    for i in range(7):
        data.append({
            "day": days[i],
            "orders": day_data[i]["orders"],
            "sales": day_data[i]["sales"]
        })

    return {
        "chart": "Daily Performance",
        "range": time_range,
        "data": data
    }