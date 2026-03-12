from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import extract, select, func, and_, cast, Date
from datetime import datetime, timedelta
import pytz

from models.order_address import OrderAddress
from models.user import User
from sqlalchemy.orm import aliased
from core.database import get_db
from core.rbac import require_role

from models.order import Order, OrderStatus
from models.product import Product
from models.delivery import Delivery
from models.order_item import OrderItem
from models.product import Product


router = APIRouter(
    prefix="/pharmacy/analytics",
    tags=["Pharmacy Analytics"]
)

IST = pytz.timezone("Asia/Kolkata")

@router.get("/pending-orders")
async def pending_orders(
    db: AsyncSession = Depends(get_db),
    pharmacist=Depends(require_role("pharmacist"))
):

    pharmacy_id = pharmacist.id

    result = await db.execute(
        select(func.count(Order.id)).where(
            and_(
                Order.pharmacy_id == pharmacy_id,
                Order.status != OrderStatus.DELIVERED
            )
        )
    )

    count = result.scalar()

    return {
        "title": "Pending Orders",
        "count": count or 0
    }

@router.get("/today-revenue")
async def todays_revenue(
    db: AsyncSession = Depends(get_db),
    pharmacist=Depends(require_role("pharmacist"))
):

    today = datetime.now(IST).date()

    revenue = await db.scalar(
        select(func.sum(Order.total)).where(
            and_(
                Order.pharmacy_id == pharmacist.id,
                Order.status == OrderStatus.DELIVERED,
                cast(Order.created_at, Date) == today
            )
        )
    )

    return {
        "title": "Today's Revenue",
        "amount": revenue or 0,
        "currency": "INR"
    }


@router.get("/active-deliveries")
async def active_deliveries(
    db: AsyncSession = Depends(get_db),
    pharmacist=Depends(require_role("pharmacist"))
):

    count = await db.scalar(
        select(func.count(Delivery.id))
        .join(Order, Delivery.order_id == Order.id)
        .where(
            and_(
                Order.pharmacy_id == pharmacist.id,
                Delivery.status != "DELIVERED"
            )
        )
    )

    return {
        "title": "Active Deliveries",
        "count": count or 0
    }

@router.get("/low-stock-items")
async def low_stock_items(
    db: AsyncSession = Depends(get_db),
    pharmacist=Depends(require_role("pharmacist"))
):

    count = await db.scalar(
        select(func.count(Product.id)).where(
            and_(
                Product.pharmacy_id == pharmacist.id,
                Product.stock <= 10
            )
        )
    )

    return {
        "title": "Low Stock Items",
        "count": count or 0
    }



# ======================================================
# 📈 REVENUE TREND (LAST 7 DAYS)
# ======================================================
@router.get("/revenue-trend")
async def revenue_trend(
    db: AsyncSession = Depends(get_db),
    pharmacist=Depends(require_role("pharmacist"))
):

    pharmacy_id = pharmacist.id

    start_date = datetime.utcnow() - timedelta(days=7)

    result = await db.execute(
        select(
            cast(Order.created_at, Date).label("date"),
            func.count(Order.id).label("orders"),
            func.coalesce(func.sum(Order.total), 0).label("revenue")
        )
        .where(
            and_(
                Order.pharmacy_id == pharmacy_id,
                Order.status == OrderStatus.DELIVERED,
                Order.created_at >= start_date
            )
        )
        .group_by(cast(Order.created_at, Date))
        .order_by(cast(Order.created_at, Date))
    )

    rows = result.all()

    data = []

    for r in rows:
        data.append({
            "date": str(r.date),
            "orders": int(r.orders),
            "revenue": float(r.revenue)
        })

    return data


@router.get("/customer-growth")
async def customer_growth(
    db: AsyncSession = Depends(get_db),
    pharmacist=Depends(require_role("pharmacist"))
):

    result = await db.execute(
        select(
            extract("month", Order.created_at).label("month"),
            func.count(func.distinct(Order.user_id)).label("new_customers"),
            func.count(Order.id).label("returning_orders")
        )
        .where(Order.pharmacy_id == pharmacist.id)
        .group_by("month")
        .order_by("month")
    )

    rows = result.all()

    import calendar

    data = []

    for r in rows:
        data.append({
            "month": calendar.month_abbr[int(r.month)],
            "new_customers": int(r.new_customers),
            "returning_customers": int(r.returning_orders)
        })

    return data

@router.get("/order-completion-rate")
async def order_completion_rate(
    db: AsyncSession = Depends(get_db),
    pharmacist=Depends(require_role("pharmacist"))
):

    total_orders = await db.scalar(
        select(func.count(Order.id)).where(
            Order.pharmacy_id == pharmacist.id
        )
    )

    delivered_orders = await db.scalar(
        select(func.count(Order.id)).where(
            Order.pharmacy_id == pharmacist.id,
            Order.status == OrderStatus.DELIVERED
        )
    )

    rate = 0
    if total_orders:
        rate = round((delivered_orders / total_orders) * 100)

    return {
        "order_completion_rate": rate
    }


