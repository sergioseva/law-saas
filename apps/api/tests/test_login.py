"""Login + me + logout flow."""
from __future__ import annotations

import pytest
from django.test import override_settings
from rest_framework.test import APIClient


@override_settings(PUBLIC_BASE_DOMAIN="lawsaas.app")
@pytest.mark.django_db
def test_login_succeeds_with_membership(admin_membership, admin_user) -> None:
    client = APIClient(HTTP_HOST="acme.lawsaas.app")
    response = client.post(
        "/api/auth/login",
        {"email": admin_user.email, "password": "adminpass-12345"},
        format="json",
    )
    assert response.status_code == 200, response.json()
    body = response.json()
    assert body["role"] == "admin"
    assert body["firm"]["subdomain"] == "acme"


@override_settings(PUBLIC_BASE_DOMAIN="lawsaas.app")
@pytest.mark.django_db
def test_login_rejects_bad_password(admin_membership, admin_user) -> None:
    client = APIClient(HTTP_HOST="acme.lawsaas.app")
    response = client.post(
        "/api/auth/login",
        {"email": admin_user.email, "password": "wrong-password"},
        format="json",
    )
    assert response.status_code == 401


@override_settings(PUBLIC_BASE_DOMAIN="lawsaas.app")
@pytest.mark.django_db
def test_login_rejects_user_without_membership_in_subdomain(
    admin_membership, admin_user, firm_b
) -> None:
    """Admin of firm_a tries to log in via firm_b's subdomain — must 403."""
    client = APIClient(HTTP_HOST="beta.lawsaas.app")
    response = client.post(
        "/api/auth/login",
        {"email": admin_user.email, "password": "adminpass-12345"},
        format="json",
    )
    assert response.status_code == 403


@override_settings(PUBLIC_BASE_DOMAIN="lawsaas.app")
@pytest.mark.django_db
def test_login_requires_firm_subdomain() -> None:
    """Login on the marketing host (no firm) must fail with 403 (HasFirm)."""
    client = APIClient(HTTP_HOST="app.lawsaas.app")
    response = client.post(
        "/api/auth/login",
        {"email": "anyone@example.com", "password": "any"},
        format="json",
    )
    assert response.status_code == 403


@override_settings(PUBLIC_BASE_DOMAIN="lawsaas.app")
@pytest.mark.django_db
def test_me_after_login(admin_membership, admin_user) -> None:
    client = APIClient(HTTP_HOST="acme.lawsaas.app")
    client.post(
        "/api/auth/login",
        {"email": admin_user.email, "password": "adminpass-12345"},
        format="json",
    )
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == admin_user.email
    assert body["role"] == "admin"
    assert body["firm"]["subdomain"] == "acme"


@override_settings(PUBLIC_BASE_DOMAIN="lawsaas.app")
@pytest.mark.django_db
def test_logout_clears_session(admin_membership, admin_user) -> None:
    client = APIClient(HTTP_HOST="acme.lawsaas.app")
    client.post(
        "/api/auth/login",
        {"email": admin_user.email, "password": "adminpass-12345"},
        format="json",
    )
    response = client.post("/api/auth/logout")
    assert response.status_code == 204

    me = client.get("/api/auth/me")
    assert me.status_code in (401, 403)
