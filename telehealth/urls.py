"""
Telehealth app URL configuration
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TelehealthSessionViewSet

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r"sessions", TelehealthSessionViewSet, basename="telehealth-session")

# URL patterns
urlpatterns = [
    path(
        "sessions/transcripts/",
        TelehealthSessionViewSet.as_view({"get": "transcripts"}),
        name="telehealth-transcripts",
    ),
    path("", include(router.urls)),
]
