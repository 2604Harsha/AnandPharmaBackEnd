from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from core.database import get_db
from core.redis import get_redis
from core.rbac import require_role
from core.websocket_manager import manager   # ✅ ADD THIS

from models.order_address import OrderAddress
from models.delivery import Delivery, DeliveryCancelReason, DeliveryStatus
from models.order import Order, OrderStatus
from models.order_item import OrderItem
from models.user import User

from services.redis_geo_service import RedisGeoService
from services.delivery_otp_redis_service import DeliveryOTPService
from services.email_service import (
    send_delivery_assignment_email,
    send_delivery_otp_email,
    resend_delivery_otp_email,
    send_invoice_email,
)
from services.invoice_service import generate_gst_invoice
from services.eta_service import calculate_eta


router = APIRouter(prefix="/delivery", tags=["Delivery"])


NO_REASSIGN_REASONS = [
    "CUSTOMER_UNREACHABLE",
    "CUSTOMER_CANCELLED",
    "WRONG_ADDRESS"
]

# ======================================================
# 🚚 ASSIGN DELIVERY (ADMIN)
# ======================================================
@router.post("/assign/{order_id}")
async def assign_delivery(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    admin=Depends(require_role("admin", "pharmacist")),
):
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(404, "Order not found")

    if order.status != OrderStatus.READY_FOR_DELIVERY:
        raise HTTPException(
            400,
            f"Order not ready for delivery. Current status: {order.status}"
        )

    address = (
        await db.execute(
            select(OrderAddress).where(OrderAddress.order_id == order_id)
        )
    ).scalar_one_or_none()

    if not address:
        raise HTTPException(400, "Order address missing")

    agent_id = await RedisGeoService.find_nearest_agent(
        redis, address.latitude, address.longitude
    )

    if not agent_id:
        raise HTTPException(404, "No delivery agents nearby")

    agent = await db.get(User, int(agent_id))

    eta = calculate_eta(
        agent.last_latitude,
        agent.last_longitude,
        address.latitude,
        address.longitude,
    )

    delivery = Delivery(
        order_id=order.id,
        delivery_user_id=agent.id,
        status="ASSIGNED",
        assigned_at=datetime.now(timezone.utc),
        eta_minutes=eta,
    )

    db.add(delivery)
    order.status = OrderStatus.OUT_FOR_DELIVERY
    await db.commit()

    await redis.hset(
        f"delivery:order:{order.id}",
        mapping={"agent_id": agent.id, "status": "ASSIGNED"}
    )

    send_delivery_assignment_email(agent.email, order.id)

    return {"message": "Delivery assigned", "agent_id": agent.id, "eta": eta}


# ======================================================
# 📦 PICKUP CONFIRMATION (DELIVERY AGENT)
# ======================================================

@router.post("/pickup/{order_id}")
async def confirm_pickup(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    agent=Depends(require_role("delivery_agent")),
):
    delivery = (
        await db.execute(
            select(Delivery).where(
                Delivery.order_id == order_id,
                Delivery.delivery_user_id == agent.id
            )
        )
    ).scalar_one_or_none()

    if not delivery:
        raise HTTPException(404, "Delivery not found")

    if delivery.status != DeliveryStatus.ASSIGNED:
        raise HTTPException(400, "Pickup already done or invalid state")

    order = await db.get(Order, order_id)

    if order.status not in [
        OrderStatus.READY_FOR_DELIVERY,
        OrderStatus.OUT_FOR_DELIVERY
    ]:
        raise HTTPException(400, "Order not ready for pickup")

    delivery.status = DeliveryStatus.PICKED_UP
    delivery.picked_at = datetime.now(timezone.utc)
    order.status = OrderStatus.OUT_FOR_DELIVERY

    await db.commit()

    # 🔔 Notify customer
    await manager.send_user(
        order.user_id,
        {
            "event": "DELIVERY_PICKED_UP",
            "order_id": order.id,
            "message": "Your order has been picked up"
        }
    )

    return {
        "message": "Pickup confirmed",
        "order_id": order.id,
        "order_status": order.status
    }

# ======================================================
# 🔐 GENERATE OTP
# ======================================================
@router.post("/generate-otp/{order_id}")
async def generate_delivery_otp(
    order_id: int,
    resend: bool = False,
    redis=Depends(get_redis),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role("admin", "delivery_agent")),
):
    otp = await DeliveryOTPService.generate(redis, order_id)

    order = await db.get(Order, order_id)
    customer = await db.get(User, order.user_id)

    if resend:
        resend_delivery_otp_email(customer.email, customer.full_name, otp)
    else:
        send_delivery_otp_email(customer.email, customer.full_name, otp)

    return {"message": "OTP sent", "expires_in": 300}


