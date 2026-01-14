from datetime import datetime, timedelta
from fastapi import Request
from jose import jwt
from models.user import User
from core.database import AsyncSession
from core.config import settings

def create_access_token(data: dict):
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

