from fastapi import Request
from fastapi.responses import JSONResponse
from jose import jwt, JWTError
from core.config import settings

PUBLIC_PATHS = ["/docs","/chatbot", "/openapi.json","/auth/register", "/auth/login","/auth/verify-otp", "/auth/resend-otp","/auth/forgot-password","/auth/reset-password","/prescription/upload"]

async def auth_middleware(request: Request, call_next):
    if any(request.url.path.startswith(p) for p in PUBLIC_PATHS):
        return await call_next(request)

    token = request.cookies.get("access_token")

    if not token:
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        request.state.user = payload
    except JWTError:
        return JSONResponse(status_code=401, content={"detail": "Invalid token"})

    return await call_next(request)
