"""
Audit app URL configuration
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r"logs", views.AuditLogViewSet, basename="auditlog")

# URL patterns
urlpatterns = [
    path("logs/batch/", views.create_audit_log_batch, name="audit_log_batch"),
    path("", include(router.urls)),
]
