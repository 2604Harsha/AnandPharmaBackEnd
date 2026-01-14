from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from core.rbac import require_role

from models.order import Order
from models.order_item import OrderItem

router = APIRouter(prefix="/billing", tags=["Billing"])
@router.get("/{order_id}")
async def get_billing_page(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role("user"))
):
    order = await db.get(Order, order_id)

    if not order:
        raise HTTPException(404, "Order not found")

    items = await db.execute(
        select(OrderItem).where(OrderItem.order_id == order_id)
    )

    return {
        "order_id": order.id,
        "subtotal": order.subtotal,
        "tax": order.tax,
        "total": order.total,
        "payment_methods": [
            "CARD",
            "UPI"
        ],
        "items": [
            {
                "name": i.product_name,
                "qty": i.quantity,
                "price": i.price
            }
            for i in items.scalars()
        ]
    }
