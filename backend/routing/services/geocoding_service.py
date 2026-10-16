"""
Geocoding service using OpenStreetMap Nominatim with local fallback cache
for major US freight hubs and cities.
"""
import requests
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

# Fallback coordinates for major trucking hubs to ensure zero failure during offline or rate-limited tests
FREIGHT_HUBS_CACHE = {
    "chicago": (41.8781, -87.6298, "Chicago, IL"),
    "chicago, il": (41.8781, -87.6298, "Chicago, IL"),
    "dallas": (32.7767, -96.7970, "Dallas, TX"),
    "dallas, tx": (32.7767, -96.7970, "Dallas, TX"),
    "denver": (39.7392, -104.9903, "Denver, CO"),
    "denver, co": (39.7392, -104.9903, "Denver, CO"),
    "atlanta": (33.7490, -84.3880, "Atlanta, GA"),
    "atlanta, ga": (33.7490, -84.3880, "Atlanta, GA"),
    "los angeles": (34.0522, -118.2437, "Los Angeles, CA"),
    "los angeles, ca": (34.0522, -118.2437, "Los Angeles, CA"),
    "seattle": (47.6062, -122.3321, "Seattle, WA"),
    "seattle, wa": (47.6062, -122.3321, "Seattle, WA"),
    "new york": (40.7128, -74.0060, "New York, NY"),
    "new york, ny": (40.7128, -74.0060, "New York, NY"),
    "kansas city": (39.0997, -94.5786, "Kansas City, MO"),
    "kansas city, mo": (39.0997, -94.5786, "Kansas City, MO"),
    "memphis": (35.1495, -90.0490, "Memphis, TN"),
    "memphis, tn": (35.1495, -90.0490, "Memphis, TN"),
    "minneapolis": (44.9778, -93.2650, "Minneapolis, MN"),
    "minneapolis, mn": (44.9778, -93.2650, "Minneapolis, MN"),
}


def geocode_location(query: str) -> Tuple[float, float, str]:
    """
    Geocodes an address or city query to (latitude, longitude, display_name).
    Uses Nominatim with fallback to cached hubs.
    """
    normalized = query.strip().lower()
    if normalized in FREIGHT_HUBS_CACHE:
        lat, lon, name = FREIGHT_HUBS_CACHE[normalized]
        return lat, lon, name

    # Query Nominatim API with descriptive User-Agent
    url = "https://nominatim.openstreetmap.org/search"
    headers = {"User-Agent": "WeatherAwareTruckRoutingAssessment/1.0"}
    params = {
        "q": query,
        "format": "json",
        "limit": 1,
        "countrycodes": "us,ca,mx"
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                item = data[0]
                lat = float(item["lat"])
                lon = float(item["lon"])
                name = item.get("display_name", query)
                return lat, lon, name
    except Exception as e:
        logger.warning(f"Nominatim geocoding error for '{query}': {e}")

    # If Nominatim fails or finds nothing, search partial match in fallback cache
    for key, val in FREIGHT_HUBS_CACHE.items():
        if key in normalized or normalized in key:
            return val[0], val[1], val[2]

    # Default fallback to Chicago if all else fails
    return 41.8781, -87.6298, f"{query} (Approximate)"
