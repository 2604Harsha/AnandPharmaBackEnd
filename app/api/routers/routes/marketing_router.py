from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.rbac import require_role

from schemas.marketing_overview import CountOut, ConversionRateOut
from services.marketing_service import (
    get_active_campaigns_count,
    get_push_sent_today,
    get_active_coupons_count,
    get_conversion_rate,
)

router = APIRouter(
    prefix="/admin/marketing",
    tags=["Marketing Dashboard"],
)


# =====================================================
# ACTIVE CAMPAIGNS
# =====================================================

@router.get("/active-campaigns", response_model=CountOut)
async def active_campaigns_api(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("admin")),
):
    count = await get_active_campaigns_count(db)
    return {"count": count}


# =====================================================
# PUSH SENT TODAY
# =====================================================

@router.get("/push-sent-today", response_model=CountOut)
async def push_sent_today_api(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("admin")),
):
    count = await get_push_sent_today(db)
    return {"count": count}


# =====================================================
# ACTIVE COUPONS
# =====================================================

@router.get("/active-coupons", response_model=CountOut)
async def active_coupons_api(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("admin")),
):
    count = await get_active_coupons_count(db)
    return {"count": count}


# =====================================================
# CONVERSION RATE
# =====================================================

@router.get("/conversion-rate", response_model=ConversionRateOut)
async def conversion_rate_api(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("admin")),
):
    rate = await get_conversion_rate(db)
    return {"conversion_rate": rate}