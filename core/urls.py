"""
Core app URL configuration (Health checks, etc.)
"""
from django.urls import path, include
from django.http import JsonResponse
from rest_framework.routers import DefaultRouter

def health_check(request):
    """Simple health check endpoint for Railway"""
    return JsonResponse({'status': 'ok', 'service': 'theracare-backend'})

# Create a router and register our viewsets with it
router = DefaultRouter()

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
    path('', health_check, name='health_check'),
]