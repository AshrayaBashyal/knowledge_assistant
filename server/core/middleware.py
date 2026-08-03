import logging
import time

logger = logging.getLogger("core.request")


class RequestLoggingMiddleware:
    """
    Logs one structured entry per HTTP request: method, path, status
    code, user id, and latency. Plain Django middleware (not DRF-specific)
    so it covers every request Django handles, including the admin and
    Swagger UI, not just DRF API views.

    warning: for streaming responses (chat's SSEendpoint),
    `duration_ms` here only measures how long it took to
    *build* the StreamingHttpResponse object, not how long the actual
    token stream took to send - Django doesn't iterate a streaming
    response's generator until after middleware has already returned.
    Chat-specific latency is measured separately, inside
    chat/views.py's _stream_chat_response, closer to where the real
    work happens.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
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
        return response