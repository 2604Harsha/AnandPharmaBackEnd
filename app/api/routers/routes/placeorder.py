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
 
    # ✅ FIX: check payment_status, not order.status
    if order.payment_status != "SUCCESS":
        raise HTTPException(400, "Payment not completed")
 
    # Optional safety check
    if order.status not in [
        OrderStatus.WAITING_PHARMACIST,
        OrderStatus.PAID
    ]:
        raise HTTPException(400, "Order cannot be placed in current state")
 
    order.status = OrderStatus.ACCEPTED
    await db.commit()
 
    return {
        "message": "Order confirmed",
        "order_id": order.id,
        "order_status": order.status
    }