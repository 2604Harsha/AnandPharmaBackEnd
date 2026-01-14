from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey
from datetime import datetime
from core.database import Base

class PharmacistOrder(Base):
    __tablename__ = "pharmacist_orders"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    pharmacist_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String)  # SENT / ACCEPTED / REJECTED
    created_at = Column(DateTime, default=datetime.utcnow)
