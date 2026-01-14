from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from schemas.refund import RefundCreate, RefundResponse
from services.refund_service import create_refund, refund_success_after_delay

router = APIRouter(prefix="/refunds", tags=["Refunds"])


@router.post("/", response_model=RefundResponse)
async def initiate_refund(
    payload: RefundCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    refund = await create_refund(db, payload)

    # ✅ schedule success after 24 hours
    background_tasks.add_task(refund_success_after_delay, refund.id)

    return RefundResponse(
        refund_id=refund.id,
        status=refund.status,
        amount=refund.amount
    )
