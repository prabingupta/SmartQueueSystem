"""Development settings — local machine, DEBUG on, relaxed security."""
from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS += ["django_extensions"]  # noqa: F405

CORS_ALLOW_ALL_ORIGINS = True

# Use console backend for email in dev so nothing is actually sent
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Relax throttling while developing
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # noqa: F405
    "user": "1000/minute",
    "anon": "200/minute",
    "otp": "20/minute",
}
