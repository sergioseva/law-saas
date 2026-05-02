"""
Tenant resolution middleware.

Reads the request Host header, extracts the subdomain, looks up the matching
Firm, attaches it to `request.firm`, and sets the Postgres session var
`app.tenant_id` so RLS policies on every domain table can filter by it.

`request.firm` is `None` for public hosts (app., api., www., bare domain).
Views/permissions that require a firm context check for None and return 404.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import connection
from django.http import HttpRequest, HttpResponse

if TYPE_CHECKING:
    from .models import Firm

# Subdomains that map to non-tenant hosts. They never resolve to a Firm.
PUBLIC_SUBDOMAINS = {"", "app", "www", "api"}


def extract_subdomain(host: str, base_domain: str) -> str:
    """
    Pull the leading label out of `host` relative to `base_domain`.

    Examples (base_domain="lawsaas.app"):
        "acme.lawsaas.app"        -> "acme"
        "acme.lawsaas.app:8000"   -> "acme"
        "lawsaas.app"             -> ""
        "deep.acme.lawsaas.app"   -> ""    (multi-label prefix is invalid)
        "other.com"               -> ""    (foreign host)
    """
    host = host.split(":", 1)[0].lower().strip(".")
    base = base_domain.lower().strip(".")
    if host == base:
        return ""
    suffix = "." + base
    if not host.endswith(suffix):
        return ""
    prefix = host[: -len(suffix)]
    if "." in prefix or not prefix:
        return ""
    return prefix


class TenantMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request.firm = None  # type: ignore[attr-defined]
        request.firm_subdomain = ""  # type: ignore[attr-defined]

        subdomain = extract_subdomain(request.get_host(), settings.PUBLIC_BASE_DOMAIN)
        request.firm_subdomain = subdomain  # type: ignore[attr-defined]

        if subdomain and subdomain not in PUBLIC_SUBDOMAINS and subdomain not in settings.RESERVED_SUBDOMAINS:
            firm = self._resolve_firm(subdomain)
            if firm is not None:
                request.firm = firm  # type: ignore[attr-defined]
                # set_config(name, value, is_local=true) — scoped to the current
                # transaction; safe with Django's per-request connection lifecycle.
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT set_config('app.tenant_id', %s, true)",
                        [str(firm.id)],
                    )

        return self.get_response(request)

    def _resolve_firm(self, subdomain: str) -> "Firm | None":
        from .models import Firm

        try:
            return Firm.objects.get(subdomain=subdomain)
        except Firm.DoesNotExist:
            return None
