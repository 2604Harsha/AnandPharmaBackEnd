from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import BackgroundTasks, HTTPException

from services.notification_service import send_campaign_notification
from models.campaign import Campaign
from schemas.campagin import CampaignCreate, CampaignUpdate


# ================= CREATE =================

async def create_campaign(
    db: AsyncSession,
    data: CampaignCreate,
    background_tasks: BackgroundTasks,
):
    campaign = Campaign(**data.model_dump())
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)

    # 🔔 trigger notifications in background
    background_tasks.add_task(
        send_campaign_notification,
        campaign.title,
        campaign.description,
    )

    return campaign


# ================= GET ONE =================

async def get_campaign(db: AsyncSession, campaign_id: int):
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return campaign


# ================= LIST =================

async def get_campaigns(db: AsyncSession):
    result = await db.execute(select(Campaign))
    return result.scalars().all()


# ================= UPDATE (PUT FULL) =================

async def update_campaign(
    db: AsyncSession,
    campaign_id: int,
    data: CampaignUpdate,
):
    campaign = await get_campaign(db, campaign_id)

    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(campaign, key, value)

    await db.commit()
    await db.refresh(campaign)
    return campaign


# ================= DELETE (HARD) =================

async def delete_campaign(db: AsyncSession, campaign_id: int):
    campaign = await get_campaign(db, campaign_id)

    await db.delete(campaign)
    await db.commit()

    return {"message": "Campaign deleted successfully"}