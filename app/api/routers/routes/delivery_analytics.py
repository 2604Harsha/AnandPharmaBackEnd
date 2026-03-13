from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from models.order_address import OrderAddress
from models.shipping_address import ShippingAddress
from core.database import get_db
from core.rbac import require_role
from sqlalchemy import extract
from sqlalchemy.orm import aliased

from models.delivery import Delivery
from models.order import Order, OrderStatus
from models.user import User

router = APIRouter(
    prefix="/delivery/analytics",
    tags=["Delivery Analytics"]
)

@router.get("/active-deliveries")
async def active_deliveries(
    db: AsyncSession = Depends(get_db),
    delivery_agent=Depends(require_role("pharmacist"))
):

    result = await db.execute(
        select(func.count(Delivery.id)).where(
            Order.status == "OUT_FOR_DELIVERY"
        )
    )

    count = result.scalar() or 0

    return {
        "title": "Active Deliveries",
        "count": count
    }

@router.get("/pending-assignments")
async def pending_assignments(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("pharmacist"))
):

    count = await db.scalar(
        select(func.count(Order.id)).where(
            and_(
                Order.delivery_agent_id == None,
                Order.status == OrderStatus.WAITING_PHARMACIST
            )
        )
    )

    return {
        "title": "Pending Assignments",
        "count": count or 0
    }



@router.get("/avg-delivery-time")
async def avg_delivery_time(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("pharmacist"))
):

    result = await db.execute(
        select(
            func.avg(
                extract(
                    "epoch",
                    Delivery.delivered_at - Delivery.assigned_at
                )
            )
        ).where(Delivery.status == "DELIVERED")
    )

    seconds = result.scalar() or 0
    minutes = round(seconds / 60)

    return {
        "avg_delivery_time_minutes": minutes
    }


@router.get("/on-time-rate")
async def on_time_rate(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("pharmacist"))
):

    total = await db.scalar(
        select(func.count(Delivery.id)).where(
            Delivery.status == "DELIVERED"
        )
    )

    on_time = await db.scalar(
        select(func.count(Delivery.id)).where(
            and_(
                Delivery.status == "DELIVERED"
            )
        )
    )

    rate = 0
    if total:
        rate = round((on_time / total) * 100)

    return {
        "on_time_rate": rate
    }


@router.get("/list")
async def delivery_list(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("pharmacist"))
):
 
    customer = aliased(User)
    rider = aliased(User)
 
    result = await db.execute(
        select(
            Delivery.id,
            Delivery.delivery_user_id,
            Delivery.status,
            Delivery.picked_at,
 
            Order.id.label("order_id"),
            Order.total,
            Order.delivery_fee,
 
            OrderAddress.address,
 
            customer.full_name.label("customer_name"),
            rider.full_name.label("rider_name"),
            rider.phone.label("rider_phone")
        )
        .select_from(Delivery)
 
        .join(Order, Delivery.order_id == Order.id)
 
        .outerjoin(OrderAddress, OrderAddress.order_id == Order.id)
 
        .join(customer, customer.id == Order.user_id)
 
        .outerjoin(rider, rider.id == Delivery.delivery_user_id)
 
        # ❌ removed status filter
 
        .order_by(Delivery.id.desc())
        .limit(limit)
    )
 
    rows = result.all()
 
    deliveries = []
 
    for r in rows:
        deliveries.append({
            "delivery_id": f"DEL{r.id:04}",
            "order_id": r.order_id,
            "customer": r.customer_name,
            "address": r.address,
            "amount": r.total,
            "delivery_fee": r.delivery_fee,
            "status": r.status,
            "delivery_partner": r.rider_name,
            "phone": r.rider_phone
        })
 
    return deliveries