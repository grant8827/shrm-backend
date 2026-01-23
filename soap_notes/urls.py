"""
SOAP Notes app URL configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SOAPNoteViewSet

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'soap-notes', SOAPNoteViewSet, basename='soap-note')

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
]