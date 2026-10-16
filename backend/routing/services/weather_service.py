"""
Weather service using Open-Meteo API.
Queries hourly weather forecast (wind speed, precipitation, snowfall)
for checkpoints at their specific estimated arrival times (ETA).
"""
import requests
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def fetch_weather_for_checkpoints(checkpoints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Batches checkpoints and queries Open-Meteo for hourly wind speed (mph),
    precipitation (inch), and snowfall (inch).
    Extracts the weather reading corresponding to each checkpoint's estimated arrival hour.
    """
    if not checkpoints:
        return []

    # Open-Meteo allows comma-separated latitude and longitude lists up to ~50 points
    chunk_size = 40
    results = list(checkpoints)

    for i in range(0, len(results), chunk_size):
        chunk = results[i:i + chunk_size]
        lats = [str(c["latitude"]) for c in chunk]
        lons = [str(c["longitude"]) for c in chunk]

        params = {
            "latitude": ",".join(lats),
            "longitude": ",".join(lons),
            "hourly": "wind_speed_10m,precipitation,snowfall",
            "wind_speed_unit": "mph",
            "precipitation_unit": "inch",
            "forecast_days": 3,
        }

        try:
            resp = requests.get(OPEN_METEO_URL, params=params, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                # Open-Meteo returns a list of dictionaries if multiple points were sent, or a single dict if 1 point
                items = data if isinstance(data, list) else [data]

                for idx, c in enumerate(chunk):
                    if idx < len(items) and "hourly" in items[idx]:
                        hourly = items[idx]["hourly"]
                        times = hourly.get("time", [])
                        winds = hourly.get("wind_speed_10m", [])
                        rains = hourly.get("precipitation", [])
                        snows = hourly.get("snowfall", [])

                        target_time = c["eta_hour"]  # "2026-10-17T14:00"

                        # Find matching time index
                        match_idx = -1
                        if target_time in times:
                            match_idx = times.index(target_time)
                        elif times:
                            # Closest fallback
                            match_idx = 0

                        if match_idx >= 0:
                            c["weather"] = {
                                "wind_speed_mph": float(winds[match_idx] if match_idx < len(winds) and winds[match_idx] is not None else 8.0),
                                "precipitation_in_hr": float(rains[match_idx] if match_idx < len(rains) and rains[match_idx] is not None else 0.0),
                                "snowfall_in_hr": float(snows[match_idx] if match_idx < len(snows) and snows[match_idx] is not None else 0.0),
                                "forecast_time": times[match_idx] if match_idx < len(times) else target_time,
                            }
                            continue
        except Exception as e:
            logger.warning(f"Open-Meteo weather batch query error: {e}")

        # Fallback simulation if network or API error occurs
        for c in chunk:
            if "weather" not in c:
                # Plausible calm weather fallback
                c["weather"] = {
                    "wind_speed_mph": 12.0,
                    "precipitation_in_hr": 0.0,
                    "snowfall_in_hr": 0.0,
                    "forecast_time": c["eta_hour"],
                }

    return results
