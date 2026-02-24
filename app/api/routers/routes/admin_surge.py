from fastapi import APIRouter, Depends
from core.redis import get_redis
from core.rbac import require_role
from services.surge_service import (
    admin_set_surge,
    admin_disable_surge,
    admin_get_surge,
)

router = APIRouter(prefix="/admin/surge", tags=["Admin Surge"])


@router.get("/")
async def get(redis=Depends(get_redis), admin=Depends(require_role("admin"))):
    return await admin_get_surge(redis)


@router.post("/set")
async def set(
    amount: int,
    reason: str = "MANUAL",
    redis=Depends(get_redis),
    admin=Depends(require_role("admin")),
):
    await admin_set_surge(redis, amount, reason)
    return {"message": "Surge enabled"}


@router.post("/disable")
async def disable(
    redis=Depends(get_redis),
    admin=Depends(require_role("admin")),
):
    await admin_disable_surge(redis)
    return {"message": "Surge disabled"}
