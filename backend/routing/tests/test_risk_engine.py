"""
Unit tests for the Risk Engine and Recommendation Logic.
Validates all requirements from the Spotter Assessment.
"""
from django.test import TestCase
from routing.services.risk_engine import (
    RiskLevel,
    classify_wind,
    classify_rain,
    classify_snow,
    apply_load_rules,
    evaluate_checkpoint_risk,
)
from routing.services.recommendation_engine import rank_routes


class TestRiskEngine(TestCase):

    def test_wind_classification(self):
        self.assertEqual(classify_wind(15.0), RiskLevel.LOW)
        self.assertEqual(classify_wind(24.9), RiskLevel.LOW)
        self.assertEqual(classify_wind(25.0), RiskLevel.MODERATE)
        self.assertEqual(classify_wind(34.0), RiskLevel.MODERATE)
        self.assertEqual(classify_wind(35.0), RiskLevel.HIGH)
        self.assertEqual(classify_wind(44.0), RiskLevel.HIGH)
        self.assertEqual(classify_wind(45.0), RiskLevel.SEVERE)
        self.assertEqual(classify_wind(54.0), RiskLevel.SEVERE)
        self.assertEqual(classify_wind(55.0), RiskLevel.NO_TRAVEL)
        self.assertEqual(classify_wind(70.0), RiskLevel.NO_TRAVEL)

    def test_rain_classification(self):
        self.assertEqual(classify_rain(0.05), RiskLevel.LOW)
        self.assertEqual(classify_rain(0.10), RiskLevel.MODERATE)
        self.assertEqual(classify_rain(0.24), RiskLevel.MODERATE)
        self.assertEqual(classify_rain(0.25), RiskLevel.HIGH)
        self.assertEqual(classify_rain(0.49), RiskLevel.HIGH)
        self.assertEqual(classify_rain(0.50), RiskLevel.SEVERE)
        self.assertEqual(classify_rain(1.00), RiskLevel.SEVERE)
        self.assertEqual(classify_rain(1.05), RiskLevel.NO_TRAVEL)

    def test_snow_classification(self):
        self.assertEqual(classify_snow(0.2), RiskLevel.LOW)
        self.assertEqual(classify_snow(0.5), RiskLevel.MODERATE)
        self.assertEqual(classify_snow(0.9), RiskLevel.MODERATE)
        self.assertEqual(classify_snow(1.0), RiskLevel.HIGH)
        self.assertEqual(classify_snow(1.9), RiskLevel.HIGH)
        self.assertEqual(classify_snow(2.0), RiskLevel.SEVERE)
        self.assertEqual(classify_snow(3.0), RiskLevel.SEVERE)
        self.assertEqual(classify_snow(3.5), RiskLevel.NO_TRAVEL)

    def test_load_rules_escalation(self):
        # 1. >= 55 mph -> No Travel for any load
        res, _ = apply_load_rules(wind_mph=56.0, load_weight_lbs=10000, baseline_wind_risk=RiskLevel.NO_TRAVEL)
        self.assertEqual(res, RiskLevel.NO_TRAVEL)

        # 2. 45–54 mph + >30,000 lb -> No Travel (escalated from Severe)
        # Weight <= 30k stays Severe
        res, _ = apply_load_rules(wind_mph=48.0, load_weight_lbs=25000, baseline_wind_risk=RiskLevel.SEVERE)
        self.assertEqual(res, RiskLevel.SEVERE)
        # Weight > 30k escalates to No Travel
        res, _ = apply_load_rules(wind_mph=48.0, load_weight_lbs=35000, baseline_wind_risk=RiskLevel.SEVERE)
        self.assertEqual(res, RiskLevel.NO_TRAVEL)

        # 3. 35–44 mph + >40,000 lb -> Severe (escalated from High)
        # Weight <= 40k stays High
        res, _ = apply_load_rules(wind_mph=40.0, load_weight_lbs=35000, baseline_wind_risk=RiskLevel.HIGH)
        self.assertEqual(res, RiskLevel.HIGH)
        # Weight > 40k escalates to Severe
        res, _ = apply_load_rules(wind_mph=40.0, load_weight_lbs=45000, baseline_wind_risk=RiskLevel.HIGH)
        self.assertEqual(res, RiskLevel.SEVERE)

    def test_evaluate_checkpoint_composite(self):
        # Case where snow causes severe risk even if wind is low
        eval_result = evaluate_checkpoint_risk(
            wind_mph=15.0,
            rain_in_hr=0.0,
            snow_in_hr=2.5,
            load_weight_lbs=20000
        )
        self.assertEqual(eval_result["overall_risk"], RiskLevel.SEVERE.value)

        # Case where wind with heavy load triggers No Travel
        eval_result2 = evaluate_checkpoint_risk(
            wind_mph=48.0,
            rain_in_hr=0.05,
            snow_in_hr=0.0,
            load_weight_lbs=38000
        )
        self.assertEqual(eval_result2["overall_risk"], RiskLevel.NO_TRAVEL.value)


class TestRecommendationEngine(TestCase):

    def test_ranking_priority(self):
        # Route 1: Has 10 severe miles, travel time 4 hours
        r1 = {
            "name": "Route 1",
            "duration_seconds": 14400,
            "metrics": {
                "no_travel_miles": 0,
                "severe_miles": 10.0,
                "high_miles": 0.0,
                "average_risk_score": 2.5
            }
        }
        # Route 2: Has 0 severe miles, 20 high miles, travel time 5 hours
        r2 = {
            "name": "Route 2",
            "duration_seconds": 18000,
            "metrics": {
                "no_travel_miles": 0,
                "severe_miles": 0.0,
                "high_miles": 20.0,
                "average_risk_score": 2.2
            }
        }
        # Route 3: Has 0 severe miles, 5 high miles, travel time 5.5 hours
        r3 = {
            "name": "Route 3",
            "duration_seconds": 19800,
            "metrics": {
                "no_travel_miles": 0,
                "severe_miles": 0.0,
                "high_miles": 5.0,
                "average_risk_score": 1.8
            }
        }

        # Priority 1: Fewest Severe miles -> r2 and r3 beat r1 (0 severe < 10 severe)
        # Priority 2: Fewest High miles -> r3 beats r2 (5 high < 20 high)
        ranked = rank_routes([r1, r2, r3])
        self.assertEqual(ranked[0]["name"], "Route 3")
        self.assertTrue(ranked[0]["is_recommended"])
        self.assertEqual(ranked[1]["name"], "Route 2")
        self.assertEqual(ranked[2]["name"], "Route 1")


class TestPipelineOrchestration(TestCase):

    def test_pipeline_structure(self):
        from routing.services.pipeline import execute_routing_pipeline
        from datetime import datetime, timezone

        payload = {
            "origin": "Chicago, IL",
            "destination": "Dallas, TX",
            "departure_time": datetime.now(timezone.utc),
            "load_weight_lbs": 35000.0,
            "sample_interval_miles": 50.0
        }
        result = execute_routing_pipeline(payload)
        self.assertIn("routes", result)
        self.assertEqual(len(result["routes"]), 3)
        self.assertTrue(result["routes"][0]["is_recommended"])
        self.assertIn("corridor_heatmap", result)
        self.assertIn("debug_meta", result)
        self.assertEqual(result["debug_meta"]["status"], "success")

