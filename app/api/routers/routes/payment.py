from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.database import get_db
from core.rbac import require_role
from core.razorpay_client import razorpay_client
from core.config import settings
from services.razorpay_service import razorpay_service
from services.pharmacist_assignment_service import assign_nearest_pharmacists
from schemas.payment import CreatePaymentOrder, VerifyPayment
from models.order import Order, OrderStatus
import os
 
router = APIRouter(prefix="/payments", tags=["Payments"])
 
# ======================================================
# CREATE RAZORPAY ORDER (BILLING PAGE)
# ======================================================
@router.post("/create-order")
async def create_payment_order(
    payload: CreatePaymentOrder,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("user"))
):
    order = await db.get(Order, payload.order_id)
 
    if not order:
        raise HTTPException(404, "Order not found")
 
    # ✅ Payment allowed only after address + cart saved
    if order.status != OrderStatus.PENDING:
        raise HTTPException(400, "Order not eligible for payment")
 
    razorpay_order = await razorpay_service.create_order(payload.amount)
 
    order.razorpay_order_id = razorpay_order["id"]
    order.status = OrderStatus.PAYMENT_INITIATED
 
    await db.commit()
 
    return {
        "razorpay_order_id": razorpay_order["id"],
        "razorpay_key": settings.RAZORPAY_KEY_ID,
        "amount": payload.amount,
        "currency": "INR",
    }
 
 
# ======================================================
# VERIFY PAYMENT (THIS IS WHERE PAYMENT BECOMES PAID)
# ======================================================
 
@router.post("/verify")
async def verify_payment(
    payload: VerifyPayment,
    db: AsyncSession = Depends(get_db)
):
    # 🔐 Verify Razorpay signature
    try:
        await razorpay_service.verify_payment(
            payload.razorpay_order_id,
            payload.razorpay_payment_id,
            payload.razorpay_signature,
        )
    except Exception:
        # ❌ Payment verification failed
        return {
            "message": "Payment verification failed",
            "payment_status": "NOT_PAID",
            "payment_result": "FAILED"
        }
 
    # 🔍 Find order
    result = await db.execute(
        select(Order).where(
            Order.razorpay_order_id == payload.razorpay_order_id
        )
    )
    order = result.scalar_one_or_none()
 
    if not order:
        raise HTTPException(404, "Order not found")
 
    # 🟡 Already processed
    if order.payment_status == "SUCCESS":
        return {
            "message": "Payment already processed",
            "payment_status": "PAID",
            "payment_result": "SUCCESS",
            "order_id": order.id,
            "order_status": order.status
        }
 
    # ✅ Mark payment success
    order.razorpay_payment_id = payload.razorpay_payment_id
    order.payment_status = "SUCCESS"
    order.payment_method = "RAZORPAY"
    order.status = OrderStatus.WAITING_PHARMACIST
 
    await db.commit()
    await db.refresh(order)
 
    # 🔔 Notify pharmacists
    await assign_nearest_pharmacists(db, order.id)
 
    return {
        "message": "Payment verified. Pharmacists notified.",
        "payment_status": "PAID",
        "payment_result": "SUCCESS",
        "order_id": order.id,
        "order_status": order.status
    }
 
 