@router.get("/avg-response-time")
async def avg_response_time(
    db: AsyncSession = Depends(get_db),
    pharmacist=Depends(require_role("pharmacist"))
):

    result = await db.execute(
        select(
            func.avg(
                func.extract(
                    "epoch",
                    Order.updated_at - Order.created_at
                )
            )
        )
        .where(Order.pharmacy_id == pharmacist.id)
    )

    avg_seconds = result.scalar() or 0
    avg_minutes = round(avg_seconds / 60)

    return {
        "avg_response_time_minutes": avg_minutes
    }


@router.get("/conversion-rate")
async def conversion_rate(
    db: AsyncSession = Depends(get_db),
    pharmacist=Depends(require_role("pharmacist"))
):

    total_orders = await db.scalar(
        select(func.count(Order.id)).where(
            Order.pharmacy_id == pharmacist.id
        )
    )

    total_users = await db.scalar(
        select(func.count(func.distinct(Order.user_id))).where(
            Order.pharmacy_id == pharmacist.id
        )
    )

    rate = 0
    if total_users:
        rate = round((total_orders / total_users) * 100)

    return {
        "conversion_rate": rate
    }


@router.get("/top-products")
async def top_products(
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
    pharmacist=Depends(require_role("pharmacist"))
):

    current_month = datetime.utcnow().month
    current_year = datetime.utcnow().year

    result = await db.execute(
        select(
            Product.id,
            Product.name,
            func.sum(OrderItem.quantity).label("units_sold"),
            func.sum(OrderItem.quantity * OrderItem.price).label("revenue")
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .where(
            and_(
                Order.pharmacy_id == pharmacist.id,
                Order.status == OrderStatus.DELIVERED,
                extract("month", Order.created_at) == current_month,
                extract("year", Order.created_at) == current_year
            )
        )
        .group_by(Product.id, Product.name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(limit)
    )

    rows = result.all()

    return [
        {
            "product_id": r.id,
            "product_name": r.name,
            "units_sold": int(r.units_sold),
            "revenue": float(r.revenue)
        }
        for r in rows
    ]

@router.get("/restock-alerts")
async def restock_alerts(
    db: AsyncSession = Depends(get_db),
    pharmacist=Depends(require_role("pharmacist"))
):

    result = await db.execute(
        select(func.count(Product.id)).where(
            and_(
                Product.pharmacy_id == pharmacist.id,
                Product.stock <= 10
            )
        )
    )

    count = result.scalar() or 0

    return {
        "critical_items": count
    }

@router.get("/inventory-value")
async def inventory_value(
    db: AsyncSession = Depends(get_db),
    pharmacist=Depends(require_role("pharmacist"))
):

    result = await db.execute(
        select(
            func.sum(Product.stock * Product.price)
        ).where(Product.pharmacy_id == pharmacist.id)
    )

    value = result.scalar() or 0

    return {
        "inventory_value": float(value)
    }


# ======================================================
# 🧾 RECENT ORDERS
# ======================================================
@router.get("/recent-orders")
async def recent_orders(
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
    pharmacist=Depends(require_role("pharmacist"))
):

    customer = aliased(User)

    result = await db.execute(
        select(
            Order.id,
            Order.order_number,
            Order.total,
            Order.status,
            Order.created_at,
            Order.payment_method,
            Order.payment_status,
            OrderAddress.address,
            customer.full_name,
            customer.phone
        )
        .join(customer, customer.id == Order.user_id)
        .outerjoin(OrderAddress, OrderAddress.order_id == Order.id)
        .where(Order.pharmacy_id == pharmacist.id)
        .order_by(Order.created_at.desc())
        .limit(limit)
    )

    rows = result.all()

    orders = []

    for r in rows:

        # -------- Fetch Items from OrderItem table --------
        items_result = await db.execute(
            select(
                OrderItem.product_name,
                OrderItem.quantity
            )
            .where(OrderItem.order_id == r.id)
        )

        item_rows = items_result.all()

        items = []
        for item in item_rows:
            items.append({
                "name": item.product_name,
                "quantity": item.quantity
            })

        # -------- Time Conversion to IST --------
        order_time = r.created_at
        if order_time.tzinfo is None:
            order_time = order_time.replace(tzinfo=pytz.utc)

        order_time = order_time.astimezone(IST)
        time_diff = datetime.now(IST) - order_time

        if time_diff.seconds < 3600:
            time_ago = f"{time_diff.seconds // 60} min ago"
        else:
            time_ago = f"{time_diff.seconds // 3600} hour ago"

        orders.append({
            "order_id": r.order_number or f"ORD{r.id:03}",
            "customer_name": r.full_name,
            "phone": r.phone,

            "items_count": len(items),
            "items": items,

            "amount": r.total,
            "status": r.status.value if r.status else None,

            "payment_method": r.payment_method,
            "payment_status": r.payment_status,

            "delivery_address": r.address,

            "created_at": order_time.isoformat(),
            "time": time_ago
        })

    return orders