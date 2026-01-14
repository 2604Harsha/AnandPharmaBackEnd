from sqlalchemy import Column, Integer, String, Float, Enum, ForeignKey, DateTime
from sqlalchemy.sql import func
from core.database import Base
import enum
 
 
class RefundStatus(str, enum.Enum):
    initiated = "initiated"
    processing = "processing"
    success = "success"
    failed = "failed"
 
 
class RefundReason(str, enum.Enum):
    cancelled = "cancelled"
    out_of_stock = "out_of_stock"
    prescription_rejected = "prescription_rejected"
    damaged = "damaged"
    wrong_item = "wrong_item"
    payment_failure = "payment_failure"
 
 
class Refund(Base):
    __tablename__ = "refunds"
 
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    payment_id = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False)
 
    reason = Column(Enum(RefundReason), nullable=False)
    status = Column(Enum(RefundStatus), default=RefundStatus.initiated)
 
    gateway_refund_id = Column(String(100), nullable=True)
 
    created_at = Column(DateTime(timezone=True), server_default=func.now())