"""
End-to-end API tests for CRM endpoints — auth + tenant + RBAC + CRUD.

We use force_authenticate (not force_login) so the session/cookie scoping
doesn't fight with subdomain testing. Each test sets HTTP_HOST so the
TenantMiddleware resolves request.firm.
"""
from __future__ import annotations

import pytest
from django.test import override_settings
from rest_framework.test import APIClient

from crm.models import Action, Client
from crm.services import create_action, create_client


# Helper to build authenticated clients --------------------------------------


def _client_for(*, host: str, user) -> APIClient:
    c = APIClient(HTTP_HOST=host)
    c.force_authenticate(user=user)
    return c


@pytest.fixture
def acme_data() -> dict:
    return {
        "full_name": "María José Pérez",
        "dni_cuil": "30.123.456-7",
        "phone": "(011) 4555-1234",
        "email": "mj@example.com",
        "city": "CABA",
        "case_status": "consulta",
        "case_type": "Extrajudicial",
        "case_label": "",
    }


# ---------------------------------------------------------------------------
# Client CRUD
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_BASE_DOMAIN="lawsaas.app")
@pytest.mark.django_db
def test_client_create_and_retrieve(admin_membership, admin_user, firm_a, acme_data) -> None:
    api = _client_for(host="acme.lawsaas.app", user=admin_user)
    response = api.post("/api/clients", acme_data, format="json")
    assert response.status_code == 201, response.json()
    body = response.json()
    assert body["full_name"] == "María José Pérez"
    cid = body["id"]

    detail = api.get(f"/api/clients/{cid}")
    assert detail.status_code == 200
    assert detail.json()["dni_cuil"] == "30.123.456-7"


@override_settings(PUBLIC_BASE_DOMAIN="lawsaas.app")
@pytest.mark.django_db
def test_client_list_returns_summary_no_decryption_cost(
    admin_membership, admin_user, firm_a, acme_data
) -> None:
    create_client(firm=firm_a, data=acme_data)
    create_client(firm=firm_a, data={**acme_data, "full_name": "Otro Cliente"})

    api = _client_for(host="acme.lawsaas.app", user=admin_user)
    response = api.get("/api/clients")
    assert response.status_code == 200
    body = response.json()
    results = body.get("results", body)
    assert len(results) == 2
    # Summary payload — no decrypted fields like dni_cuil
    assert "dni_cuil" not in results[0]
    assert "full_name_display" in results[0]


@override_settings(PUBLIC_BASE_DOMAIN="lawsaas.app")
@pytest.mark.django_db
def test_client_search_by_name(admin_membership, admin_user, firm_a, acme_data) -> None:
    create_client(firm=firm_a, data={**acme_data, "full_name": "Juan Pérez"})
    create_client(firm=firm_a, data={**acme_data, "full_name": "Carlos García"})

    api = _client_for(host="acme.lawsaas.app", user=admin_user)
    response = api.get("/api/clients?q=garcía")
    body = response.json()
    results = body.get("results", body)
    assert len(results) == 1
    assert results[0]["full_name_display"] == "Carlos García"


@override_settings(PUBLIC_BASE_DOMAIN="lawsaas.app")
@pytest.mark.django_db
def test_client_search_by_dni_partial(admin_membership, admin_user, firm_a, acme_data) -> None:
    create_client(firm=firm_a, data={**acme_data, "dni_cuil": "30123456"})
    create_client(firm=firm_a, data={**acme_data, "dni_cuil": "27987654"})

    api = _client_for(host="acme.lawsaas.app", user=admin_user)
    response = api.get("/api/clients?q=301")
    results = response.json().get("results", response.json())
    assert len(results) == 1


@override_settings(PUBLIC_BASE_DOMAIN="lawsaas.app")
@pytest.mark.django_db
def test_client_filter_by_case_status(admin_membership, admin_user, firm_a, acme_data) -> None:
    create_client(firm=firm_a, data={**acme_data, "case_status": "consulta"})
    create_client(firm=firm_a, data={**acme_data, "case_status": "demanda iniciada"})
    create_client(firm=firm_a, data={**acme_data, "case_status": "demanda iniciada"})

    api = _client_for(host="acme.lawsaas.app", user=admin_user)
    response = api.get("/api/clients?case_status=demanda%20iniciada")
    results = response.json().get("results", response.json())
    assert len(results) == 2


