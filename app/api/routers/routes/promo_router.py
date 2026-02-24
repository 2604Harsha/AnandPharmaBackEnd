# routers/promo_router.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from core.rbac import require_role
from core.database import get_db
from schemas.promo_code import (
    PromoCodeCreate,
    PromoCodeUpdate,
    PromoCodeOut,
)
from services.promo_service import (
    create_promo,
    get_all_promos,
    get_promo_by_id,
    update_promo,
    delete_promo,
)

router = APIRouter(prefix="/promo-codes", tags=["Promo Codes"])


# ✅ CREATE
@router.post("/", response_model=PromoCodeOut)
async def create_promo_code(
    data: PromoCodeCreate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("admin"))
):
    return await create_promo(db, data)


# ✅ GET ALL
@router.get("/", response_model=List[PromoCodeOut])
async def list_promo_codes(db: AsyncSession = Depends(get_db),admin=Depends(require_role("admin"))):
    return await get_all_promos(db)


# ✅ GET ONE
@router.get("/{promo_id}", response_model=PromoCodeOut)
async def get_single_promo(
    promo_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("admin"))
):
    promo = await get_promo_by_id(db, promo_id)
    if not promo:
        raise HTTPException(status_code=404, detail="Promo not found")
    return promo


# ✅ UPDATE (PUT)
@router.put("/{promo_id}", response_model=PromoCodeOut)
async def update_promo_code(
    promo_id: int,
    data: PromoCodeUpdate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("admin"))
):
    promo = await update_promo(db, promo_id, data)
    if not promo:
        raise HTTPException(status_code=404, detail="Promo not found")
    return promo


# ✅ DELETE
@router.delete("/{promo_id}")
async def delete_promo_code(
    promo_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_role("admin"))
):
    success = await delete_promo(db, promo_id)
    if not success:
        raise HTTPException(status_code=404, detail="Promo not found")
    return {"message": "Promo deleted successfully"}