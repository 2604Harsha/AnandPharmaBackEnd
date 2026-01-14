import redis.asyncio as redis
from core.config import settings

redis_client = redis.Redis(
    host=getattr(settings, "REDIS_HOST", "localhost"),
    port=getattr(settings, "REDIS_PORT", 6379),
    decode_responses=True
)

async def get_redis():
    return redis_client
