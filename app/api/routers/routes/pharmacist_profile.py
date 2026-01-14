from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
 
from core.database import get_db
from core.rbac import require_role
from models.user import User
from services.geocoding_service import geocode_address
from core.redis import get_redis
 
import enum
from pydantic import BaseModel, Field
 
router = APIRouter(prefix="/pharmacist/profile", tags=["Pharmacist Profile"])
 
# ======================================================
# 🇮🇳 Indian States Dropdown
# ======================================================
class IndianState(str, enum.Enum):
    ANDHRA_PRADESH = "Andhra Pradesh"
    TELANGANA = "Telangana"
    TAMIL_NADU = "Tamil Nadu"
    KARNATAKA = "Karnataka"
    MAHARASHTRA = "Maharashtra"
    KERALA = "Kerala"
    DELHI = "Delhi"
    WEST_BENGAL = "West Bengal"
    GUJARAT = "Gujarat"
    RAJASTHAN = "Rajasthan"
    MADHYA_PRADESH = "Madhya Pradesh"
    UTTAR_PRADESH = "Uttar Pradesh"
    BIHAR = "Bihar"
    ODISHA = "Odisha"
    PUNJAB = "Punjab"
    HARYANA = "Haryana"
 
 
# ======================================================
# 📦 Store Address Request
# ======================================================
class StoreAddressRequest(BaseModel):
    store_name: str = Field(..., example="Anand Pharma")
    shop_no: str = Field(..., example="Shop No 12")
    street: str = Field(..., example="MG Road")
    city: str = Field(..., example="Hyderabad")
    landmark: str | None = Field(None, example="Near Metro Station")
    state: IndianState
    pincode: str = Field(..., min_length=6, max_length=6)
 
 
# ======================================================
# 🏪 SET STORE ADDRESS
# ======================================================
@router.post("/set-store-address")
async def set_store_address(
    store_name: str = Query(..., example="Anand Pharma"),
    shop_no: str = Query(..., example="Shop No 12"),
    street: str = Query(..., example="MG Road"),
    city: str = Query(..., example="Hyderabad"),
    landmark: str | None = Query(None, example="Near Metro Station"),
    state: IndianState = Query(...),
    pincode: str = Query(..., min_length=6, max_length=6),
 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("pharmacist")),
):
    # 🔹 Build full address string
    full_address = f"{store_name}, {shop_no}, {street}, {city}, {state.value} - {pincode}"
 
    lat, lng = geocode_address(full_address)
 
    current_user.store_name = store_name
    current_user.store_address = full_address
    current_user.last_latitude = lat
    current_user.last_longitude = lng
    current_user.last_location_at = func.now()
    current_user.is_online = True
 
    # 🔹 Push pharmacist to Redis GEO (static)
    redis = await get_redis()
    await redis.geoadd(
        "pharmacists:live",
        (lng, lat, current_user.id)
    )
 
    await db.commit()
 
    return {
        "message": "Store address updated successfully",
        "store_name": store_name,
        "address": full_address,
        "latitude": lat,
        "longitude": lng
    }
 
# ======================================================
# 🟢 GO ONLINE
# ======================================================
@router.post("/go-online")
async def go_online(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("pharmacist"))
):
    if not current_user.last_latitude or not current_user.last_longitude:
        raise HTTPException(400, "Store address not set")
 
    redis = await get_redis()
    await redis.geoadd(
        "pharmacists:live",
        (
            current_user.last_longitude,
            current_user.last_latitude,
            current_user.id
        )
    )
 
    current_user.is_online = True
    await db.commit()
 
    return {"message": "Pharmacist is online"}
 
 
# ======================================================
# 🔴 GO OFFLINE
# ======================================================
@router.post("/go-offline")
async def go_offline(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("pharmacist"))
):
    redis = await get_redis()
    await redis.zrem("pharmacists:live", current_user.id)
 
    current_user.is_online = False
    await db.commit()
 
    return {"message": "Pharmacist is offline"}
 