from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey
from datetime import datetime
from core.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)

    # 🔹 Your internal order id
    internal_order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)

    # 🔹 Razorpay identifiers
    razorpay_order_id = Column(String(100), nullable=False, unique=True)
    razorpay_payment_id = Column(String(100), nullable=True)
    razorpay_signature = Column(String(255), nullable=True)

    # 🔹 Amount in INR (safe precision)
    amount = Column(Numeric(10, 2), nullable=False)

    # 🔹 Card / UPI / Netbanking
    payment_method = Column(String(50), nullable=True)

    # 🔹 CREATED | SUCCESS | FAILED | REFUNDED
    status = Column(String(20), default="CREATED", index=True)

    # 🔹 Failure reason if any
    failure_reason = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)