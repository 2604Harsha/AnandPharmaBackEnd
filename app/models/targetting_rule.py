# models/targeting_rule.py

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from core.database import Base
from datetime import datetime, timezone


class AudienceTargetingRule(Base):
    __tablename__ = "audience_targeting_rules"

    id = Column(Integer, primary_key=True, index=True)

    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)

    field = Column(String, nullable=False)      # city / orders / etc
    operator = Column(String, nullable=False)   # equals / greater_than
    value = Column(String, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # optional relationship
    campaign = relationship("Campaign", back_populates="targeting_rules")