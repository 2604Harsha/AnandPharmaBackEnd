import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from core.database import async_session_maker
from models.refund import Refund, RefundStatus
from schemas.refund import RefundCreate
from services.email_service import send_html_email
from models.order import Order
from models.order_address import OrderAddress   # ✅ import


async def create_refund(db: AsyncSession, payload: RefundCreate):
    # ✅ fetch order + user
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.user))
        .where(Order.id == payload.order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise Exception("Order not found")

    if not order.user:
        raise Exception("User not found")

    # ✅ fetch address from OrderAddress table directly
    address_result = await db.execute(
        select(OrderAddress).where(OrderAddress.order_id == order.id)
    )
    order_address = address_result.scalar_one_or_none()

    if not order_address:
        raise Exception("Order address not found")

    # ✅ email from user
    customer_email = order.user.email
    if not customer_email:
        raise Exception("User email not found")

    # ✅ name from user full_name
    customer_name = order.user.full_name or "Customer"

    # ✅ amount from order table
    refund_amount = float(order.total)

    # ✅ create refund
    refund = Refund(
        order_id=order.id,
        payment_id=payload.payment_id,
        amount=refund_amount,
        reason=payload.reason,
        status=RefundStatus.processing
    )

    db.add(refund)
    await db.commit()
    await db.refresh(refund)

    # ✅ send processing mail
    subject = "⏳ Refund Processing - Anand Pharma"
    message = f"""
Hi {customer_name},

Refund Initiated ✅
Your refund request has been successfully initiated.

🧾 Order ID: {order.id}
💳 Payment ID: {refund.payment_id}
💰 Refund Amount: ₹{refund.amount}

⏳ The amount will be credited back to your original payment method within 20–24 hours
(bank processing time may vary).

Thanks for choosing Anand Pharma 💊
"""
    send_html_email(customer_email, subject, message)

    # ✅ background update
    asyncio.create_task(refund_success_after_delay(refund.id))

    return refund


async def refund_success_after_delay(refund_id: int):
    await asyncio.sleep(86400)  # 24 hours

    async with async_session_maker() as db:
        # ✅ fetch refund
        result = await db.execute(select(Refund).where(Refund.id == refund_id))
        refund = result.scalar_one_or_none()
        if not refund:
            return

        # ✅ mark success
        refund.status = RefundStatus.success
        refund.gateway_refund_id = f"rfnd_{refund.id}"
        await db.commit()
        await db.refresh(refund)

        # ✅ fetch order + user
        result = await db.execute(
            select(Order)
            .options(selectinload(Order.user))
            .where(Order.id == refund.order_id)
        )
        order = result.scalar_one_or_none()
        if not order or not order.user:
            return

        customer_email = order.user.email
        customer_name = order.user.full_name or "Customer"

        # ✅ credited mail
        subject = "✅ Refund Credited - Anand Pharma"
        message = f"""
Hi {customer_name},

✅ Your refund has been successfully credited.

🧾 Order ID: {refund.order_id}
💳 Payment ID: {refund.payment_id}
💰 Refund Amount: ₹{refund.amount}
🆔 Refund Ref: {refund.gateway_refund_id}

Thank you,
Anand Pharma
"""
        send_html_email(customer_email, subject, message)
