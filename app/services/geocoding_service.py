import requests
from core.config import settings

def geocode_address(address: str):
    # Default center of India (safe fallback)
    DEFAULT_LAT = 20.5937
    DEFAULT_LNG = 78.9629

    if not settings.GOOGLE_MAPS_API_KEY:
        return DEFAULT_LAT, DEFAULT_LNG

    try:
        res = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={
                "address": address,
                "key": settings.GOOGLE_MAPS_API_KEY,
            },
            timeout=5,
        )
        data = res.json()

        if data.get("status") != "OK":
            return DEFAULT_LAT, DEFAULT_LNG

        location = data["results"][0]["geometry"]["location"]
        return location["lat"], location["lng"]

    except Exception:
        return DEFAULT_LAT, DEFAULT_LNG
