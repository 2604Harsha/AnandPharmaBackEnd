from fastapi import Depends, Request, HTTPException
from jose import jwt, JWTError
from core.config import settings

def get_current_user(request: Request):
    token = request.cookies.get("access_token")

    # Swagger / Postman support
    if not token:
        auth = request.headers.get("Authorization")
        if auth and auth.startswith("Bearer "):
            token = auth.split(" ")[1]

    if not token:
        raise HTTPException(status_code=401, detail="Login required")

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def require_role(allowed_roles: list):
    def role_checker(payload=Depends(get_current_user)):
        if payload.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="Permission denied"
            )
        return payload
    return role_checker
