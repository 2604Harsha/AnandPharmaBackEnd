
from core.database import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime, timedelta

class EmailOTP(Base):
    __tablename__ = "email_otps"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    otp = Column(String)
    expires_at = Column(DateTime)

    @staticmethod
    def expiry_time():
        return datetime.utcnow() + timedelta(minutes=10)
