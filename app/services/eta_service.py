import requests
from core.config import settings

# ======================================================
# ⏱️ ETA CALCULATION SERVICE
# ======================================================

def calculate_eta(
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
) -> int:
    """
    Returns ETA in minutes
    Fallbacks safely if Google Maps fails
    """

    DEFAULT_ETA = 30  # minutes

    # 🚫 Missing coordinates
    if not all([origin_lat, origin_lng, dest_lat, dest_lng]):
        return DEFAULT_ETA

    # 🧪 No Google API → fallback
    if not settings.GOOGLE_MAPS_API_KEY:
        return DEFAULT_ETA

    try:
        response = requests.get(
            "https://maps.googleapis.com/maps/api/directions/json",
            params={
                "origin": f"{origin_lat},{origin_lng}",
                "destination": f"{dest_lat},{dest_lng}",
                "key": settings.GOOGLE_MAPS_API_KEY,
            },
            timeout=5,
        )

        data = response.json()

        if data.get("status") != "OK":
            return DEFAULT_ETA

        seconds = data["routes"][0]["legs"][0]["duration"]["value"]

        # ✅ Minimum ETA = 1 minute
        return max(1, round(seconds / 60))

    except Exception:
        return DEFAULT_ETA
