class RedisGeoService:
    DELIVERY_KEY = "delivery:agents:live"
    PHARMACIST_KEY = "pharmacists:live"

    # ---------------- DELIVERY (EXISTING) ----------------
    @staticmethod
    async def find_nearest_agent(redis, latitude, longitude, radius_km=10):
        results = await redis.georadius(
            RedisGeoService.DELIVERY_KEY,
            longitude=longitude,
            latitude=latitude,
            radius=radius_km,
            unit="km",
            withdist=False,
            count=1,
            sort="ASC"
        )
        return results[0] if results else None

    # ---------------- PHARMACIST (NEW) ----------------
    @staticmethod
    async def find_nearest_pharmacists(
        redis,
        latitude,
        longitude,
        radius_km=5,
        count=5
    ):
        return await redis.geosearch(
            RedisGeoService.PHARMACIST_KEY,
            longitude=longitude,
            latitude=latitude,
            radius=radius_km,
            unit="km",
            count=count,
            sort="ASC"
        )
