from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError

from core.database import get_db
from models.user import User
from core.config import settings

security = HTTPBearer(auto_error=False)  # Don't auto-error

def require_role(*roles: str):

    async def role_checker(
        request: Request,  # Add request to check cookies
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: AsyncSession = Depends(get_db)
    ):
        token = None
        
        # Try to get token from Authorization header first
        if credentials:
            token = credentials.credentials
            print(f"Token from header: {token}")
        
        # If no header token, try cookies
        if not token:
            token = request.cookies.get("access_token")
            print(f"Token from cookie: {token}")
        
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            print(f"Payload from token: {payload}")
            
            user_id = payload.get("sub")
            user_role = payload.get("role")
            
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            # Check role
            allowed_roles = [r.strip().lower() for r in roles]
            if (user_role or "").strip().lower() not in allowed_roles:
                raise HTTPException(
                    status_code=403,
                    detail=f"Access denied. Your role: {user_role}"
                )
            
            # Get user from database
            user = await db.get(User, int(user_id))
            if not user:
                raise HTTPException(status_code=401, detail="User not found")
            
            return user
            
        except JWTError as e:
            print(f"JWT Error: {e}")
            raise HTTPException(status_code=401, detail="Invalid token")
    
    return role_checker