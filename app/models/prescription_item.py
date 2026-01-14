from sqlalchemy import Column, Integer, String, ForeignKey
from core.database import Base

class PrescriptionItem(Base):
    __tablename__ = "prescription_items"

    id = Column(Integer, primary_key=True)
    prescription_id = Column(Integer, ForeignKey("prescriptions.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    medicine_name = Column(String)
