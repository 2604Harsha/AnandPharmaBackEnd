 
from sqlalchemy import Column, DateTime, Float, Integer, String, Boolean
from core.database import Base
from sqlalchemy.orm import relationship
 
 
class User(Base):
    __tablename__ = "users"
 
    id = Column(Integer, primary_key=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, unique=True)
    password = Column(String, nullable=False)
 
    role = Column(String, default="user")   # admin / pharmacist / user
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
 
    orders = relationship("Order", back_populates="user")
 
    # 📍 Stable pharmacist store location

    store_name = Column(String, nullable=True)
    store_shop_no = Column(String, nullable=True)
    store_street = Column(String, nullable=True)
    store_city = Column(String, nullable=True)
    store_landmark = Column(String, nullable=True)
    store_state = Column(String, nullable=True)
    store_pincode = Column(String, nullable=True)
    store_address = Column(String, nullable=True)
 
    # Reuse existing fields
    last_latitude = Column(Float, nullable=True)
    last_longitude = Column(Float, nullable=True)
    last_location_at = Column(DateTime(timezone=True), nullable=True)
    is_online = Column(Boolean, default=False)
 
 