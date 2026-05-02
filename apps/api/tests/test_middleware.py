"""Tenant middleware unit + integration tests."""
from __future__ import annotations

import pytest
from django.test import RequestFactory, override_settings

from tenants.middleware import TenantMiddleware, extract_subdomain


@pytest.mark.parametrize(
    "host,base,expected",
    [
        ("acme.lawsaas.app", "lawsaas.app", "acme"),
        ("acme.lawsaas.app:8000", "lawsaas.app", "acme"),
        ("ACME.LAWSAAS.APP", "lawsaas.app", "acme"),
        ("lawsaas.app", "lawsaas.app", ""),
        ("deep.acme.lawsaas.app", "lawsaas.app", ""),
        ("foreign.com", "lawsaas.app", ""),
        ("acme.lvh.me", "lvh.me", "acme"),
        ("", "lawsaas.app", ""),
        ("api.lawsaas.app", "lawsaas.app", "api"),
    ],
)
def test_extract_subdomain(host: str, base: str, expected: str) -> None:
    assert extract_subdomain(host, base) == expected


@override_settings(PUBLIC_BASE_DOMAIN="lawsaas.app")
def test_middleware_public_subdomain_no_firm(rf: RequestFactory) -> None:
    request = rf.get("/", HTTP_HOST="app.lawsaas.app")
    middleware = TenantMiddleware(lambda req: None)  # type: ignore[arg-type,return-value]
    middleware(request)
    assert request.firm is None  # type: ignore[attr-defined]
    assert request.firm_subdomain == "app"  # type: ignore[attr-defined]


@override_settings(PUBLIC_BASE_DOMAIN="lawsaas.app")
def test_middleware_resolves_firm(db, firm_a, rf: RequestFactory) -> None:
    request = rf.get("/", HTTP_HOST="acme.lawsaas.app")
    middleware = TenantMiddleware(lambda req: None)  # type: ignore[arg-type,return-value]
    middleware(request)
    assert request.firm is not None  # type: ignore[attr-defined]
    assert request.firm.id == firm_a.id  # type: ignore[attr-defined]


@override_settings(PUBLIC_BASE_DOMAIN="lawsaas.app")
def test_middleware_unknown_subdomain_yields_no_firm(db, rf: RequestFactory) -> None:
    request = rf.get("/", HTTP_HOST="ghost.lawsaas.app")
    middleware = TenantMiddleware(lambda req: None)  # type: ignore[arg-type,return-value]
    middleware(request)
    assert request.firm is None  # type: ignore[attr-defined]


@pytest.fixture
def rf() -> RequestFactory:
    return RequestFactory()
