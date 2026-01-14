from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base

class ShippingAddress(Base):
    __tablename__ = "shipping_addresses"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)

    first_name = Column(String(100))
    last_name = Column(String(100))
    email = Column(String(150))
    phone = Column(String(20))

    address = Column(String(255))
    landmark = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    pincode = Column(String(10))
    
    order = relationship(
        "Order",
        back_populates="address"
    )