@override_settings(PUBLIC_BASE_DOMAIN="lawsaas.app")
@pytest.mark.django_db
def test_client_partial_update(admin_membership, admin_user, firm_a, acme_data) -> None:
    client = create_client(firm=firm_a, data=acme_data)
    api = _client_for(host="acme.lawsaas.app", user=admin_user)
    response = api.patch(
        f"/api/clients/{client.pk}",
        {"phone": "5555-9999", "case_status": "en proceso"},
        format="json",
    )
    assert response.status_code == 200, response.json()
    body = response.json()
    assert body["phone"] == "5555-9999"
    assert body["case_status"] == "en proceso"
    # Untouched fields preserved
    assert body["full_name"] == "María José Pérez"


@override_settings(PUBLIC_BASE_DOMAIN="lawsaas.app")
@pytest.mark.django_db
def test_client_destroy_admin_only(admin_membership, admin_user, firm_a, acme_data) -> None:
    client = create_client(firm=firm_a, data=acme_data)
    api = _client_for(host="acme.lawsaas.app", user=admin_user)
    response = api.delete(f"/api/clients/{client.pk}")
    assert response.status_code == 204
    assert not Client.objects.filter(pk=client.pk).exists()


# ---------------------------------------------------------------------------
# RBAC enforcement
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_BASE_DOMAIN="lawsaas.app")
@pytest.mark.django_db
def test_secretario_cannot_create_client(firm_a, secretario_user, acme_data) -> None:
    api = _client_for(host="acme.lawsaas.app", user=secretario_user)
    response = api.post("/api/clients", acme_data, format="json")
    assert response.status_code == 403


@override_settings(PUBLIC_BASE_DOMAIN="lawsaas.app")
@pytest.mark.django_db
def test_secretario_can_read_clients(firm_a, secretario_user, acme_data) -> None:
    create_client(firm=firm_a, data=acme_data)
    api = _client_for(host="acme.lawsaas.app", user=secretario_user)
    response = api.get("/api/clients")
    assert response.status_code == 200


@override_settings(PUBLIC_BASE_DOMAIN="lawsaas.app")
@pytest.mark.django_db
def test_abogado_cannot_delete_client(firm_a, abogado_user, acme_data) -> None:
    client = create_client(firm=firm_a, data=acme_data)
    api = _client_for(host="acme.lawsaas.app", user=abogado_user)
    response = api.delete(f"/api/clients/{client.pk}")
    assert response.status_code == 403
    assert Client.objects.filter(pk=client.pk).exists()


@override_settings(PUBLIC_BASE_DOMAIN="lawsaas.app")
@pytest.mark.django_db
def test_abogado_can_create_and_update(firm_a, abogado_user, acme_data) -> None:
    api = _client_for(host="acme.lawsaas.app", user=abogado_user)
    create = api.post("/api/clients", acme_data, format="json")
    assert create.status_code == 201
    cid = create.json()["id"]

    update = api.patch(f"/api/clients/{cid}", {"phone": "0000"}, format="json")
    assert update.status_code == 200


# ---------------------------------------------------------------------------
# Cross-tenant
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_BASE_DOMAIN="lawsaas.app")
@pytest.mark.django_db
def test_user_without_membership_blocked(firm_b, admin_user, admin_membership) -> None:
    """admin_user is admin of firm_a — calling on firm_b's subdomain must 403."""
    api = _client_for(host="beta.lawsaas.app", user=admin_user)
    response = api.get("/api/clients")
    assert response.status_code == 403


@override_settings(PUBLIC_BASE_DOMAIN="lawsaas.app")
@pytest.mark.django_db
def test_cross_tenant_retrieve_returns_404(
    firm_a, firm_b, admin_user, admin_membership, acme_data
) -> None:
    """A client of firm_b is not visible from firm_a, even by its real id."""
    from tenants.models import Membership

    # Make admin_user also an admin of firm_b so we *could* see it from there,
    # but we're not — we're calling from firm_a's subdomain.
    Membership.objects.create(
        user=admin_user, firm=firm_b, role=Membership.Role.ADMIN
    )
    other = create_client(firm=firm_b, data=acme_data)

    api = _client_for(host="acme.lawsaas.app", user=admin_user)
    response = api.get(f"/api/clients/{other.pk}")
    assert response.status_code == 404


@override_settings(PUBLIC_BASE_DOMAIN="lawsaas.app")
@pytest.mark.django_db
def test_no_firm_subdomain_blocks_crm(admin_user) -> None:
    """Calling /api/clients on the marketing host has no firm context."""
    api = _client_for(host="app.lawsaas.app", user=admin_user)
    response = api.get("/api/clients")
    assert response.status_code == 403  # HasFirm rejects


