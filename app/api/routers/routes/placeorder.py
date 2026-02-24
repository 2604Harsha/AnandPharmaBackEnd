from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.rbac import require_role
from models.order import Order, OrderStatus

router = APIRouter(prefix="/orders", tags=["Orders"])


# ======================================================
# PLACE ORDER (FINAL STEP)
# ======================================================
@router.post("/place-order/{order_id}")
async def place_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role("user")),
):
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(404, "Order not found")
 
    # ❌ Payment must be successful
    if order.payment_status != "SUCCESS":
        raise HTTPException(400, "Payment not completed")
 
    # ❌ Cancelled orders cannot be placed
    if order.status == OrderStatus.CANCELLED:
        raise HTTPException(400, "Order is cancelled")
 
    # ✅ ALREADY PLACED → JUST RETURN STATUS (KEY FIX 🔥)
    if order.status != OrderStatus.PAID:
        return {
            "message": "Order already placed",
            "order_id": order.id,
            "order_status": order.status
        }
 
    # ✅ FIRST-TIME PLACE
    order.status = OrderStatus.WAITING_PHARMACIST
    await db.commit()
 
    return {
        "message": "Order placed successfully. Waiting for pharmacist approval.",
        "order_id": order.id,
        "order_status": order.status
    }