import logging

from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger("core.exceptions")


def custom_exception_handler(exc, context):
    """
    Wraps DRF's default exception handler to:
 
    1. Ensure every error response uses {"detail": ...} consistently,
       instead of DRF's default {"field": ["message"]} shape for
       validation errors. The React frontend only needs to handle one
       error shape, not two.
 
    2. Log every unhandled exception (5xx) with structured context
       (view name, request method/path), so production errors are
       findable in the logs alongside the structured
       logging.
    """

    response = drf_exception_handler(exc, context)

    if response is None:
        # DRF didn't handle this - it'll become a 500.
        # Log it with enough context to find in structured logs, then let Django's own 500 handling take over (returns a clean error page or JSON depending on DEBUG).
        view = context.get("view")
        request = context.get("request")
        logger.exception(
            "unhandled_exception",
            extra={
                "view": type(view).__name__ if view else None,
                "method": request.method if request else None,
                "path": request.path if request else None,
            },
        )
        return None

    # Reshape validation errors: DRF returns {"field_name": ["msg"]} for serializer errors.
    # Normalize to {"detail": {field: [msgs]}} so the client always finds the error under the same key.
    if isinstance(exc, ValidationError):
        response.data = {"detail": exc.detail}
    elif "detail" not in response.data:
        # Some DRF exceptions (e.g. NotAuthenticated) already use "detail"; others set a different top-level key. Make sure "detail" is always present.
        response.data = {"detail": response.data}
 
    return response