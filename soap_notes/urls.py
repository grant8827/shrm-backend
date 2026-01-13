"""
SOAP Notes app URL configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Create a router and register our viewsets with it
router = DefaultRouter()

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
]