"""
Core app URL configuration (Health checks, etc.)
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Create a router and register our viewsets with it
router = DefaultRouter()

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
    # Add health check endpoint later
    # path('check/', views.health_check, name='health_check'),
]