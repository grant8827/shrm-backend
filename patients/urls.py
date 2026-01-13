"""
Patients app URL configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PatientViewSet

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'', PatientViewSet, basename='patient')

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
]