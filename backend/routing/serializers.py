"""
Serializers for Route Analysis API input validation.
"""
from rest_framework import serializers
from datetime import datetime, timezone


class RouteAnalysisRequestSerializer(serializers.Serializer):
    origin = serializers.CharField(
        max_length=255,
        required=True,
        help_text="Starting city or address (e.g., 'Chicago, IL')"
    )
    destination = serializers.CharField(
        max_length=255,
        required=True,
        help_text="Destination city or address (e.g., 'Dallas, TX')"
    )
    departure_time = serializers.DateTimeField(
        required=False,
        default=lambda: datetime.now(timezone.utc),
        help_text="Departure timestamp in ISO 8601 format"
    )
    load_weight_lbs = serializers.FloatField(
        required=False,
        default=35000.0,
        min_value=0.0,
        max_value=120000.0,
        help_text="Truck cargo weight in pounds (lbs)"
    )
    sample_interval_miles = serializers.ChoiceField(
        choices=[10, 25, 50],
        default=25,
        required=False,
        help_text="Sampling checkpoint interval in miles (10, 25, or 50)"
    )
