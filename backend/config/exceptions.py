import logging
from django.conf import settings
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger("config.exceptions")


def custom_exception_handler(exc, context):
    """
    Custom exception handler for Django REST Framework.
    Preserves all standard DRF responses (400, 401, 403, 404, 429, etc.)
    and intercepts unhandled server errors (500) to ensure generic, safe responses
    without leaking stack traces, SQL, file paths, or secrets to API clients.
    """
    response = drf_exception_handler(exc, context)

    if response is not None:
        return response

    # Unhandled 500 exception
    request = context.get("request") if context else None
    view = context.get("view") if context else None
    view_name = view.__class__.__name__ if view else "UnknownView"
    path = getattr(request, "path", "unknown") if request else "unknown"
    method = getattr(request, "method", "unknown") if request else "unknown"

    logger.error(
        "Unexpected server error in %s (%s %s): %s",
        view_name,
        method,
        path,
        str(exc),
        exc_info=exc,
    )

    return Response(
        {"detail": "An unexpected error occurred."},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def server_error_500(request):
    """
    Fallback Django HTTP 500 handler for non-DRF views or middleware exceptions.
    """
    logger.error(
        "Unexpected server error: %s %s",
        getattr(request, "method", ""),
        getattr(request, "path", ""),
        exc_info=True,
    )
    return JsonResponse(
        {"detail": "An unexpected error occurred."},
        status=500,
    )
