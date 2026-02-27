from datetime import datetime
import pytz


from encodings import aliases

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, func, select, cast, Date, text
from sqlalchemy.orm import aliased

from models.product import Product
from utils.mappers import map_delivery_agent
from schemas.user import DeliveryAgentListResponse, ListResponse, UserListResponse, UserResponse
from core.database import get_db
from core.rbac import require_role

from models.order import Order, OrderStatus
from models.delivery import Delivery
from models.user import User

router = APIRouter(prefix="/admin/analytics", tags=["Admin Analytics"])

IST = pytz.timezone("Asia/Kolkata")
UTC = pytz.utc



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

@router.get("/users/total", response_model=ListResponse)
async def get_total_users(db: AsyncSession = Depends(get_db),admin=Depends(require_role("admin"))):
    # 🔢 Count only role=user
    count_result = await db.execute(
        select(func.count()).where(User.role == "user")
    )
    total_users = count_result.scalar()

    # 📋 Data only role=user
    users_result = await db.execute(
        select(User).where(User.role == "user")
    )
    users = users_result.scalars().all()

    return {
        "count": total_users,
        "users": users
    }

@router.get("/users/active", response_model=ListResponse)
async def get_active_users(db: AsyncSession = Depends(get_db),admin=Depends(require_role("admin"))):
    # 🔢 Count active + role=user
    count_result = await db.execute(
        select(func.count()).where(
            and_(
                User.is_active == True,
                User.role == "user"
            )
        )
    )
    active_users = count_result.scalar()

    # 📋 Data active + role=user
    users_result = await db.execute(
        select(User).where(
            and_(
                User.is_active == True,
                User.role == "user"
            )
        )
    )
    users = users_result.scalars().all()

    return {
        "count": active_users,
        "users": users
    }

@router.get("/pharmacies/total", response_model=UserListResponse)
async def get_total_pharmacies(db: AsyncSession = Depends(get_db),admin=Depends(require_role("admin"))):
    # 🔢 Count role=pharmacist
    count_result = await db.execute(
        select(func.count()).where(User.role == "pharmacist")
    )
    total_pharmacists = count_result.scalar()

    # 📋 Data role=pharmacist
    users_result = await db.execute(
        select(User).where(User.role == "pharmacist")
    )
    pharmacists = users_result.scalars().all()

    return {
        "count": total_pharmacists,
        "users": pharmacists
    }

@router.get("/pharmacies/online", response_model=list[UserResponse])
async def get_online_pharmacies(db: AsyncSession = Depends(get_db),admin=Depends(require_role("admin"))):
    result = await db.execute(
        select(User).where(
            and_(
                User.role == "pharmacist",
                User.is_online == True
            )
        )
    )
    pharmacists = result.scalars().all()
    return pharmacists


@router.get("/pharmacies/offline", response_model=UserListResponse)
async def get_offline_pharmacies(db: AsyncSession = Depends(get_db),admin=Depends(require_role("admin"))):
    # 🔢 Count offline pharmacists
    count_result = await db.execute(
        select(func.count()).where(
            and_(
                User.role == "pharmacist",
                User.is_online == False
            )
        )
    )
    offline_count = count_result.scalar()

    # 📋 Offline pharmacists data
    data_result = await db.execute(
        select(User).where(
            and_(
                User.role == "pharmacist",
                User.is_online == False
            )
        )
    )
    pharmacists = data_result.scalars().all()

    return {
        "count": offline_count,
        "users": pharmacists
    }

@router.get("/delivery-agents/total", response_model=DeliveryAgentListResponse)
async def get_total_delivery_agents(db: AsyncSession = Depends(get_db),admin=Depends(require_role("admin"))):
    # count
    count_result = await db.execute(
        select(func.count()).where(User.role == "delivery_agent")
    )
    total_count = count_result.scalar()

    # data
    result = await db.execute(
        select(User).where(User.role == "delivery_agent")
    )
    agents = result.scalars().all()

    return {
        "count": total_count,
        "users": [map_delivery_agent(u) for u in agents]
    }

