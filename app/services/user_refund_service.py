import os
import uuid
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models.refund_request import RefundRequest, RefundRequestStatus, UserRefundReason
from models.pharmacist_notification import PharmacistNotification
from models.order import Order
from models.user import User


UPLOAD_DIR = "uploads/refund_proofs"
os.makedirs(UPLOAD_DIR, exist_ok=True)


async def create_user_refund_request_service(
    db: AsyncSession,
    order_id: int,
    reason: UserRefundReason,
    comment: str | None,
    photo: UploadFile,
    current_user
):
    # ✅ Order check
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # ✅ Make sure order belongs to logged-in user
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to create refund request for this order"
        )

    # ✅ Refund allowed ONLY after delivery (FIXED ERROR HERE ✅)
    # This avoids Enum AttributeError completely
    if order.status!= "DELIVERED":
        raise HTTPException(
            status_code=400,
            detail="Refund request can be created only after order delivery"
        )

    # ✅ User check
    result = await db.execute(select(User).where(User.id == order.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # ✅ Prevent multiple pending requests for same order
    pending_result = await db.execute(
        select(RefundRequest).where(
            RefundRequest.order_id == order_id,
            RefundRequest.status == RefundRequestStatus.pending
        )
    )
    existing_pending = pending_result.scalar_one_or_none()

    if existing_pending:
        raise HTTPException(
            status_code=400,
            detail="A refund request is already pending for this order"
        )

    # ✅ Validate file extension
    if not photo.filename or "." not in photo.filename:
        raise HTTPException(status_code=400, detail="Invalid file uploaded")

    ext = photo.filename.split(".")[-1].lower()
    allowed = ["jpg", "jpeg", "png", "webp"]
    if ext not in allowed:
        raise HTTPException(status_code=400, detail="Only jpg/jpeg/png/webp allowed")

    # ✅ Save photo
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    content = await photo.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    with open(filepath, "wb") as f:
        f.write(content)

    photo_url = f"/uploads/refund_proofs/{filename}"

    # ✅ Create refund request
    req = RefundRequest(
        order_id=order.id,
        user_id=user.id,
        reason=reason,
        comment=comment,
        photo_url=photo_url,
        status=RefundRequestStatus.pending
    )

    db.add(req)
    await db.commit()
    await db.refresh(req)

    # ✅ Create pharmacist notification
    notif = PharmacistNotification(
        refund_request_id=req.id,
        title="New Refund Request",
        message=f"Refund request submitted for Order ID {order.id} by {user.full_name} ({user.email})"
    )

    db.add(notif)
    await db.commit()

    return req


# ✅ User can view only his refund requests
async def get_user_refund_requests_by_order_service(
    db: AsyncSession,
    order_id: int,
    current_user
):
    result = await db.execute(
        select(RefundRequest).where(
            RefundRequest.order_id == order_id,
            RefundRequest.user_id == current_user.id
        )
    )
    return result.scalars().all()


# ✅ User can view only his refund request detail
async def get_user_refund_request_detail_service(
    db: AsyncSession,
    request_id: int,
    current_user
):
    result = await db.execute(
        select(RefundRequest).where(
            RefundRequest.id == request_id,
            RefundRequest.user_id == current_user.id
        )
    )
    return result.scalar_one_or_none()
