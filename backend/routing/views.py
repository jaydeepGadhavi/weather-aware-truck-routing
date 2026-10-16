"""
API Views for Route Analysis and Freight Hub Presets.
Adheres to Clean Architecture: Views act as thin HTTP controllers,
delegating business orchestration to the domain service layer.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import logging

from .serializers import RouteAnalysisRequestSerializer
from .services.pipeline import execute_routing_pipeline

logger = logging.getLogger(__name__)


class AnalyzeRoutesView(APIView):
    """
    POST /api/routes/analyze/
    Accepts origin, destination, departure time, truck weight, and sampling interval.
    Delegates processing to the pipeline orchestrator service.
    """

    def post(self, request):
        serializer = RouteAnalysisRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "Validation failed", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = execute_routing_pipeline(serializer.validated_data)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(f"Routing pipeline execution failed: {e}")
            return Response(
                {
                    "error": "Failed to analyze routes due to an unexpected error.",
                    "details": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FreightHubsView(APIView):
    """
    GET /api/hubs/
    Returns quick-select presets for freight corridors.
    """
    def get(self, request):
        hubs = [
            {"id": "chi_dal", "name": "Chicago, IL → Dallas, TX", "origin": "Chicago, IL", "destination": "Dallas, TX"},
            {"id": "atl_den", "name": "Atlanta, GA → Denver, CO", "origin": "Atlanta, GA", "destination": "Denver, CO"},
            {"id": "sea_la", "name": "Seattle, WA → Los Angeles, CA", "origin": "Seattle, WA", "destination": "Los Angeles, CA"},
            {"id": "kc_mem", "name": "Kansas City, MO → Memphis, TN", "origin": "Kansas City, MO", "destination": "Memphis, TN"},
        ]
        return Response(hubs)
