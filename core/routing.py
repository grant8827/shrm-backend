# backend/core/routing.py
"""
WebSocket routing configuration for TheraCare.
"""

from django.urls import path
from telehealth.consumers import VideoSessionConsumer

websocket_urlpatterns = [
    path('ws/video/<str:room_id>/', VideoSessionConsumer.as_asgi()),
]
