from sqlalchemy import Column, DateTime, Float, Integer, String, Boolean
from sqlalchemy.orm import relationship
from models.order import Order
from core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, unique=True)
    password = Column(String, nullable=False)
    role = Column(String, default="user")  # admin / pharmacist / user

    pharmacy_name = Column(String, nullable=True)
    license_no = Column(String, nullable=True)
    shop_no = Column(String, nullable=True)

    vehicle_number = Column(String, nullable=True)
    vehicle_type = Column(String, nullable=True)
    driving_license_no = Column(String, nullable=True)
    rc_no = Column(String, nullable=True)

    # ✅ NEW — User Address
    address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    pincode = Column(String, nullable=True)

    is_active = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)

    # 📍 Stable pharmacist store location
    store_name = Column(String, nullable=True)
    store_shop_no = Column(String, nullable=True)
    store_street = Column(String, nullable=True)
    store_city = Column(String, nullable=True)
    store_landmark = Column(String, nullable=True)
    store_state = Column(String, nullable=True)
    store_pincode = Column(String, nullable=True)
    store_address = Column(String, nullable=True)

    da_street = Column(String, nullable=True)
    da_city = Column(String, nullable=True)
    da_state = Column(String, nullable=True)
    da_pincode = Column(String, nullable=True)
    da_address = Column(String, nullable=True)

    # Reuse existing fields
    last_latitude = Column(Float, nullable=True)
    last_longitude = Column(Float, nullable=True)
    last_location_at = Column(DateTime(timezone=True), nullable=True)
    is_online = Column(Boolean, default=False)
    
    # 👤 Orders placed by customer
    customer_orders = relationship(
       "Order",
       foreign_keys=[Order.user_id],
       back_populates="user"
    )

    # 🏥 Orders received by pharmacy
    pharmacy_orders = relationship(
      "Order",
      foreign_keys=[Order.pharmacy_id],
      back_populates="pharmacy"
    )