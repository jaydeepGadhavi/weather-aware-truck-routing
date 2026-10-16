"""
Routing app URL configuration.
"""
from django.urls import path
from .views import AnalyzeRoutesView, FreightHubsView

urlpatterns = [
    path('routes/analyze/', AnalyzeRoutesView.as_view(), name='analyze-routes'),
    path('hubs/', FreightHubsView.as_view(), name='freight-hubs'),
]
