"""
Core app URL configuration (Health checks, etc.)
"""
from django.urls import path, include
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.routers import DefaultRouter

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Simple health check endpoint for Railway - no authentication required"""
    return Response({'status': 'ok', 'service': 'theracare-backend'})

# Create a router and register our viewsets with it
router = DefaultRouter()

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
    path('', health_check, name='health_check'),
]