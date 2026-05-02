"""Signup endpoint tests."""
from __future__ import annotations

import pytest
from django.test import override_settings
from rest_framework.test import APIClient

from tenants.models import Firm, Membership, User


@override_settings(PUBLIC_BASE_DOMAIN="lawsaas.app")
@pytest.mark.django_db
def test_signup_creates_user_firm_and_admin_membership() -> None:
    client = APIClient(HTTP_HOST="app.lawsaas.app")
    response = client.post(
        "/api/auth/signup",
        {
            "email": "founder@example.com",
            "password": "long-enough-12345",
            "firm_name": "Estudio Pérez",
            "subdomain": "perez",
        },
        format="json",
    )
    assert response.status_code == 201, response.json()
    body = response.json()
    assert body["firm"]["subdomain"] == "perez"
    assert "perez." in body["redirect_url"]

    user = User.objects.get(email="founder@example.com")
    firm = Firm.objects.get(subdomain="perez")
    membership = Membership.objects.get(user=user, firm=firm)
    assert membership.role == Membership.Role.ADMIN
    assert firm.wrapped_dek  # DEK was generated


@pytest.mark.django_db
def test_signup_rejects_reserved_subdomain() -> None:
    client = APIClient(HTTP_HOST="app.lawsaas.app")
    response = client.post(
        "/api/auth/signup",
        {
            "email": "x@example.com",
            "password": "long-enough-12345",
            "firm_name": "Whatever",
            "subdomain": "api",
        },
        format="json",
    )
    assert response.status_code == 400
    assert "subdomain" in response.json()


@pytest.mark.django_db
def test_signup_rejects_bad_subdomain_format() -> None:
    client = APIClient(HTTP_HOST="app.lawsaas.app")
    response = client.post(
        "/api/auth/signup",
        {
            "email": "x@example.com",
            "password": "long-enough-12345",
            "firm_name": "Whatever",
            "subdomain": "-bad-",
        },
        format="json",
    )
    assert response.status_code == 400
    assert "subdomain" in response.json()


@pytest.mark.django_db
def test_signup_rejects_duplicate_subdomain(firm_a) -> None:
    client = APIClient(HTTP_HOST="app.lawsaas.app")
    response = client.post(
        "/api/auth/signup",
        {
            "email": "new@example.com",
            "password": "long-enough-12345",
            "firm_name": "Acme 2",
            "subdomain": firm_a.subdomain,
        },
        format="json",
    )
    assert response.status_code == 400
    assert "subdomain" in response.json()


@pytest.mark.django_db
def test_signup_rejects_weak_password() -> None:
    client = APIClient(HTTP_HOST="app.lawsaas.app")
    response = client.post(
        "/api/auth/signup",
        {
            "email": "x@example.com",
            "password": "short",
            "firm_name": "Whatever",
            "subdomain": "freshfirm",
        },
        format="json",
    )
    assert response.status_code == 400
    assert "password" in response.json()


@pytest.mark.django_db
def test_signup_atomic_rollback_on_collision(firm_a) -> None:
    """If user creation succeeds but firm creation fails, no user should remain."""
    client = APIClient(HTTP_HOST="app.lawsaas.app")
    pre = User.objects.count()
    response = client.post(
        "/api/auth/signup",
        {
            "email": "race@example.com",
            "password": "long-enough-12345",
            "firm_name": "Race",
            "subdomain": firm_a.subdomain,  # collides
        },
        format="json",
    )
    assert response.status_code == 400
    assert User.objects.count() == pre  # transaction rolled back
