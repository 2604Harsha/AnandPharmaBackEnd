from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from core.database import Base
from datetime import datetime, timedelta
import secrets

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    token = Column(String(255), unique=True, index=True)
    expires_at = Column(DateTime)

    @staticmethod
    def generate_token():
        return secrets.token_urlsafe(32)

    @staticmethod
    def expiry_time(minutes=15):
        return datetime.utcnow() + timedelta(minutes=minutes)
