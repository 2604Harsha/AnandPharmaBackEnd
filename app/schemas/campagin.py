from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import datetime

from models.campaign import (
    CampaignType,
    DiscountType,
    AudienceType,
    LaunchType,
)


# ================= CREATE =================

class CampaignCreate(BaseModel):
    title: str
    description: Optional[str] = None

    campaign_type: CampaignType
    discount_type: Optional[DiscountType] = None
    discount_value: Optional[float] = None

    audience_type: AudienceType
    target_cities: Optional[List[str]] = None

    launch_type: LaunchType
    scheduled_at: Optional[datetime] = None

    campaign_budget: Optional[float] = None
    max_redemptions: Optional[int] = None

    banner_url: Optional[str] = None

    # ✅ smart validations
    @field_validator("discount_value")
    @classmethod
    def validate_discount(cls, v):
        if v is not None and v < 0:
            raise ValueError("Discount must be positive")
        return v


class CampaignUpdate(CampaignCreate):
    pass


# ================= RESPONSE =================

class CampaignOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    campaign_type: CampaignType
    discount_type: Optional[DiscountType]
    discount_value: Optional[float]
    audience_type: AudienceType
    target_cities: Optional[List[str]]
    launch_type: LaunchType
    scheduled_at: Optional[datetime]
    campaign_budget: Optional[float]
    max_redemptions: Optional[int]
    banner_url: Optional[str]

    class Config:
        from_attributes = True