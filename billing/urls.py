"""
Billing app URL configuration
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BillViewSet, PaymentViewSet

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r"bills", BillViewSet, basename="bill")
router.register(r"payments", PaymentViewSet, basename="payment")

# URL patterns
urlpatterns = [
    path("", include(router.urls)),
]
