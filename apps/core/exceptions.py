"""
Custom DRF exception handler.

Wraps DRF's default handler so every API error returns a consistent shape:

    {
        "success": false,
        "error": {
            "code": "validation_error",
            "message": "...",
            "details": {...}
        }
    }

instead of DRF's default inconsistent shapes (list for some errors, dict
for others).
"""
import logging

from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger("apps")


def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)

    if response is None:
        # Unhandled exception (bug, DB error, etc.) — log it, don't leak
        # internals to the client.
        logger.exception("Unhandled exception in API view", exc_info=exc)
        return None

    error_code = getattr(exc, "default_code", exc.__class__.__name__.lower())
    response.data = {
        "success": False,
        "error": {
            "code": error_code,
            "message": _extract_message(response.data),
            "details": response.data,
        },
    }
    return response


def _extract_message(data):
    if isinstance(data, dict):
        for key in ("detail", "message", "non_field_errors"):
            if key in data:
                value = data[key]
                return value[0] if isinstance(value, list) else value
        # Fall back to first field's first error
        for value in data.values():
            return value[0] if isinstance(value, list) else value
    if isinstance(data, list) and data:
        return data[0]
    return "An error occurred."