# ---------------------------------------------------------------------------
# Action endpoints
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_BASE_DOMAIN="lawsaas.app")
@pytest.mark.django_db
def test_create_action_for_client(
    firm_a, admin_user, admin_membership, acme_data
) -> None:
    client = create_client(firm=firm_a, data=acme_data)
    api = _client_for(host="acme.lawsaas.app", user=admin_user)
    response = api.post(
        "/api/actions",
        {
            "client": client.pk,
            "description": "Llamado a ART",
            "action_date": "2026-04-20",
            "next_action_date": "2026-04-27",
            "next_step": "Esperar respuesta",
        },
        format="json",
    )
    assert response.status_code == 201, response.json()
    body = response.json()
    assert body["description"] == "Llamado a ART"
    assert body["client_id"] == client.pk


@override_settings(PUBLIC_BASE_DOMAIN="lawsaas.app")
@pytest.mark.django_db
def test_action_complete_endpoint(
    firm_a, admin_user, admin_membership, acme_data
) -> None:
    client = create_client(firm=firm_a, data=acme_data)
    action = create_action(firm=firm_a, client=client, data={"description": "x"})
    api = _client_for(host="acme.lawsaas.app", user=admin_user)
    response = api.post(f"/api/actions/{action.pk}/complete")
    assert response.status_code == 200
    assert response.json()["completed"] is True

    action.refresh_from_db()
    assert action.completed is True


@override_settings(PUBLIC_BASE_DOMAIN="lawsaas.app")
@pytest.mark.django_db
def test_create_action_for_other_firm_404(
    firm_a, firm_b, admin_user, admin_membership, acme_data
) -> None:
    """An action create that references a client of another firm must 404."""
    other_client = create_client(firm=firm_b, data=acme_data)
    api = _client_for(host="acme.lawsaas.app", user=admin_user)
    response = api.post(
        "/api/actions",
        {"client": other_client.pk, "description": "Sneaky"},
        format="json",
    )
    assert response.status_code == 404


@override_settings(PUBLIC_BASE_DOMAIN="lawsaas.app")
@pytest.mark.django_db
def test_action_list_filter_by_client(
    firm_a, admin_user, admin_membership, acme_data
) -> None:
    c1 = create_client(firm=firm_a, data=acme_data)
    c2 = create_client(firm=firm_a, data={**acme_data, "full_name": "Other"})
    create_action(firm=firm_a, client=c1, data={"description": "1"})
    create_action(firm=firm_a, client=c1, data={"description": "2"})
    create_action(firm=firm_a, client=c2, data={"description": "3"})

    api = _client_for(host="acme.lawsaas.app", user=admin_user)
    response = api.get(f"/api/actions?client={c1.pk}")
    results = response.json().get("results", response.json())
    assert len(results) == 2


# ---------------------------------------------------------------------------
# Document endpoint (metadata-only — full upload comes in Phase 4)
# ---------------------------------------------------------------------------


@override_settings(PUBLIC_BASE_DOMAIN="lawsaas.app")
@pytest.mark.django_db
def test_document_create_metadata(
    firm_a, admin_user, admin_membership, acme_data
) -> None:
    client = create_client(firm=firm_a, data=acme_data)
    api = _client_for(host="acme.lawsaas.app", user=admin_user)
    response = api.post(
        "/api/documents",
        {
            "client": client.pk,
            "original_name": "denuncia.pdf",
            "stored_key": f"firm-{firm_a.id}/{client.pk}/denuncia.pdf",
            "mime_type": "application/pdf",
            "size_bytes": 1234,
        },
        format="json",
    )
    assert response.status_code == 201, response.json()
    body = response.json()
    assert body["original_name"] == "denuncia.pdf"
    assert body["mime_type"] == "application/pdf"


@override_settings(PUBLIC_BASE_DOMAIN="lawsaas.app")
@pytest.mark.django_db
def test_document_rejects_disallowed_extension(
    firm_a, admin_user, admin_membership, acme_data
) -> None:
    client = create_client(firm=firm_a, data=acme_data)
    api = _client_for(host="acme.lawsaas.app", user=admin_user)
    response = api.post(
        "/api/documents",
        {
            "client": client.pk,
            "original_name": "exploit.exe",
            "stored_key": "x/y/z.exe",
            "mime_type": "application/octet-stream",
            "size_bytes": 100,
        },
        format="json",
    )
    assert response.status_code == 400
    assert "original_name" in response.json()
