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

router = APIRouter(prefix="/delivery-agent/profile", tags=["Delivery Agent Profile"])

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

@router.post("/set-delivery-address")
async def set_delivery_address(
    street: str = Query(..., example="MG Road"),
    city: str = Query(..., example="Hyderabad"),
    state: IndianState = Query(...),
    pincode: str = Query(..., min_length=6, max_length=6),

    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("delivery_agent")),
):
    # 🔹 Build address
    full_address = f"{street}, {city}, {state.value} - {pincode}"

    lat, lng = geocode_address(full_address)

    # 🔹 Save to user
    current_user.da_street = street
    current_user.da_city = city
    current_user.da_state = state.value
    current_user.da_pincode = pincode
    current_user.da_address = full_address
    current_user.last_latitude = lat
    current_user.last_longitude = lng
    current_user.last_location_at = func.now()
    current_user.is_online = True

    # 🔹 Push to Redis GEO
    redis = await get_redis()
    await redis.geoadd(
        "delivery_agents:live",
        (lng, lat, current_user.id)
    )

    await db.commit()

    return {
        "message": "Delivery address updated successfully",
        "address": full_address,
        "latitude": lat,
        "longitude": lng,
    }


@router.post("/go-online")
async def go_online_delivery(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("delivery_agent")),
):
    if not current_user.last_latitude or not current_user.last_longitude:
        raise HTTPException(400, "Delivery address not set")

    redis = await get_redis()
    await redis.geoadd(
        "delivery_agents:live",
        (
            current_user.last_longitude,
            current_user.last_latitude,
            current_user.id,
        ),
    )

    current_user.is_online = True
    await db.commit()

    return {"message": "Delivery agent is online"}

@router.post("/go-offline")
async def go_offline_delivery(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("delivery_agent")),
):
    redis = await get_redis()
    await redis.zrem("delivery_agents:live", current_user.id)

    current_user.is_online = False
    await db.commit()

    return {"message": "Delivery agent is offline"}
