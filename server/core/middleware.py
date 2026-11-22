import logging
import time

from django.db import DatabaseError

logger = logging.getLogger("core.request")


class RequestLoggingMiddleware:
    """
    Logs one structured entry per HTTP request: method, path, status
    code, user id, and latency. Plain Django middleware (not DRF-specific)
    so it covers every request Django handles, including the admin and
    Swagger UI, not just DRF API views.

    Also records API metrics to ApiMetric for the Admin Dashboard.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        request._request_started_at = start
        response = self.get_response(request)
        duration_ms = round((time.monotonic() - start) * 1000, 2)

        user = getattr(request, "user", None)
        user_id = getattr(user, "id", None) if user and user.is_authenticated else None

        logger.info(
            "request",
            extra={
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "user_id": user_id,
            },
        )

        # Record API metric for admin dashboard (skip log viewer polling to avoid recursive noise)
        if (
            request.path.startswith("/api/")
            and request.path != "/api/health/"
            and not request.path.startswith("/api/admin/logs")
        ):
            try:
                from apps.analytics.models import ApiMetric
                metric = ApiMetric.objects.create(
                    path=request.path,
                    method=request.method,
                    status_code=response.status_code,
                    duration_ms=duration_ms,
                    user=user if (user and user.is_authenticated) else None,
                )
                if response.streaming and request.path.startswith("/api/chat/stream/"):
                    request._api_metric_id = metric.pk
            except DatabaseError:
                logger.exception("Could not persist API request metric.")

        return response
