from sqlalchemy import Column, Integer, String, Enum, ForeignKey, DateTime, Text
from sqlalchemy.sql import func
from core.database import Base
import enum


class RefundRequestStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class UserRefundReason(str, enum.Enum):
    damaged = "damaged"
    expired = "expired"
    wrong_item = "wrong_item"
    missing_item = "missing_item"
    leakage = "leakage"


class RefundRequest(Base):
    __tablename__ = "refund_requests"

    id = Column(Integer, primary_key=True)

    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    reason = Column(Enum(UserRefundReason), nullable=False)
    comment = Column(Text, nullable=True)

    photo_url = Column(String(255), nullable=False)

    status = Column(Enum(RefundRequestStatus), default=RefundRequestStatus.pending)

    rejection_reason = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
