from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MessageViewSet, MessageThreadViewSet

router = DefaultRouter()
router.register(r'threads', MessageThreadViewSet, basename='messagethread')
router.register(r'messages', MessageViewSet, basename='message')

urlpatterns = [
    path('', include(router.urls)),
]