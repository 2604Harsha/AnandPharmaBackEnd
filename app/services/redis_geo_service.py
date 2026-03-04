from typing import Optional, List


class RedisGeoService:
    # Redis GEO Keys
    DELIVERY_KEY = "delivery:agents:live"
    PHARMACIST_KEY = "pharmacists:live"

    # =========================================================
    # 🚚 DELIVERY AGENTS
    # =========================================================

    @staticmethod
    async def update_agent_location(
        redis,
        agent_id: int,
        latitude: float,
        longitude: float,
    ):
        """
        Add or update delivery agent live location in Redis GEO.
        IMPORTANT: Redis expects (longitude, latitude, member)
        """
        await redis.geoadd(
            RedisGeoService.DELIVERY_KEY,
            (longitude, latitude, str(agent_id))
        )

    @staticmethod
    async def remove_agent(redis, agent_id: int):
        """
        Remove delivery agent from live tracking (offline).
        """
        await redis.zrem(
            RedisGeoService.DELIVERY_KEY,
            str(agent_id),
        )

    @staticmethod
    async def find_nearest_agent(
        redis,
        latitude: float,
        longitude: float,
        radius_km: int = 10,
    ) -> Optional[str]:
        """
        Find nearest available delivery agent.
        Uses Redis 7 GEOSEARCH (recommended).
        """
        results = await redis.georadius(
            RedisGeoService.DELIVERY_KEY,
            longitude,
            latitude,
            radius_km,
            unit="km",
            count=1,
            sort="ASC",
        )

        return results[0] if results else None

    @staticmethod
    async def get_all_live_agents(redis) -> List[str]:
        """
        Debug helper – get all live agents.
        """
        return await redis.zrange(
            RedisGeoService.DELIVERY_KEY,
            0,
            -1,
        )

    # =========================================================
    # 💊 PHARMACISTS
    # =========================================================

    @staticmethod
    async def update_pharmacist_location(
        redis,
        pharmacist_id: int,
        latitude: float,
        longitude: float,
    ):
        await redis.geoadd(
            RedisGeoService.PHARMACIST_KEY,
            (longitude, latitude, str(pharmacist_id))
        )

    @staticmethod
    async def remove_pharmacist(redis, pharmacist_id: int):
        await redis.zrem(
            RedisGeoService.PHARMACIST_KEY,
            str(pharmacist_id),
        )

    @staticmethod
    async def find_nearest_pharmacists(
        redis,
        latitude: float,
        longitude: float,
        radius_km: int = 5,
        count: int = 5,
    ) -> List[str]:
        return await redis.georadius(
            RedisGeoService.PHARMACIST_KEY,
            longitude,
            latitude,
            radius_km,
            unit="km",
            count=count,
            sort="ASC",
        )