"""
ASGI config for theracare project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator, OriginValidator
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'theracare.settings')

django_asgi_app = get_asgi_application()

from telehealth.routing import websocket_urlpatterns

ws_application = AuthMiddlewareStack(
    URLRouter(
        websocket_urlpatterns
    )
)

ws_origins = list(getattr(settings, 'CORS_ALLOWED_ORIGINS', []))

if not ws_origins:
    ws_origins = [
        'http://localhost:3000',
        'http://127.0.0.1:3000',
        'http://localhost:5173',
        'http://127.0.0.1:5173',
        'http://localhost:5174',
        'http://127.0.0.1:5174',
        'https://shrm-frontend.up.railway.app',
        'https://shrm-backend-production.up.railway.app',
    ]

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": OriginValidator(ws_application, ws_origins) if ws_origins else AllowedHostsOriginValidator(ws_application),
})