from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, String, Enum
import enum
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base
from sqlalchemy.sql import func

class OrderStatus(str, enum.Enum):
    # 🛒 Checkout & Payment
    PENDING = "PENDING"                      # Address saved, payment not started
    PAYMENT_INITIATED = "PAYMENT_INITIATED"
    PAID = "PAID"

    # 🧑‍⚕️ Pharmacist Flow (NEW)
    WAITING_PHARMACIST = "WAITING_PHARMACIST"   # Notification sent
    ACCEPTED = "ACCEPTED"                       # Pharmacist accepted
    PACKED = "PACKED"                           # Medicines packed
    READY_FOR_DELIVERY = "READY_FOR_DELIVERY"   # Ready to assign delivery

    # 🚴 Delivery
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"

    # ❌ Other
    CANCELLED = "CANCELLED"

    # ⚠️ Backward compatibility (keep if already used)
    CONFIRMED = "CONFIRMED"




class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    order_number = Column(String(20), unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subtotal = Column(Float, default=0)
    cgst = Column(Float, default=0)
    sgst = Column(Float, default=0)
    handling_fee = Column(Float, default=10)
    delivery_fee = Column(Float, default=0)
    surge_fee = Column(Float, default=0)
    total = Column(Float, default=0)
    promo_code_id = Column(Integer, ForeignKey("promo_codes.id"), nullable=True)
    payment_id = Column(String(50), nullable=True, unique=True)
    payment_method = Column(String, nullable=True)
    payment_status = Column(String, default="PENDING")
    status = Column(
        Enum(OrderStatus),
        default=OrderStatus.PENDING,
        nullable=False
    )

    razorpay_order_id = Column(String, nullable=True)
    razorpay_payment_id = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan"
    )
    user = relationship("User", back_populates="orders")

    address = relationship(
        "ShippingAddress",
        back_populates="order",
        uselist=False,
        cascade="all, delete-orphan"
    )
