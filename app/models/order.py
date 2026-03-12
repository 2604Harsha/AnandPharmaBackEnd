from datetime import datetime

from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, String, Enum
import enum
from sqlalchemy.orm import relationship
from core.database import Base
from sqlalchemy.sql import func


class OrderStatus(str, enum.Enum):

    PENDING = "PENDING"
    PAYMENT_INITIATED = "PAYMENT_INITIATED"
    PAID = "PAID"

    WAITING_PHARMACIST = "WAITING_PHARMACIST"
    ACCEPTED = "ACCEPTED"
    PACKED = "PACKED"
    READY_FOR_DELIVERY = "READY_FOR_DELIVERY"

    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"

    CANCELLED = "CANCELLED"
    CONFIRMED = "CONFIRMED"
    DISPUTED = "DISPUTED"
    REFUNDED = "REFUNDED"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    order_number = Column(String(20), unique=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pharmacy_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    delivery_agent_id = Column(Integer, ForeignKey("users.id"), nullable=True)

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
    updated_at = Column(
    DateTime,
    default=datetime.utcnow,
    onupdate=datetime.utcnow
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 📦 Order Items
    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan"
    )

    # 👤 Customer
    user = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="customer_orders"
    )

    # 🏥 Pharmacy
    pharmacy = relationship(
        "User",
        foreign_keys=[pharmacy_id],
        back_populates="pharmacy_orders"
    )

    # 🚴 Delivery Agent
    delivery_agent = relationship(
        "User",
        foreign_keys=[delivery_agent_id]
    )

    # 📍 Shipping Address
    address = relationship(
        "ShippingAddress",
        back_populates="order",
        uselist=False,
        cascade="all, delete-orphan"
    )