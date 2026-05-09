"""DRF exception handler — converts django-ratelimit's exception into a 429."""
from __future__ import annotations

from django_ratelimit.exceptions import Ratelimited
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_default_handler


def custom_exception_handler(exc, context):
    if isinstance(exc, Ratelimited):
        return Response(
            {"detail": "Demasiadas solicitudes. Intentá de nuevo en unos minutos."},
            status=429,
        )
    return drf_default_handler(exc, context)
