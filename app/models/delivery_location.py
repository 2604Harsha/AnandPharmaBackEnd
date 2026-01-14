from sqlalchemy import Column, Integer, Float, ForeignKey
from core.database import Base

class DeliveryLocation(Base):
    __tablename__ = "delivery_locations"

    id = Column(Integer, primary_key=True)
    delivery_id = Column(Integer, ForeignKey("deliveries.id"))
    latitude = Column(Float)
    longitude = Column(Float)
