import requests
from core.config import settings

def get_route_polyline(origin, destination):
    # Check if we are in Mock mode
    if settings.GOOGLE_MAPS_API_KEY == "MOCK" or not settings.GOOGLE_MAPS_API_KEY:
        print("MAPS NOTICE: Using Mock Polyline because no API Key is provided.")
        # This is a sample polyline string representing a straight line
        return "_p~iF~ps|U_ulLnnqC_mqNvxq`@"

    try:
        res = requests.get(
            "https://maps.googleapis.com/maps/api/directions/json",
            params={
                "origin": origin,
                "destination": destination,
                "key": settings.GOOGLE_MAPS_API_KEY,
            },
            timeout=5

        )
        data = res.json()
        
        # Safety check if Google returns an error (like invalid key)
        if data.get("status") != "OK":
            return "_p~iF~ps|U_ulLnnqC_mqNvxq`@"
            
        return data["routes"][0]["overview_polyline"]["points"]
    except Exception as e:
        print(f"Maps Error: {e}")
        return "_p~iF~ps|U_ulLnnqC_mqNvxq`@"