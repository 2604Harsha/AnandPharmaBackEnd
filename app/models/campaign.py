import enum
from datetime import datetime
from sqlalchemy.orm import relationship

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Enum, JSON
from core.database import Base


# ================= ENUMS =================

class CampaignType(str, enum.Enum):
    discount_offer = "discount_offer"
    free_delivery = "free_delivery"
    cashback = "cashback"
    buy_one_get_one = "buy_one_get_one"


class DiscountType(str, enum.Enum):
    percentage = "percentage"
    flat = "flat"


class AudienceType(str, enum.Enum):
    all_users = "all_users"
    new_users = "new_users"
    returning_customers = "returning_customers"
    prescription_users = "prescription_users"


class LaunchType(str, enum.Enum):
    immediate = "immediate"
    scheduled = "scheduled"


# ================= MODEL =================

class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)

    # Campaign Details
    title = Column(String(255), nullable=False)
    description = Column(Text)

    campaign_type = Column(Enum(CampaignType), nullable=False)
    discount_type = Column(Enum(DiscountType), nullable=True)
    discount_value = Column(Float, nullable=True)

    # Audience
    audience_type = Column(Enum(AudienceType), nullable=False)
    target_cities = Column(JSON, nullable=True)

    # Schedule
    launch_type = Column(Enum(LaunchType), nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)

    # Budget
    campaign_budget = Column(Float, nullable=True)
    max_redemptions = Column(Integer, nullable=True)

    # Banner
    banner_url = Column(String, nullable=True)

    # Meta
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    targeting_rules = relationship(
    "AudienceTargetingRule",
    back_populates="campaign",
    cascade="all, delete-orphan"
)