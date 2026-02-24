from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from core.database import get_db
from core.rbac import require_role

from schemas.campagin import (
    CampaignCreate,
    CampaignUpdate,
    CampaignOut,
)

from services.campaign_service import (
    create_campaign,
    get_campaign,
    get_campaigns,
    update_campaign,
    delete_campaign,
)

router = APIRouter(
    prefix="/admin/campaigns",
    tags=["Marketing Campaigns"],
)


@router.post("/", response_model=CampaignOut)
async def create_campaign_api(
    data: CampaignCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("admin")),
):
    return await create_campaign(db, data, background_tasks)


@router.get("/", response_model=List[CampaignOut])
async def list_campaigns(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("admin")),
):
    return await get_campaigns(db)


@router.get("/{campaign_id}", response_model=CampaignOut)
async def get_campaign_api(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("admin")),
):
    return await get_campaign(db, campaign_id)


@router.put("/{campaign_id}", response_model=CampaignOut)
async def update_campaign_api(
    campaign_id: int,
    data: CampaignUpdate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("admin")),
):
    return await update_campaign(db, campaign_id, data)


@router.delete("/{campaign_id}")
async def delete_campaign_api(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("admin")),
):
    return await delete_campaign(db, campaign_id)