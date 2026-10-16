"""
Route Recommendation Engine.
Ranks candidate routes based on Spotter's specified preference hierarchy:
1. Fewest Severe miles (and No Travel miles)
2. Fewest High miles
3. Lowest average risk
4. Shortest travel times
"""
from typing import List, Dict, Any


def rank_routes(routes_with_metrics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sorts routes according to the strict priority rules:
    Rule 1: Fewest Severe miles (No Travel miles penalized highest + Severe miles)
    Rule 2: Fewest High miles
    Rule 3: Lowest average risk score
    Rule 4: Shortest travel time (duration_seconds)
    """
    def sorting_key(route: Dict[str, Any]):
        metrics = route.get("metrics", {})
        # Combined severe + no_travel (or separate tuple ensuring no_travel is penalized first)
        no_travel_miles = metrics.get("no_travel_miles", 0.0)
        severe_miles = metrics.get("severe_miles", 0.0)
        high_miles = metrics.get("high_miles", 0.0)
        avg_risk = metrics.get("average_risk_score", 1.0)
        duration_sec = route.get("duration_seconds", 0.0)

        # Tuple comparison in Python naturally sorts by element 0, then 1, then 2, then 3
        return (no_travel_miles, severe_miles, high_miles, avg_risk, duration_sec)

    sorted_routes = sorted(routes_with_metrics, key=sorting_key)

    # Attach rank, recommendation flag, and human explanation
    for idx, r in enumerate(sorted_routes):
        r["rank"] = idx + 1
        r["is_recommended"] = (idx == 0)
        if idx == 0:
            r["recommendation_reason"] = (
                f"Safest route: {r['metrics']['severe_miles']:.1f} severe miles, "
                f"{r['metrics']['high_miles']:.1f} high-risk miles, "
                f"avg risk score {r['metrics']['average_risk_score']:.2f}."
            )
        else:
            r["recommendation_reason"] = (
                f"Alternative route #{idx + 1}: higher risk or longer travel time."
            )

    return sorted_routes
