"""Global values available in every template (site name, branding, etc.)."""
from django.conf import settings


def site_settings(request):
    return {
        "SITE_NAME": "Smart Queue Management System",
        "SITE_TAGLINE": "AI-Powered Digital Queue & Crowd Monitoring Platform",
        "GOVERNMENT_NAME": "Government of Nepal",
        "DEBUG": settings.DEBUG,
    }