@router.get("/delivery-agents/online", response_model=DeliveryAgentListResponse)
async def get_online_delivery_agents(db: AsyncSession = Depends(get_db),admin=Depends(require_role("admin"))):
    count_result = await db.execute(
        select(func.count()).where(
            and_(
                User.role == "delivery_agent",
                User.is_online == True
            )
        )
    )
    online_count = count_result.scalar()

    result = await db.execute(
        select(User).where(
            and_(
                User.role == "delivery_agent",
                User.is_online == True
            )
        )
    )
    agents = result.scalars().all()

    return {
        "count": online_count,
        "users": [map_delivery_agent(u) for u in agents]
    }

@router.get("/delivery-agents/offline", response_model=DeliveryAgentListResponse)
async def get_offline_delivery_agents(db: AsyncSession = Depends(get_db),admin=Depends(require_role("admin"))):
    count_result = await db.execute(
        select(func.count()).where(
            and_(
                User.role == "delivery_agent",
                User.is_online == False
            )
        )
    )
    offline_count = count_result.scalar()

    result = await db.execute(
        select(User).where(
            and_(
                User.role == "delivery_agent",
                User.is_online == False
            )
        )
    )
    agents = result.scalars().all()

    return {
        "count": offline_count,
        "users": [map_delivery_agent(u) for u in agents]
    }


# ======================================================
# GET ALL ORDERS (ADMIN)
# ======================================================
@router.get("/orders")
async def get_all_orders(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin"))
):
    result = await db.execute(select(Order).order_by(Order.id.desc()))
    orders = result.scalars().all()

    return {
        "total": len(orders),
        "orders": orders
    }

# ======================================================
# 📊 MONTHLY REVENUE vs ORDERS (Dashboard Chart)
# ======================================================
@router.get("/revenue/monthly-trends")
async def monthly_revenue_trends(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("admin"))
):
    month_col = func.date_trunc("month", Order.created_at).label("month")

    result = await db.execute(
        select(
            month_col,
            func.count(Order.id).label("orders"),
            func.sum(Order.total).label("revenue"),
        )
        .group_by(month_col)
        .order_by(month_col)
    )

    return [
        {
            "month": month.strftime("%Y-%m"),
            "orders": orders,
            "revenue": revenue or 0,
        }
        for month, orders, revenue in result.all()
    ]

# ======================================================
# 🏆 TOP PHARMACIES
# ======================================================
@router.get("/pharmacies/top")
async def top_pharmacies(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("admin"))
):
    result = await db.execute(
        select(
            User.id,
            User.full_name,
            func.count(Order.id).label("total_orders"),
            func.sum(Order.total).label("total_revenue"),
        )
        .join(Order, Order.pharmacy_id == User.id)
        .where(User.role == "pharmacist")
        .group_by(User.id, User.full_name)
        .order_by(func.count(Order.id).desc())
        .limit(5)
    )

    rows = result.all()

    if not rows:
        return []

    max_orders = rows[0].total_orders or 1

    return [
        {
            "pharmacy_id": r.id,
            "name": r.full_name,
            "orders": r.total_orders,
            "revenue": r.total_revenue or 0,
            "performance": round((r.total_orders / max_orders) * 100, 2),
        }
        for r in rows
    ]


# ======================================================
# 🧾 RECENT ORDERS (LIVE DASHBOARD)
# ======================================================
@router.get("/orders/recent")
async def recent_orders(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("admin")),
):
    pharmacy_user = aliased(User)

    result = await db.execute(
        select(
            Order.id,
            Order.order_number,
            Order.total,
            Order.status,
            Order.created_at,
            User.full_name.label("customer_name"),
            pharmacy_user.full_name.label("pharmacy_name"),
        )
        .join(User, User.id == Order.user_id)
        .join(pharmacy_user, pharmacy_user.id == Order.pharmacy_id)
        .order_by(Order.created_at.desc())
        .limit(limit)
    )

    rows = result.all()

    response = []
    for r in rows:
        # ✅ Safe timezone handling
        order_time = None
        if r.created_at:
            if r.created_at.tzinfo is None:
                # naive → assume UTC
                order_time = (
                    r.created_at.replace(tzinfo=UTC)
                    .astimezone(IST)
                    .strftime("%I:%M %p")
                )
            else:
                # already timezone-aware
                order_time = r.created_at.astimezone(IST).strftime("%I:%M %p")

        response.append(
            {
                "order_id": r.order_number or f"ORD-{r.id}",
                "pharmacy": r.pharmacy_name,
                "customer": r.customer_name,
                "status": r.status.value if r.status else None,
                "amount": r.total,
                "time": order_time,
            }
        )

    return response
