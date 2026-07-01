"""
WSGI config for the Smart Queue Management System.

Exposes the WSGI callable as a module-level variable named ``application``.
Used by Gunicorn in production.
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

application = get_wsgi_application()
