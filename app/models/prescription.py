from sqlalchemy import Column, Integer, String, Enum, DateTime
from core.database import Base
from datetime import datetime
import enum
 
class PrescriptionStatus(str, enum.Enum):
    approved = "approved"
    pharmacist_review = "pharmacist_review"
    rejected = "rejected"
 
class Prescription(Base):
    __tablename__ = "prescriptions"
 
    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String, nullable=False)
    extracted_text = Column(String)
    status = Column(Enum(PrescriptionStatus), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
 
 