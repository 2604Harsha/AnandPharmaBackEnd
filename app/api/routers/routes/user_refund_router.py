from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.rbac import require_role
from models.refund_request import UserRefundReason
from services.user_refund_service import (
    create_user_refund_request_service,
    get_user_refund_requests_by_order_service,
    get_user_refund_request_detail_service
)

router = APIRouter(prefix="/user-refunds", tags=["User Refund Requests"])


# ✅ Create refund request (image upload + reason + comment)
@router.post("/")
async def create_user_refund_request(
    order_id: int = Form(...),
    reason: UserRefundReason = Form(...),
    comment: str = Form(None),
    photo: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("user"))
):
    req = await create_user_refund_request_service(
        db=db,
        order_id=order_id,
        reason=reason,
        comment=comment,
        photo=photo,
        current_user=current_user
    )

    return {
        "message": "Refund request submitted successfully",
        "request_id": req.id,
        "order_id": req.order_id,
        "status": req.status,
        "reason": req.reason,
        "comment": req.comment,
        "photo_url": req.photo_url
    }


# ✅ List refund requests by order (only current user)
@router.get("/order/{order_id}")
async def get_user_refund_requests_by_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("user"))
):
    requests = await get_user_refund_requests_by_order_service(
        db=db,
        order_id=order_id,
        current_user=current_user
    )

    if not requests:
        return {"message": "No refund requests found", "order_id": order_id}

    return [
        {
            "request_id": r.id,
            "order_id": r.order_id,
            "user_id": r.user_id,
            "status": r.status,
            "reason": r.reason,
            "comment": r.comment,
            "photo_url": r.photo_url,
            "rejection_reason": r.rejection_reason,
            "created_at": r.created_at
        }
        for r in requests
    ]


# ✅ Refund request details (only current user)
@router.get("/{request_id}")
async def get_user_refund_request_detail(
    request_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("user"))
):
    r = await get_user_refund_request_detail_service(
        db=db,
        request_id=request_id,
        current_user=current_user
    )

    if not r:
        raise HTTPException(status_code=404, detail="Refund request not found")

    return {
        "request_id": r.id,
        "order_id": r.order_id,
        "user_id": r.user_id,
        "status": r.status,
        "reason": r.reason,
        "comment": r.comment,
        "photo_url": r.photo_url,
        "rejection_reason": r.rejection_reason,
        "created_at": r.created_at
    }
