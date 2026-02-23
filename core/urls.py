"""
Core app URL configuration (Health checks, etc.)
"""

from django.urls import path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """Simple health check endpoint for Railway - no authentication required"""
    return Response({"status": "ok", "service": "theracare-backend"})


# URL patterns
urlpatterns = [
    path("", health_check, name="health_check"),
]
