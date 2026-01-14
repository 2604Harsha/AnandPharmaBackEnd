class DeliveryLiveService:
    GEO_KEY = "delivery:agents:live"

    @staticmethod
    async def update_agent_location(redis, agent_id: str, lat: float, lng: float):
        """
        SAFE redis-py GEOADD call (tuple format)
        """
        await redis.geoadd(
            DeliveryLiveService.GEO_KEY,
            (lng, lat, agent_id)
        )

    @staticmethod
    async def get_agent_location(redis, agent_id: str):
        pos = await redis.geopos(
            DeliveryLiveService.GEO_KEY,
            agent_id
        )

        if not pos or pos[0] is None:
            return None

        lng, lat = pos[0]
        return {
            "lat": float(lat),
            "lng": float(lng)
        }
