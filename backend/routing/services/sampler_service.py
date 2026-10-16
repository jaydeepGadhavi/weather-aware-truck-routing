"""
Route checkpoint sampling service.
Samples coordinates along a GeoJSON route line at 10, 25, or 50 mile intervals,
calculating exact cumulative distances and estimated arrival times (ETA).
"""
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two points in miles."""
    R = 3958.8  # Earth radius in miles
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def sample_route_checkpoints(
    geometry: Dict[str, Any],
    total_distance_miles: float,
    total_duration_seconds: float,
    departure_time: datetime,
    interval_miles: float = 25.0
) -> List[Dict[str, Any]]:
    """
    Samples checkpoints along the route line every `interval_miles` (10, 25, or 50 miles).
    Computes cumulative distance and estimated arrival time (ETA) for each checkpoint.
    """
    coords = geometry.get("coordinates", [])
    if not coords or len(coords) < 2:
        return []

    # 1. Compute segment distances and total polyline distance
    cumulative_dists = [0.0]
    for i in range(1, len(coords)):
        lon1, lat1 = coords[i - 1]
        lon2, lat2 = coords[i]
        seg_dist = haversine_miles(lat1, lon1, lat2, lon2)
        cumulative_dists.append(cumulative_dists[-1] + seg_dist)

    total_polyline_miles = cumulative_dists[-1]
    # Scaling factor to match actual OSRM road distance
    scale_factor = (total_distance_miles / total_polyline_miles) if total_polyline_miles > 0 else 1.0

    target_distances = []
    curr = 0.0
    while curr < total_distance_miles:
        target_distances.append(curr)
        curr += interval_miles
    # Always include the destination
    if not target_distances or (total_distance_miles - target_distances[-1] > 2.0):
        target_distances.append(total_distance_miles)

    checkpoints = []
    seg_idx = 0

    for idx, target_dist in enumerate(target_distances):
        # Target distance in polyline units
        target_poly_dist = target_dist / scale_factor if scale_factor > 0 else 0

        # Advance to the segment containing target_poly_dist
        while seg_idx < len(cumulative_dists) - 2 and cumulative_dists[seg_idx + 1] < target_poly_dist:
            seg_idx += 1

        p1_dist = cumulative_dists[seg_idx]
        p2_dist = cumulative_dists[seg_idx + 1]
        seg_len = p2_dist - p1_dist

        if seg_len > 0:
            fraction = max(0.0, min(1.0, (target_poly_dist - p1_dist) / seg_len))
        else:
            fraction = 0.0

        lon1, lat1 = coords[seg_idx]
        lon2, lat2 = coords[seg_idx + 1]
        interp_lat = lat1 + fraction * (lat2 - lat1)
        interp_lon = lon1 + fraction * (lon2 - lon1)

        # Elapsed time proportional to cumulative distance
        progress_ratio = (target_dist / total_distance_miles) if total_distance_miles > 0 else 0
        elapsed_seconds = progress_ratio * total_duration_seconds
        eta = departure_time + timedelta(seconds=elapsed_seconds)

        checkpoints.append({
            "checkpoint_index": idx,
            "latitude": round(interp_lat, 5),
            "longitude": round(interp_lon, 5),
            "distance_from_origin_miles": round(target_dist, 1),
            "elapsed_time_hours": round(elapsed_seconds / 3600, 2),
            "eta": eta.isoformat(),
            "eta_hour": eta.strftime("%Y-%m-%dT%H:00"),
        })

    return checkpoints