# ======================================================
# 🚨 SYSTEM UPDATES (ADMIN DASHBOARD)
# ======================================================
@router.get("/dashboard/system-updates")
async def system_updates(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("admin")),
):
    # 🔴 Low stock products
    low_stock_q = await db.execute(
        select(func.count(Product.id)).where(Product.stock <= 10)
    )
    low_stock_count = low_stock_q.scalar() or 0

    # 🚴 Rider issues (orders stuck in delivery too long)
    rider_issue_q = await db.execute(
        select(func.count(Order.id)).where(
            Order.status == OrderStatus.OUT_FOR_DELIVERY
        )
    )
    rider_issues = rider_issue_q.scalar() or 0

    

    return {
        "low_stock": low_stock_count,
        "rider_issues": rider_issues
    }


# ======================================================
# 📈 DAILY ORDER TRENDS
# ======================================================
@router.get("/dashboard/order-trends")
async def order_trends(
    days: int = 7,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("admin")),
):
    from datetime import datetime, timedelta
    from sqlalchemy import cast, Date

    start_date = datetime.utcnow() - timedelta(days=days)

    result = await db.execute(
        select(
            cast(Order.created_at, Date).label("date"),
            func.count(Order.id).label("orders")
        )
        .where(Order.created_at >= start_date)
        .group_by(cast(Order.created_at, Date))
        .order_by(cast(Order.created_at, Date))
    )

    rows = result.all()

    return [
        {
            "date": str(r.date),
            "orders": r.orders
        }
        for r in rows
    ]


# ======================================================
# 🧪 PRODUCT CATEGORY DISTRIBUTION
# ======================================================
@router.get("/dashboard/product-categories")
async def product_categories(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("admin")),
):
    # 📊 Total products
    total_q = await db.execute(
        select(func.count(Product.id))
    )
    total_products = total_q.scalar() or 0

    if total_products == 0:
        return {
            "prescription": 0,
            "otc": 0,
            "medical_devices": 0,
            "wellness": 0,
        }

    # 💊 Prescription products
    rx_q = await db.execute(
        select(func.count(Product.id)).where(Product.is_rx == True)
    )
    rx_count = rx_q.scalar() or 0

    # 🟢 OTC products
    otc_q = await db.execute(
        select(func.count(Product.id)).where(Product.is_rx == False)
    )
    otc_count = otc_q.scalar() or 0

    # 🩺 Medical devices
    devices_q = await db.execute(
        select(func.count(Product.id)).where(
            Product.category == "medical_devices"
        )
    )
    devices_count = devices_q.scalar() or 0

    # 🌿 Wellness
    wellness_q = await db.execute(
        select(func.count(Product.id)).where(
            Product.category == "wellness"
        )
    )
    wellness_count = wellness_q.scalar() or 0

    # 📈 Convert to percentage
    def pct(x):
        return round((x / total_products) * 100, 2) if total_products else 0

    return {
        "prescription": pct(rx_count),
        "otc": pct(otc_count),
        "medical_devices": pct(devices_count),
        "wellness": pct(wellness_count),
        "total_products": total_products,
    }


