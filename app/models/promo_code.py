# models/promo_code.py

from sqlalchemy import Column, Integer, String, DateTime
from core.database import Base
from datetime import datetime, timezone


class PromoCode(Base):
    __tablename__ = "promo_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False)
    discount_type = Column(String, nullable=False)  # percentage / flat
    discount_value = Column(Integer, nullable=False)
    used_count = Column(Integer, default=0)
    max_usage = Column(Integer, nullable=False)

    # ✅ IMPORTANT FIXES
    expires_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, default="active")  # active / paused

    # ✅ UTC aware timestamp
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )