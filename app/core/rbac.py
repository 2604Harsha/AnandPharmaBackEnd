from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError

from core.database import get_db
from models.user import User
from core.config import settings

security = HTTPBearer()

def require_role(*roles: str):   # ✅ multiple roles
    async def role_checker(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: AsyncSession = Depends(get_db)
    ):
        token = credentials.credentials

        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )

            user_id = payload.get("sub")
            user_role = payload.get("role")

            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token")

            # ✅ case-insensitive role match
            allowed_roles = [r.strip().lower() for r in roles]
            if (user_role or "").strip().lower() not in allowed_roles:
                raise HTTPException(
                    status_code=403,
                    detail=f"Access denied. Your role: {user_role}"
                )

        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.get(User, int(user_id))
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return user

    return role_checker
