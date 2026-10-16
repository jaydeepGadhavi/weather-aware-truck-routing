"""
URL configuration for core backend.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def health_check(request):
    """Simple health check endpoint for monitoring & deployment checks."""
    return JsonResponse({
        "status": "healthy",
        "service": "weather-aware-truck-routing-api",
        "version": "1.0.0"
    })


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check, name='health-check'),
    path('api/', include('routing.urls')),
]