# ======================================================
# ✅ VERIFY OTP & COMPLETE DELIVERY
# ======================================================
@router.post("/verify-otp/{order_id}")
async def verify_delivery_otp(
    order_id: int,
    otp: str,
    redis=Depends(get_redis),
    db: AsyncSession = Depends(get_db),
    agent=Depends(require_role("delivery_agent")),
):
    if not await DeliveryOTPService.verify(redis, order_id, otp):
        raise HTTPException(400, "Invalid OTP")

    delivery = (
        await db.execute(select(Delivery).where(Delivery.order_id == order_id))
    ).scalar_one_or_none()

    delivery.status = "DELIVERED"
    delivery.delivered_at = datetime.now(timezone.utc)

    order = await db.get(Order, order_id)
    order.status = OrderStatus.DELIVERED

    items = (
        await db.execute(select(OrderItem).where(OrderItem.order_id == order_id))
    ).scalars().all()

    invoice_path = generate_gst_invoice(order, items)
    order.invoice_path = invoice_path

    customer = await db.get(User, order.user_id)
    send_invoice_email(customer.email, order.id, invoice_path)

    await db.commit()
    await redis.hset(f"delivery:order:{order_id}", "status", "DELIVERED")

    # 🔔 PUSH TO CUSTOMER
    await manager.send_user(
        order.user_id,
        {
            "event": "ORDER_DELIVERED",
            "order_id": order.id,
            "message": "Your order has been delivered successfully"
        }
    )

    return {"message": "Order delivered successfully"}


# ======================================================
# ❌ CANCEL DELIVERY (DELIVERY AGENT)
# ======================================================

@router.post("/cancel/{order_id}")
async def cancel_delivery(
    order_id: int,
    reason: DeliveryCancelReason = Query(...),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    agent=Depends(require_role("delivery_agent")),
):
    delivery = (
        await db.execute(
            select(Delivery).where(
                Delivery.order_id == order_id,
                Delivery.delivery_user_id == agent.id
            )
        )
    ).scalar_one_or_none()

    if not delivery:
        raise HTTPException(404, "Delivery not found")

    # ✅ ALLOW cancel AFTER pickup
    if delivery.status in [
        DeliveryStatus.DELIVERED,
        DeliveryStatus.CANCELLED
    ]:
        raise HTTPException(
            400,
            "Delivery cannot be cancelled at this stage"
        )

    delivery.status = DeliveryStatus.CANCELLED
    delivery.cancel_reason = reason
    delivery.cancelled_at = datetime.now(timezone.utc)

    order = await db.get(Order, order_id)

    NO_REASSIGN = {
        DeliveryCancelReason.CUSTOMER_UNREACHABLE,
        DeliveryCancelReason.CUSTOMER_CANCELLED,
        DeliveryCancelReason.WRONG_ADDRESS,
    }

    # ❌ NO REASSIGN → ORDER CANCELLED
    if reason in NO_REASSIGN:
        order.status = OrderStatus.CANCELLED
        await db.commit()

        await manager.send_user(
            order.user_id,
            {
                "event": "ORDER_CANCELLED",
                "order_id": order.id,
                "reason": reason.value,
                "message": "Order cancelled by delivery agent"
            }
        )

        return {
            "message": "Order cancelled",
            "reason": reason.value
        }

    # 🔁 REASSIGN FLOW
    order.status = OrderStatus.READY_FOR_DELIVERY
    await db.commit()

    await manager.send_user(
        order.user_id,
        {
            "event": "DELIVERY_DELAY",
            "order_id": order.id,
            "message": "Delivery agent changed, reassigning"
        }
    )

    address = (
        await db.execute(
            select(OrderAddress).where(OrderAddress.order_id == order_id)
        )
    ).scalar_one_or_none()

    new_agent_id = await RedisGeoService.find_nearest_agent(
        redis,
        address.latitude,
        address.longitude
    )

    if not new_agent_id:
        return {
            "message": "Delivery cancelled. No agents available.",
            "action": "ADMIN_INTERVENTION"
        }

    db.add(
        Delivery(
            order_id=order_id,
            delivery_user_id=int(new_agent_id),
            status=DeliveryStatus.ASSIGNED,
            assigned_at=datetime.now(timezone.utc)
        )
    )

    order.status = OrderStatus.OUT_FOR_DELIVERY
    await db.commit()

    return {
        "message": "Delivery cancelled and reassigned",
        "new_agent_id": new_agent_id
    }

