"""
ASGI config for the Smart Queue Management System.

Kept ASGI-ready (not just WSGI) because the live queue dashboard and
camera-feed alerts will benefit from WebSocket support (Django Channels)
in a later phase.
"""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

application = get_asgi_application()
