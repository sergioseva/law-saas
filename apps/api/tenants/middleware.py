"""
Tenant resolution middleware — Phase 1 will flesh this out.

Reads the request Host header, extracts the subdomain, looks up the matching
Firm, attaches it to `request.firm`, and sets the Postgres session var
`app.tenant_id` so RLS policies on every domain table can filter by it.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import connection
from django.http import HttpRequest, HttpResponse

if TYPE_CHECKING:
    from .models import Firm


PUBLIC_SUBDOMAINS = {"app", "www", ""}


def extract_subdomain(host: str) -> str:
    """`acme.lawsaas.app:8000` -> `acme`. Returns "" if no firm subdomain."""
    host = host.split(":")[0]
    base = settings.PUBLIC_BASE_DOMAIN
    if not host.endswith(base):
        return ""
    prefix = host[: -len(base)].rstrip(".")
    # Accept only a single label
    if "." in prefix:
        return ""
    return prefix


class TenantMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request.firm = None  # type: ignore[attr-defined]
        subdomain = extract_subdomain(request.get_host())

        if subdomain and subdomain not in PUBLIC_SUBDOMAINS and subdomain not in settings.RESERVED_SUBDOMAINS:
            firm = self._resolve_firm(subdomain)
            if firm is not None:
                request.firm = firm  # type: ignore[attr-defined]
                with connection.cursor() as cursor:
                    cursor.execute("SELECT set_config('app.tenant_id', %s, true)", [str(firm.id)])

        return self.get_response(request)

    def _resolve_firm(self, subdomain: str) -> "Firm | None":
        from .models import Firm

        try:
            return Firm.objects.get(subdomain=subdomain)
        except Firm.DoesNotExist:
            return None
