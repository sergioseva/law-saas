"""Rate limiter — verify the configured caps on signup and login."""
from __future__ import annotations

import pytest
from django.core.cache import cache
from django.test import override_settings
from rest_framework.test import APIClient


@pytest.fixture
def _enable_ratelimit(settings):
    settings.RATELIMIT_ENABLE = True
    cache.clear()
    yield
    cache.clear()


@override_settings(PUBLIC_BASE_DOMAIN="lawsaas.app")
@pytest.mark.django_db
def test_signup_rate_limited_after_3_per_hour(_enable_ratelimit) -> None:
    api = APIClient(HTTP_HOST="app.lawsaas.app", REMOTE_ADDR="203.0.113.10")

    # First 3 are allowed (whether they succeed or fail validation is irrelevant).
    for i in range(3):
        api.post(
            "/api/auth/signup",
            {
                "email": f"user{i}@example.com",
                "password": "long-enough-12345",
                "firm_name": f"Firm {i}",
                "subdomain": f"firm{i}",
            },
            format="json",
        )

    # 4th from same IP must be 429.
    response = api.post(
        "/api/auth/signup",
        {
            "email": "user4@example.com",
            "password": "long-enough-12345",
            "firm_name": "Firm 4",
            "subdomain": "firm4",
        },
        format="json",
    )
    assert response.status_code == 429
    assert "Demasiadas" in response.json()["detail"]


@override_settings(PUBLIC_BASE_DOMAIN="lawsaas.app")
@pytest.mark.django_db
def test_login_rate_limited_after_5_per_5min(
    _enable_ratelimit, admin_membership, admin_user, firm_a
) -> None:
    api = APIClient(HTTP_HOST="acme.lawsaas.app", REMOTE_ADDR="203.0.113.20")

    for _ in range(5):
        api.post(
            "/api/auth/login",
            {"email": admin_user.email, "password": "wrong-pass"},
            format="json",
        )

    response = api.post(
        "/api/auth/login",
        {"email": admin_user.email, "password": "adminpass-12345"},
        format="json",
    )
    assert response.status_code == 429


@override_settings(PUBLIC_BASE_DOMAIN="lawsaas.app")
@pytest.mark.django_db
def test_rate_limit_keyed_per_ip(_enable_ratelimit) -> None:
    """A different IP shouldn't be blocked just because another one was."""
    api = APIClient(HTTP_HOST="app.lawsaas.app", REMOTE_ADDR="203.0.113.30")
    for i in range(3):
        api.post(
            "/api/auth/signup",
            {
                "email": f"a{i}@example.com",
                "password": "long-enough-12345",
                "firm_name": f"Z{i}",
                "subdomain": f"z{i}",
            },
            format="json",
        )

    other = APIClient(HTTP_HOST="app.lawsaas.app", REMOTE_ADDR="203.0.113.40")
    response = other.post(
        "/api/auth/signup",
        {
            "email": "fresh@example.com",
            "password": "long-enough-12345",
            "firm_name": "Fresh",
            "subdomain": "fresh",
        },
        format="json",
    )
    # Either 201 (succeeded) or 400 (validation) — anything but 429.
    assert response.status_code != 429
