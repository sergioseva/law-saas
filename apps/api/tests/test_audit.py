"""Audit log — verify representative auth + CRM events get recorded."""
from __future__ import annotations

import pytest
from django.test import override_settings
from rest_framework.test import APIClient


@override_settings(PUBLIC_BASE_DOMAIN="lawsaas.app")
@pytest.mark.django_db
def test_signup_and_login_produce_audit_entries() -> None:
    from audit.models import AuditLogEntry

    api = APIClient(HTTP_HOST="app.lawsaas.app")
    api.post(
        "/api/auth/signup",
        {
            "email": "founder@example.com",
            "password": "long-enough-12345",
            "firm_name": "Estudio Pérez",
            "subdomain": "perez",
        },
        format="json",
    )

    signup_entry = AuditLogEntry.objects.get(action="auth.signup")
    assert signup_entry.tenant is not None
    assert signup_entry.tenant.subdomain == "perez"
    assert signup_entry.user is not None
    assert signup_entry.user.email == "founder@example.com"
    assert signup_entry.metadata["subdomain"] == "perez"

    api2 = APIClient(HTTP_HOST="perez.lawsaas.app")
    api2.post(
        "/api/auth/login",
        {"email": "founder@example.com", "password": "long-enough-12345"},
        format="json",
    )
    login_entry = AuditLogEntry.objects.get(action="auth.login")
    assert login_entry.user.email == "founder@example.com"
    assert login_entry.metadata["role"] == "admin"


@override_settings(PUBLIC_BASE_DOMAIN="lawsaas.app")
@pytest.mark.django_db
def test_failed_login_records_login_failed(firm_a, admin_membership, admin_user) -> None:
    from audit.models import AuditLogEntry

    api = APIClient(HTTP_HOST="acme.lawsaas.app")
    api.post(
        "/api/auth/login",
        {"email": admin_user.email, "password": "wrong"},
        format="json",
    )
    assert AuditLogEntry.objects.filter(action="auth.login_failed").exists()
    entry = AuditLogEntry.objects.get(action="auth.login_failed")
    assert entry.metadata["email"] == admin_user.email
    assert entry.tenant_id == firm_a.id


@override_settings(PUBLIC_BASE_DOMAIN="lawsaas.app")
@pytest.mark.django_db
def test_client_create_records_audit_entry(
    firm_a, admin_membership, admin_user
) -> None:
    from audit.models import AuditLogEntry

    api = APIClient(HTTP_HOST="acme.lawsaas.app")
    api.force_authenticate(user=admin_user)

    response = api.post(
        "/api/clients",
        {"full_name": "Foo Bar", "case_status": "consulta", "case_type": "Extrajudicial"},
        format="json",
    )
    assert response.status_code == 201

    entry = AuditLogEntry.objects.get(action="client.create")
    assert entry.user == admin_user
    assert entry.tenant_id == firm_a.id
    assert entry.resource_type == "client"
    assert entry.resource_id == response.json()["id"]


@override_settings(PUBLIC_BASE_DOMAIN="lawsaas.app")
@pytest.mark.django_db
def test_audit_failure_does_not_break_request(
    monkeypatch, firm_a, admin_membership, admin_user
) -> None:
    """If the audit write throws, the user-facing request still succeeds."""
    from audit.models import AuditLogEntry

    real_create = AuditLogEntry.objects.create

    def fail(*args, **kwargs):
        raise RuntimeError("audit DB unavailable")

    monkeypatch.setattr(AuditLogEntry.objects, "create", fail)

    api = APIClient(HTTP_HOST="acme.lawsaas.app")
    api.force_authenticate(user=admin_user)
    response = api.post(
        "/api/clients",
        {"full_name": "Resilient", "case_status": "consulta", "case_type": "Extrajudicial"},
        format="json",
    )
    # Audit failure must not turn into 500.
    assert response.status_code == 201

    # Restore so other tests work.
    monkeypatch.setattr(AuditLogEntry.objects, "create", real_create)
