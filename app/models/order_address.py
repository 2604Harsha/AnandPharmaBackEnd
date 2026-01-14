from sqlalchemy import Column, Float, Integer, String, ForeignKey
from core.database import Base

class OrderAddress(Base):
    __tablename__ = "order_addresses"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))

    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    phone = Column(String)

    address = Column(String)
    city = Column(String)
    state = Column(String)
    pincode = Column(String)
    landmark = Column(String, nullable=True)

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