# ======================================================
# 📈 REVENUE & ORDERS TREND (MONTHLY)
# ======================================================
@router.get("/dashboard/revenue-orders-trend")
async def revenue_orders_trend(
    months: int = 6,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("admin")),
):
    from datetime import datetime, timedelta
    from sqlalchemy import func, extract

    # 🔹 start date (last N months)
    start_date = datetime.utcnow() - timedelta(days=months * 30)

    result = await db.execute(
        select(
            extract("year", Order.created_at).label("year"),
            extract("month", Order.created_at).label("month"),
            func.count(Order.id).label("orders"),
            func.coalesce(func.sum(Order.total), 0).label("revenue"),
        )
        .where(Order.created_at >= start_date)
        .group_by("year", "month")
        .order_by("year", "month")
    )

    rows = result.all()

    # 📅 Month name helper
    import calendar

    data = []
    for r in rows:
        month_name = calendar.month_abbr[int(r.month)]

        data.append(
            {
                "month": month_name,
                "orders": int(r.orders),
                "revenue": float(r.revenue),
            }
        )

    return data


# ======================================================
# 🏆 TOP PERFORMING PHARMACIES
# ======================================================
@router.get("/dashboard/top-pharmacies")
async def top_pharmacies(
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("admin")),
):
    pharmacy_user = aliased(User)

    result = await db.execute(
        select(
            pharmacy_user.id.label("pharmacy_id"),
            pharmacy_user.full_name.label("pharmacy_name"),
            func.count(Order.id).label("total_orders"),
            func.coalesce(func.sum(Order.total), 0).label("total_revenue"),
        )
        .join(pharmacy_user, pharmacy_user.id == Order.pharmacy_id)
        .group_by(pharmacy_user.id, pharmacy_user.full_name)
        .order_by(func.sum(Order.total).desc())
        .limit(limit)
    )

    rows = result.all()

    # 🔥 compute performance score (simple normalized score)
    max_revenue = max([float(r.total_revenue) for r in rows], default=1)

    data = []
    for idx, r in enumerate(rows, start=1):
        revenue = float(r.total_revenue)
        score = round((revenue / max_revenue) * 100) if max_revenue else 0

        data.append(
            {
                "rank": idx,
                "pharmacy_id": r.pharmacy_id,
                "pharmacy_name": r.pharmacy_name,
                "total_orders": int(r.total_orders),
                "total_revenue": revenue,
                "performance_score": score,
            }
        )

    return data


# ======================================================
# 🌆 CITY PERFORMANCE
# ======================================================
@router.get("/dashboard/city-performance")
async def city_performance(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("admin")),
):
    """
    Revenue + orders grouped by customer city
    Growth % is month-over-month based on revenue
    """

    # ✅ current month revenue per city
    current_month = func.date_trunc("month", func.now())
    prev_month = func.date_trunc(
        "month",
        func.now() - text("interval '1 month'")
    )

    # ---- current month ----
    current_q = await db.execute(
        select(
            User.city.label("city"),
            func.count(Order.id).label("orders"),
            func.coalesce(func.sum(Order.total), 0).label("revenue"),
        )
        .join(User, User.id == Order.user_id)
        .where(
            Order.status == OrderStatus.DELIVERED,
            func.date_trunc("month", Order.created_at) == current_month,
        )
        .group_by(User.city)
    )
    current_rows = {r.city: r for r in current_q.all()}

    # ---- previous month ----
    prev_q = await db.execute(
        select(
            User.city.label("city"),
            func.coalesce(func.sum(Order.total), 0).label("revenue"),
        )
        .join(User, User.id == Order.user_id)
        .where(
            Order.status == OrderStatus.DELIVERED,
            func.date_trunc("month", Order.created_at) == prev_month,
        )
        .group_by(User.city)
    )
    prev_rows = {r.city: r.revenue for r in prev_q.all()}

    # ✅ build response
    data = []
    for city, row in current_rows.items():
        current_rev = float(row.revenue)
        prev_rev = float(prev_rows.get(city, 0))

        # 📈 growth %
        if prev_rev > 0:
            growth = round(((current_rev - prev_rev) / prev_rev) * 100)
        else:
            growth = 0

        data.append(
            {
                "city": city or "Unknown",
                "total_orders": int(row.orders),
                "total_revenue": current_rev,
                "growth_percent": growth,
            }
        )

    # 🔥 sort by revenue desc (matches UI)
    data.sort(key=lambda x: x["total_revenue"], reverse=True)

    return data