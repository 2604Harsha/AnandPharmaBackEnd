from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.database import get_db
from core.rbac import require_role
from models.refund_request import RefundRequest, RefundRequestStatus
from models.user import User
from services.email_service import send_html_email


router = APIRouter(prefix="/pharmacist-refunds", tags=["Pharmacist Refund Action"])


# ======================================================
# ✅ EMAIL TEMPLATE: Refund Approved
# ======================================================
def refund_approved_template(name: str, order_id: int) -> str:
    return f"""
    <html>
    <body style="margin:0;background:#f4f6f8;font-family:Arial,Helvetica,sans-serif">
        <div style="max-width:600px;margin:auto;background:#ffffff;border-radius:8px;overflow:hidden">

            <div style="background:#0b5c6b;color:white;padding:20px;text-align:center">
                <h2 style="margin:0">ANAND PHARMA</h2>
                <p style="margin:5px 0 0;font-size:13px">Trusted Healthcare</p>
            </div>

            <div style="padding:30px;color:#333">
                <p>Hello <b>{name}</b>,</p>

                <p style="font-size:15px">
                    Your refund request for <b>Order ID #{order_id}</b> has been
                    <span style="color:green;font-weight:bold">APPROVED ✅</span>.
                </p>

                <div style="background:#f1f5f9;padding:15px;border-radius:6px;margin:20px 0">
                    <p style="margin:0;font-size:14px">
                        We are now processing your refund.<br>
                        You will receive the amount soon.
                    </p>
                </div>

                <p style="font-size:14px;color:#555">
                    If you need help, please contact our support team.
                </p>

                <br>

                <p style="font-size:14px">
                    Warm regards,<br>
                    <b>Anand Pharma Team</b>
                </p>
            </div>

            <div style="text-align:center;padding:12px;color:#999;font-size:12px;background:#fafafa">
                © 2026 Anand Pharma. All Rights Reserved.
            </div>

        </div>
    </body>
    </html>
    """


# ======================================================
# ✅ EMAIL TEMPLATE: Refund Rejected
# ======================================================
def refund_rejected_template(name: str, order_id: int, reason: str) -> str:
    return f"""
    <html>
    <body style="margin:0;background:#f4f6f8;font-family:Arial,Helvetica,sans-serif">
        <div style="max-width:600px;margin:auto;background:#ffffff;border-radius:8px;overflow:hidden">

            <div style="background:#0b5c6b;color:white;padding:20px;text-align:center">
                <h2 style="margin:0">ANAND PHARMA</h2>
                <p style="margin:5px 0 0;font-size:13px">Trusted Healthcare</p>
            </div>

            <div style="padding:30px;color:#333">
                <p>Hello <b>{name}</b>,</p>

                <p style="font-size:15px">
                    Your refund request for <b>Order ID #{order_id}</b> has been
                    <span style="color:red;font-weight:bold">REJECTED ❌</span>.
                </p>

                <div style="background:#fff3f3;padding:15px;border-radius:6px;margin:20px 0;border:1px solid #ffd1d1">
                    <p style="margin:0;font-size:14px">
                        <b>Reason:</b><br>
                        {reason}
                    </p>
                </div>

                <p style="font-size:14px;color:#555">
                    If you feel this is incorrect, please contact our support team.
                </p>

                <br>

                <p style="font-size:14px">
                    Warm regards,<br>
                    <b>Anand Pharma Team</b>
                </p>
            </div>

            <div style="text-align:center;padding:12px;color:#999;font-size:12px;background:#fafafa">
                © 2026 Anand Pharma. All Rights Reserved.
            </div>

        </div>
    </body>
    </html>
    """


# ======================================================
# ✅ APPROVE REFUND REQUEST
# ======================================================
@router.put("/{request_id}/approve")
async def approve_refund_request(
    request_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("pharmacist")),
):
    result = await db.execute(select(RefundRequest).where(RefundRequest.id == request_id))
    req = result.scalar_one_or_none()

    if not req:
        raise HTTPException(status_code=404, detail="Refund request not found")

    if req.status != RefundRequestStatus.pending:
        raise HTTPException(status_code=400, detail="Refund request already processed")

    req.status = RefundRequestStatus.approved
    req.rejection_reason = None

    await db.commit()
    await db.refresh(req)

    # ✅ Get user
    user_result = await db.execute(select(User).where(User.id == req.user_id))
    user = user_result.scalar_one_or_none()

    # ✅ Send email (Background)
    if user:
        subject = "✅ Refund Request Approved - Processing"
        html = refund_approved_template(user.full_name, req.order_id)

        background_tasks.add_task(
            send_html_email,
            to_email=user.email,
            subject=subject,
            html_body=html,
        )

    return {
        "message": "Refund request approved successfully",
        "status": req.status,
        "request_id": req.id,
        "order_id": req.order_id,
    }


# ======================================================
# ❌ REJECT REFUND REQUEST
# ======================================================
@router.put("/{request_id}/reject")
async def reject_refund_request(
    request_id: int,
    rejection_reason: str = Query(...),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("pharmacist")),
):
    result = await db.execute(select(RefundRequest).where(RefundRequest.id == request_id))
    req = result.scalar_one_or_none()

    if not req:
        raise HTTPException(status_code=404, detail="Refund request not found")

    if req.status != RefundRequestStatus.pending:
        raise HTTPException(status_code=400, detail="Refund request already processed")

    if not rejection_reason.strip():
        raise HTTPException(status_code=400, detail="Rejection reason is required")

    req.status = RefundRequestStatus.rejected
    req.rejection_reason = rejection_reason

    await db.commit()
    await db.refresh(req)

    # ✅ Get user
    user_result = await db.execute(select(User).where(User.id == req.user_id))
    user = user_result.scalar_one_or_none()

    # ✅ Send email (Background)
    if user:
        subject = "❌ Refund Request Rejected"
        html = refund_rejected_template(user.full_name, req.order_id, rejection_reason)

        if background_tasks:
            background_tasks.add_task(
                send_html_email,
                to_email=user.email,
                subject=subject,
                html_body=html,
            )
        else:
            # fallback
            send_html_email(to_email=user.email, subject=subject, html_body=html)

    return {
        "message": "Refund request rejected successfully",
        "status": req.status,
        "request_id": req.id,
        "order_id": req.order_id,
        "rejection_reason": rejection_reason,
    }
