
import enum
from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    String,
    Boolean,
    DateTime,
    Enum
)
from sqlalchemy.sql import func
from core.database import Base


# ===============================
# 🚚 DELIVERY STATUS ENUM
# ===============================
class DeliveryStatus(str, enum.Enum):
    ASSIGNED = "ASSIGNED"
    PICKED_UP = "PICKED_UP"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


# ===============================
# ❌ DELIVERY CANCEL REASONS
# ===============================
class DeliveryCancelReason(str, enum.Enum):
    # 🔁 Reassign allowed
    VEHICLE_BREAKDOWN = "VEHICLE_BREAKDOWN"
    HEALTH_ISSUE = "HEALTH_ISSUE"
    EMERGENCY = "EMERGENCY"
    STORE_DELAY = "STORE_DELAY"

    # ❌ No reassignment
    CUSTOMER_UNREACHABLE = "CUSTOMER_UNREACHABLE"
    CUSTOMER_CANCELLED = "CUSTOMER_CANCELLED"
    WRONG_ADDRESS = "WRONG_ADDRESS"


class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True)

    order_id = Column(
        Integer,
        ForeignKey("orders.id"),
        nullable=False
    )

    delivery_user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    # ✅ FIXED: status is ENUM
    status = Column(
        Enum(DeliveryStatus, name="deliverystatus"),
        nullable=False,
        default=DeliveryStatus.ASSIGNED
    )

    assigned_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    picked_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    delivered_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    eta_minutes = Column(
        Integer,
        nullable=True
    )

    # ===============================
    # 🔐 OTP
    # ===============================
    otp = Column(String, nullable=True)
    otp_verified = Column(Boolean, default=False)
    otp_expires_at = Column(DateTime(timezone=True), nullable=True)
    otp_attempts = Column(Integer, default=0)

    # ===============================
    # ❌ Cancellation
    # ===============================
    cancel_reason = Column(
        Enum(DeliveryCancelReason, name="deliverycancelreason"),
        nullable=True
    )

    cancelled_at = Column(
        DateTime(timezone=True),
        nullable=True
    )
