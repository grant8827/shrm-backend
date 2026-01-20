# backend/core/routing.py
"""
WebSocket routing configuration for TheraCare.
"""

from django.urls import re_path
from telehealth.consumers import VideoCallConsumer

websocket_urlpatterns = [
    re_path(r'ws/video/(?P<session_id>[0-9a-fA-F\-]+)/$', VideoCallConsumer.as_asgi()),
]
