"""
Pipeline Orchestrator Service.
Coordinates the end-to-end execution flow of the route analysis:
1. Geocoding
2. Highway routing (OSRM)
3. Checkpoint sampling & ETA calculation
4. Weather forecasting at ETA (Open-Meteo)
5. Safety risk scoring & weight rule application
6. Hierarchical route recommendation
7. 48-hour corridor heatmap synthesis
"""
import time
import logging
from typing import Dict, Any

from .geocoding_service import geocode_location
from .osrm_service import generate_3_routes
from .sampler_service import sample_route_checkpoints
from .weather_service import fetch_weather_for_checkpoints
from .risk_engine import evaluate_checkpoint_risk, RiskLevel
from .recommendation_engine import rank_routes
from .corridor_service import get_corridor_heatmap_data

logger = logging.getLogger("routing.pipeline")


def execute_routing_pipeline(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes the clean step-by-step pipeline with timing and verbose diagnostics.
    """
    start_time = time.perf_counter()
    origin_query = params["origin"]
    dest_query = params["destination"]
    departure_time = params["departure_time"]
    load_weight_lbs = params["load_weight_lbs"]
    sample_interval = float(params["sample_interval_miles"])

    logger.info(f"==> Starting Route Analysis: '{origin_query}' -> '{dest_query}' | Weight: {load_weight_lbs:,.0f} lbs | Interval: {sample_interval} mi")

    # Step 1: Geocode Origin & Destination
    orig_lat, orig_lon, orig_name = geocode_location(origin_query)
    dest_lat, dest_lon, dest_name = geocode_location(dest_query)
    logger.info(f"Step 1/6 [Geocode]: Origin=({orig_lat:.4f}, {orig_lon:.4f}) | Destination=({dest_lat:.4f}, {dest_lon:.4f})")

    # Step 2: Generate 3 Alternative Routes
    raw_routes = generate_3_routes(orig_lat, orig_lon, dest_lat, dest_lon)
    logger.info(f"Step 2/6 [OSRM Routing]: Successfully retrieved {len(raw_routes)} route options")

    all_route_checkpoints = []
    processed_routes = []

    # Step 3 & 4: Sampling, Weather & Risk Evaluation for each route
    for route_idx, route in enumerate(raw_routes):
        total_dist_mi = route["distance_miles"]
        total_dur_sec = route["duration_seconds"]

        # Sample checkpoints at specified intervals
        checkpoints = sample_route_checkpoints(
            geometry=route["geometry"],
            total_distance_miles=total_dist_mi,
            total_duration_seconds=total_dur_sec,
            departure_time=departure_time,
            interval_miles=sample_interval
        )

        # Batch query Open-Meteo for checkpoint weather at exact ETA
        checkpoints = fetch_weather_for_checkpoints(checkpoints)

        # Evaluate risk thresholds and load weight rules
        severe_cps = 0
        no_travel_cps = 0
        high_cps = 0
        moderate_cps = 0
        low_cps = 0
        total_score = 0.0

        for cp in checkpoints:
            w = cp.get("weather", {})
            risk_eval = evaluate_checkpoint_risk(
                wind_mph=w.get("wind_speed_mph", 0.0),
                rain_in_hr=w.get("precipitation_in_hr", 0.0),
                snow_in_hr=w.get("snowfall_in_hr", 0.0),
                load_weight_lbs=load_weight_lbs
            )
            cp["risk"] = risk_eval
            total_score += risk_eval["overall_score"]

            lvl = risk_eval["overall_risk"]
            if lvl == RiskLevel.NO_TRAVEL.value:
                no_travel_cps += 1
            elif lvl == RiskLevel.SEVERE.value:
                severe_cps += 1
            elif lvl == RiskLevel.HIGH.value:
                high_cps += 1
            elif lvl == RiskLevel.MODERATE.value:
                moderate_cps += 1
            else:
                low_cps += 1

        num_cps = max(1, len(checkpoints))
        avg_risk = round(total_score / num_cps, 2)
        miles_per_cp = total_dist_mi / num_cps

        metrics = {
            "total_checkpoints": len(checkpoints),
            "no_travel_checkpoints": no_travel_cps,
            "no_travel_miles": round(no_travel_cps * miles_per_cp, 1),
            "severe_checkpoints": severe_cps,
            "severe_miles": round(severe_cps * miles_per_cp, 1),
            "high_checkpoints": high_cps,
            "high_miles": round(high_cps * miles_per_cp, 1),
            "moderate_checkpoints": moderate_cps,
            "moderate_miles": round(moderate_cps * miles_per_cp, 1),
            "low_checkpoints": low_cps,
            "low_miles": round(low_cps * miles_per_cp, 1),
            "average_risk_score": avg_risk,
            "dominant_risk": RiskLevel.from_score(avg_risk).value,
        }

        processed_routes.append({
            "id": route["id"],
            "name": route["name"],
            "distance_miles": total_dist_mi,
            "duration_hours": route["duration_hours"],
            "duration_seconds": total_dur_sec,
            "geometry": route["geometry"],
            "checkpoints": checkpoints,
            "metrics": metrics,
        })

        all_route_checkpoints.extend(checkpoints)

    logger.info(f"Step 3/6 [Sampling & Weather]: Processed {len(all_route_checkpoints)} total checkpoints across routes")

    # Step 5: Rank Candidate Routes
    ranked_routes = rank_routes(processed_routes)
    recommended = ranked_routes[0] if ranked_routes else None
    logger.info(f"Step 4/6 [Recommendation]: Selected '{recommended['name'] if recommended else 'N/A'}' as Recommended Route")

    # Step 6: Generate Corridor Forecast Heatmap (0-48 hours)
    corridor_heatmap = get_corridor_heatmap_data(all_route_checkpoints, num_hours=48)
    logger.info(f"Step 5/6 [Corridor Heatmap]: Built 48h matrix for {len(corridor_heatmap.get('timestamps', []))} hours")

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 1)
    logger.info(f"Step 6/6 [Complete]: Pipeline finished successfully in {elapsed_ms}ms")

    return {
        "query": {
            "origin": {"name": orig_name, "latitude": orig_lat, "longitude": orig_lon},
            "destination": {"name": dest_name, "latitude": dest_lat, "longitude": dest_lon},
            "departure_time": departure_time.isoformat(),
            "load_weight_lbs": load_weight_lbs,
            "sample_interval_miles": sample_interval,
        },
        "routes": ranked_routes,
        "corridor_heatmap": corridor_heatmap,
        "debug_meta": {
            "execution_time_ms": elapsed_ms,
            "status": "success",
            "routes_evaluated": len(ranked_routes),
            "checkpoints_sampled": len(all_route_checkpoints),
        }
    }
