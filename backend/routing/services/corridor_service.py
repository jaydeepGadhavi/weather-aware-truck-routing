"""
Corridor Weather Service.
Generates grid data along the route corridor for hours 0 to 48 to power
the smooth time-scrubbing weather heatmap slider.
"""
import requests
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def get_corridor_heatmap_data(
    all_checkpoints: List[Dict[str, Any]],
    num_hours: int = 48
) -> Dict[str, Any]:
    """
    Samples corridor points from across all 3 routes and queries the 48-hour forecast.
    Produces pre-computed heatmap intensity arrays for each hour t in [0..47],
    allowing the frontend slider to animate smoothly at 60fps.
    """
    if not all_checkpoints:
        return {"timestamps": [], "hours_data": {}}

    # Deduplicate / downsample corridor anchor points
    unique_coords: List[Tuple[float, float]] = []
    seen = set()
    for cp in all_checkpoints:
        key = (round(cp["latitude"], 2), round(cp["longitude"], 2))
        if key not in seen:
            seen.add(key)
            unique_coords.append((cp["latitude"], cp["longitude"]))

    # Cap at ~25 corridor points to keep API payload fast and responsive
    if len(unique_coords) > 25:
        step = len(unique_coords) / 25.0
        unique_coords = [unique_coords[int(i * step)] for i in range(25)]

    lats = [str(lat) for lat, lon in unique_coords]
    lons = [str(lon) for lat, lon in unique_coords]

    params = {
        "latitude": ",".join(lats),
        "longitude": ",".join(lons),
        "hourly": "wind_speed_10m,precipitation",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "forecast_days": 3,
    }

    hours_data = {}
    timestamps = []

    try:
        resp = requests.get(OPEN_METEO_URL, params=params, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            items = data if isinstance(data, list) else [data]

            if items and "hourly" in items[0]:
                raw_times = items[0]["hourly"].get("time", [])[:num_hours]
                timestamps = raw_times

                for h_idx in range(len(timestamps)):
                    points_for_hour = []
                    for pt_idx, (lat, lon) in enumerate(unique_coords):
                        if pt_idx < len(items) and "hourly" in items[pt_idx]:
                            hourly = items[pt_idx]["hourly"]
                            winds = hourly.get("wind_speed_10m", [])
                            precip = hourly.get("precipitation", [])

                            w_val = winds[h_idx] if h_idx < len(winds) and winds[h_idx] is not None else 10.0
                            p_val = precip[h_idx] if h_idx < len(precip) and precip[h_idx] is not None else 0.0

                            # Normalize intensity for Leaflet heat [0.1 to 1.0]
                            # Severe winds (>45) or high precip (>0.5) get high intensity
                            intensity = min(1.0, max(0.15, (w_val / 55.0) * 0.7 + (p_val / 1.0) * 0.3))

                            points_for_hour.append({
                                "lat": lat,
                                "lng": lon,
                                "intensity": round(intensity, 2),
                                "wind_mph": round(w_val, 1),
                                "rain_in": round(p_val, 2),
                            })
                    hours_data[str(h_idx)] = points_for_hour

    except Exception as e:
        logger.warning(f"Corridor weather fetch error: {e}")

    # Fallback if network issue
    if not hours_data:
        for h in range(num_hours):
            hours_data[str(h)] = [
                {"lat": lat, "lng": lon, "intensity": 0.25, "wind_mph": 12.0, "rain_in": 0.0}
                for lat, lon in unique_coords
            ]

    return {
        "num_hours": len(hours_data),
        "timestamps": timestamps,
        "hours_data": hours_data,
    }
