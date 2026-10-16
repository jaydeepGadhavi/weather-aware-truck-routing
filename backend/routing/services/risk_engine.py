"""
Risk Assessment Engine.
Implements the exact weather risk thresholds and truck load weight rules
specified in the Spotter assessment document.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, List, Tuple


class RiskLevel(str, Enum):
    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"
    SEVERE = "Severe"
    NO_TRAVEL = "No Travel"

    @property
    def score(self) -> int:
        """Numeric scale for calculating average risk across checkpoints."""
        mapping = {
            RiskLevel.LOW: 1,
            RiskLevel.MODERATE: 2,
            RiskLevel.HIGH: 3,
            RiskLevel.SEVERE: 4,
            RiskLevel.NO_TRAVEL: 5,
        }
        return mapping[self]

    @classmethod
    def from_score(cls, score: float) -> "RiskLevel":
        if score >= 4.5:
            return cls.NO_TRAVEL
        elif score >= 3.5:
            return cls.SEVERE
        elif score >= 2.5:
            return cls.HIGH
        elif score >= 1.5:
            return cls.MODERATE
        return cls.LOW


def classify_wind(wind_mph: float) -> RiskLevel:
    """
    Wind risk classification (baseline):
    - Low: < 25 mph
    - Moderate: 25 - 34 mph
    - High: 35 - 44 mph
    - Severe: 45 - 54 mph
    - No Travel: >= 55 mph
    """
    if wind_mph >= 55.0:
        return RiskLevel.NO_TRAVEL
    elif wind_mph >= 45.0:
        return RiskLevel.SEVERE
    elif wind_mph >= 35.0:
        return RiskLevel.HIGH
    elif wind_mph >= 25.0:
        return RiskLevel.MODERATE
    else:
        return RiskLevel.LOW


def classify_rain(rain_in_hr: float) -> RiskLevel:
    """
    Rain risk classification:
    - Low: < 0.10 in/hr
    - Moderate: 0.10 - 0.25 in/hr
    - High: 0.25 - 0.50 in/hr
    - Severe: 0.50 - 1.00 in/hr
    - No Travel: > 1.00 in/hr
    """
    if rain_in_hr > 1.00:
        return RiskLevel.NO_TRAVEL
    elif rain_in_hr >= 0.50:
        return RiskLevel.SEVERE
    elif rain_in_hr >= 0.25:
        return RiskLevel.HIGH
    elif rain_in_hr >= 0.10:
        return RiskLevel.MODERATE
    else:
        return RiskLevel.LOW


def classify_snow(snow_in_hr: float) -> RiskLevel:
    """
    Snow risk classification:
    - Low: < 0.5 in/hr
    - Moderate: 0.5 - 1.0 in/hr
    - High: 1.0 - 2.0 in/hr
    - Severe: 2.0 - 3.0 in/hr
    - No Travel: > 3.0 in/hr
    """
    if snow_in_hr > 3.0:
        return RiskLevel.NO_TRAVEL
    elif snow_in_hr >= 2.0:
        return RiskLevel.SEVERE
    elif snow_in_hr >= 1.0:
        return RiskLevel.HIGH
    elif snow_in_hr >= 0.5:
        return RiskLevel.MODERATE
    else:
        return RiskLevel.LOW


def apply_load_rules(wind_mph: float, load_weight_lbs: float, baseline_wind_risk: RiskLevel) -> Tuple[RiskLevel, List[str]]:
    """
    Applies truck load weight modifier rules to wind risk:
    - >= 55 mph -> No Travel for any load
    - 45–54 mph + >30,000 lb -> No Travel (escalated from Severe)
    - 35–44 mph + >40,000 lb -> Severe (escalated from High)
    """
    reasons = []
    effective_wind_risk = baseline_wind_risk

    if wind_mph >= 55.0:
        effective_wind_risk = RiskLevel.NO_TRAVEL
        reasons.append(f"Extreme wind ({wind_mph:.1f} mph ≥ 55 mph): Mandatory No Travel for all loads.")
    elif 45.0 <= wind_mph <= 54.99 and load_weight_lbs > 30000:
        effective_wind_risk = RiskLevel.NO_TRAVEL
        reasons.append(f"Wind ({wind_mph:.1f} mph) with heavy load ({load_weight_lbs:,.0f} lbs > 30,000 lbs) escalates to No Travel.")
    elif 35.0 <= wind_mph <= 44.99 and load_weight_lbs > 40000:
        effective_wind_risk = RiskLevel.SEVERE
        reasons.append(f"Wind ({wind_mph:.1f} mph) with severe load ({load_weight_lbs:,.0f} lbs > 40,000 lbs) escalates to Severe.")
    else:
        reasons.append(f"Wind ({wind_mph:.1f} mph) classified as {baseline_wind_risk.value}.")

    return effective_wind_risk, reasons


def evaluate_checkpoint_risk(
    wind_mph: float,
    rain_in_hr: float,
    snow_in_hr: float,
    load_weight_lbs: float
) -> Dict[str, Any]:
    """
    Evaluates weather risk at a single checkpoint taking into account:
    - Wind speed + truck load weight
    - Rain intensity
    - Snow intensity
    Returns the composite risk level, numerical score, and detailed diagnostic logs.
    """
    # 1. Base classifications
    base_wind_risk = classify_wind(wind_mph)
    rain_risk = classify_rain(rain_in_hr)
    snow_risk = classify_snow(snow_in_hr)

    # 2. Apply load weight rules to wind
    final_wind_risk, wind_reasons = apply_load_rules(wind_mph, load_weight_lbs, base_wind_risk)

    # 3. Overall checkpoint risk is the worst-case among all 3 hazards
    all_risks = [final_wind_risk, rain_risk, snow_risk]
    overall_risk = max(all_risks, key=lambda r: r.score)

    explanations = []
    explanations.extend(wind_reasons)
    if rain_risk.score >= RiskLevel.MODERATE.score:
        explanations.append(f"Rain rate {rain_in_hr:.2f} in/hr classified as {rain_risk.value}.")
    if snow_risk.score >= RiskLevel.MODERATE.score:
        explanations.append(f"Snow rate {snow_in_hr:.2f} in/hr classified as {snow_risk.value}.")

    return {
        "overall_risk": overall_risk.value,
        "overall_score": overall_risk.score,
        "wind_risk": final_wind_risk.value,
        "rain_risk": rain_risk.value,
        "snow_risk": snow_risk.value,
        "wind_mph": round(wind_mph, 1),
        "rain_in_hr": round(rain_in_hr, 3),
        "snow_in_hr": round(snow_in_hr, 3),
        "load_weight_lbs": round(load_weight_lbs, 0),
        "explanations": explanations,
    }
