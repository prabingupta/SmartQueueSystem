"""
Cross-cutting middleware.

RequestLoggingMiddleware: logs method/path/status/duration for every request.
AuditLogMiddleware: records who did what, for state-changing requests, into
the AuditLog model (implemented in Phase: Backend Development). For now this
is a safe no-op scaffold so settings.py can already reference it.
"""
import logging
import time

logger = logging.getLogger("apps")


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = (time.monotonic() - start) * 1000
        logger.info(
            "%s %s -> %s (%.1fms)",
            request.method,
            request.path,
            response.status_code,
            duration_ms,
        )
        return response


class AuditLogMiddleware:
    """
    Placeholder that will write to apps.core.models_audit.AuditLog once the
    audit trail model is built in the Backend Development phase. Left as an
    explicit no-op (not deleted) so it's clear this is intentional, not
    forgotten.
    """

    WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # TODO(Backend Development phase): persist AuditLog entries for
        # authenticated users on write requests that succeeded.
        return response
