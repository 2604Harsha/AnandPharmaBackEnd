from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from core.rbac import require_role
from models.order import Order, OrderStatus
from models.order_item import OrderItem
from models.order_address import OrderAddress
from models.pharmacist_order import PharmacistOrder
from services.pharmacist_assignment_service import notify_next_pharmacist

router = APIRouter(prefix="/pharmacist_orders", tags=["Pharmacist Orders"])

#=====================================
#Pharmasist check near by orders
#=====================================
@router.get("/nearby-orders")
async def nearby_orders(
    db: AsyncSession = Depends(get_db),
    pharmacist=Depends(require_role("pharmacist"))
):
    result = await db.execute(
        select(PharmacistOrder, Order, OrderAddress)
        .join(Order, Order.id == PharmacistOrder.order_id)
        .join(OrderAddress, OrderAddress.order_id == Order.id)
        .where(
            PharmacistOrder.pharmacist_id == pharmacist.id,
            PharmacistOrder.status == "PENDING"
        )
        .order_by(PharmacistOrder.id.desc())
    )

    orders = []
    for po, order, address in result.all():
        items = (
            await db.execute(
                select(OrderItem)
                .where(OrderItem.order_id == order.id)
            )
        ).scalars().all()

        orders.append({
            "order_id": order.id,
            "pharmacist_order_status": po.status,
            "order_status": order.status,
            "total": order.total,
            "address": address.address,
            "items": [
                {
                    "name": i.product_name,
                    "qty": i.quantity,
                    "price": i.price
                }
                for i in items
            ]
        })

    return {
        "count": len(orders),
        "orders": orders
    }

#=====================================
# pharmasist approval
#=====================================
@router.post("/accept/{order_id}")
async def accept_order(
    order_id: int,
    pharmacist_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(PharmacistOrder)
        .where(
            PharmacistOrder.order_id == order_id,
            PharmacistOrder.pharmacist_id == pharmacist_id
        )
    )
    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(
            404,
            detail="This order was not assigned to this pharmacist"
        )

    if po.status != "PENDING":
        raise HTTPException(
            400,
            detail=f"Order already {po.status.lower()}"
        )

    po.status = "ACCEPTED"

    order = await db.get(Order, order_id)
    order.status = OrderStatus.ACCEPTED

    await db.commit()

    return {"message": "Order accepted successfully"}

# ================================================
# Reject
# ===============================================
@router.post("/reject/{order_id}")
async def reject_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    pharmacist=Depends(require_role("pharmacist"))
):
    po = (
        await db.execute(
            select(PharmacistOrder)
            .where(
                PharmacistOrder.order_id == order_id,
                PharmacistOrder.pharmacist_id == pharmacist.id,
                PharmacistOrder.status == "PENDING"
            )
        )
    ).scalar_one_or_none()

    if not po:
        raise HTTPException(404, "Order not assigned to you")

    po.status = "REJECTED"
    await db.commit()

    await notify_next_pharmacist(db, order_id)

    return {"message": "Order rejected. Notified next pharmasist"}

@router.post("/pack/{order_id}")
async def pack_order(order_id: int, db: AsyncSession = Depends(get_db)):
    order = await db.get(Order, order_id)

    if order.status != OrderStatus.ACCEPTED:
        raise HTTPException(400, "Order not accepted yet")

    order.status = OrderStatus.PACKED
    await db.commit()

    return {"message": "Order packed"}

# =======================================

@router.post("/ready/{order_id}")
async def ready_for_delivery(order_id: int, db: AsyncSession = Depends(get_db)):
    order = await db.get(Order, order_id)

    if order.status != OrderStatus.PACKED:
        raise HTTPException(400, "Order not packed")

    order.status = OrderStatus.READY_FOR_DELIVERY
    await db.commit()

    return {"message": "Order ready for delivery"}

#===========================
# pharmasist get their order
#===========================
@router.get("/my")
async def my_orders(
    db: AsyncSession = Depends(get_db),
    pharmacist=Depends(require_role("pharmacist"))
):
    result = await db.execute(
        select(PharmacistOrder, Order)
        .join(Order, Order.id == PharmacistOrder.order_id)
        .where(
            PharmacistOrder.pharmacist_id == pharmacist.id,
            PharmacistOrder.status.in_(["ACCEPTED"])
        )
        .order_by(PharmacistOrder.id.desc())
    )

    orders = []
    for po, order in result.all():
        items = (
            await db.execute(
                select(OrderItem)
                .where(OrderItem.order_id == order.id)
            )
        ).scalars().all()

        orders.append({
            "order_id": order.id,
            "status": order.status,
            "total": order.total,
            "created_at": order.created_at,
            "items": [
                {
                    "name": i.product_name,
                    "qty": i.quantity,
                    "price": i.price
                }
                for i in items
            ]
        })

    return {
        "count": len(orders),
        "orders": orders
    }
