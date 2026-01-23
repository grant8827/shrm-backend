"""
Appointments app URL configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AppointmentViewSet, AppointmentTypeViewSet

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'', AppointmentViewSet, basename='appointment')  # Empty prefix since 'appointments/' is in main urls
router.register(r'types', AppointmentTypeViewSet, basename='appointment-type')

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
]