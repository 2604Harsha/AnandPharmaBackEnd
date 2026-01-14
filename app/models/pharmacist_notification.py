from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from core.database import Base


class PharmacistNotification(Base):
    __tablename__ = "pharmacist_notifications"

    id = Column(Integer, primary_key=True)

    refund_request_id = Column(Integer, ForeignKey("refund_requests.id"), nullable=False)

    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)

    is_seen = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
