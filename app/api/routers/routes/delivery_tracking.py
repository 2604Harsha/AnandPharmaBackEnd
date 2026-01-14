from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta, timezone
from sqlalchemy import select

from core.database import get_db
from core.redis import get_redis
from core.rbac import require_role
from core.websocket_manager import manager

from schemas.agent_location import AgentLocationUpdate
from models.delivery_location import DeliveryLocation
from models.delivery import Delivery
from models.order_address import OrderAddress
from models.user import User

from services.delivery_live_service import DeliveryLiveService
from services.redis_geo_service import RedisGeoService
from services.map_services import get_route_polyline
from services.geocoding_service import geocode_address

router = APIRouter(prefix="/tracking", tags=["Tracking"])

THROTTLE_SECONDS = 5
OFFLINE_TTL = 30


# ======================================================
# 🚴 AGENT LOCATION UPDATE (AUTO GPS via ADDRESS)
# ACCESS: DELIVERY_AGENT
# ======================================================
@router.post("/agent/update")
async def update_agent_location(
    payload: AgentLocationUpdate,
    redis=Depends(get_redis),
    agent: User = Depends(require_role("delivery_agent")),
):
    agent_id = str(agent.id)

    full_address = f"{payload.address}, {payload.landmark or ''}, {payload.city}, {payload.state}, {payload.pincode}"
    latitude, longitude = geocode_address(full_address)

    if not latitude or not longitude:
        raise HTTPException(400, "Unable to detect location")

    last_update = await redis.hget(f"delivery:agent:{agent_id}", "updated_at")
    if last_update:
        last_time = datetime.fromisoformat(last_update)
        if datetime.now(timezone.utc) - last_time < timedelta(seconds=THROTTLE_SECONDS):
            return {"message": "Location throttled"}

    await DeliveryLiveService.update_agent_location(redis, agent_id, latitude, longitude)

    await redis.hset(
        f"delivery:agent:{agent_id}",
        mapping={
            "lat": latitude,
            "lng": longitude,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "online": 1
        }
    )

    await redis.setex(f"delivery:agent:online:{agent_id}", OFFLINE_TTL, 1)

    await manager.send_delivery(
        agent.id,
        {
            "type": "AGENT_LOCATION",
            "agent_id": agent.id,
            "lat": latitude,
            "lng": longitude,
        }
    )

    return {"message": "Location updated", "lat": latitude, "lng": longitude}


# ======================================================
# 🔎 FIND NEAREST AGENT (REDIS GEOSEARCH)
# ACCESS: ADMIN
# ======================================================
@router.get("/nearest-agent")
async def nearest_agent(
    latitude: float,
    longitude: float,
    redis=Depends(get_redis),
    admin=Depends(require_role("admin")),
):
    agent_id = await RedisGeoService.find_nearest_agent(redis, latitude, longitude)
    if not agent_id:
        raise HTTPException(404, "No nearby agents")
    return {"agent_id": agent_id}


# ======================================================
# 📍 LIVE DELIVERY TRACKING
# ACCESS: USER, ADMIN
# ======================================================
@router.get("/order/{order_id}")
async def live_delivery_tracking(
    order_id: int,
    redis=Depends(get_redis),
    user=Depends(require_role("user", "admin")),
):
    agent_id = await redis.hget(f"delivery:order:{order_id}", "agent_id")
    status = await redis.hget(f"delivery:order:{order_id}", "status")

    if not agent_id:
        raise HTTPException(404, "Delivery not assigned")

    location = await DeliveryLiveService.get_agent_location(redis, agent_id)
    if not location:
        raise HTTPException(404, "Live location unavailable")

    return {"order_id": order_id, "status": status, "agent_location": location}


# ======================================================
# 📦 ORDER → AGENT ROUTE (MAP ANIMATION)
# ACCESS: USER, ADMIN
# ======================================================
@router.get("/order/{order_id}/route")
async def order_route_animation(
    order_id: int,
    db=Depends(get_db),
    redis=Depends(get_redis),
    user=Depends(require_role("user", "admin")),
):
    delivery = (
        await db.execute(select(Delivery).where(Delivery.order_id == order_id))
    ).scalar_one_or_none()

    if not delivery:
        raise HTTPException(404, "Delivery not found")

    address = (
        await db.execute(select(OrderAddress).where(OrderAddress.order_id == order_id))
    ).scalar_one()

    pos = await redis.geopos("delivery:agents:live", str(delivery.delivery_user_id))
    if not pos or not pos[0]:
        raise HTTPException(404, "Agent location unavailable")

    lng, lat = pos[0]
    polyline = get_route_polyline(
        f"{lat},{lng}",
        f"{address.latitude},{address.longitude}"
    )

    return {
        "agent": {"lat": lat, "lng": lng},
        "destination": {"lat": address.latitude, "lng": address.longitude},
        "polyline": polyline
    }


# ======================================================
# 📊 ADMIN LIVE MAP – ALL AGENTS
# ACCESS: ADMIN
# ======================================================
@router.get("/admin/agents")
async def admin_agents_map(
    redis=Depends(get_redis),
    admin=Depends(require_role("admin")),
):
    agent_ids = await redis.zrange("delivery:agents:live", 0, -1)
    response = []

    for agent_id in agent_ids:
        pos = await redis.geopos("delivery:agents:live", agent_id)
        if pos and pos[0]:
            lng, lat = pos[0]
            response.append({
                "agent_id": agent_id,
                "lat": lat,
                "lng": lng,
                "online": True,
            })

    return response
