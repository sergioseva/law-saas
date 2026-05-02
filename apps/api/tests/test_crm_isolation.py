"""
CRM tenant isolation — service-layer + payload encryption.

These tests enforce isolation at the *application* layer (services + serializers).
DB-layer RLS is also configured (crm/migrations/0002_rls.py) but is bypassed
when the connection is a Postgres superuser — which is the case for the default
docker-compose dev DB. Phase 5 hardening swaps in a non-superuser role and adds
DB-level isolation tests that bypass the service layer.
"""
from __future__ import annotations

import pytest

from crm.models import Action, Client
from crm.services import (
    create_action,
    create_client,
    read_action,
    read_client,
    update_client,
)


@pytest.fixture
def acme_client_data() -> dict:
    return {
        "full_name": "  María José  PÉREZ ",
        "dni_cuil": "30.123.456-7",
        "phone": "(011) 4555-1234",
        "email": "mj@example.com",
        "address": "Av. Corrientes 1234",
        "city": "CABA",
        "case_status": "consulta",
        "case_type": "Extrajudicial",
        "case_label": "",
        "first_visit_date": "2026-04-15",
        "case_reason": "ART denegada",
    }


@pytest.mark.django_db
def test_create_client_encrypts_payload_and_denormalizes(firm_a, acme_client_data) -> None:
    client = create_client(firm=firm_a, data=acme_client_data)

    # Payload is encrypted ciphertext — plaintext fields must not appear.
    assert "María" not in client.payload
    assert "30123456" not in client.payload
    assert client.payload.startswith("gAAAAA")  # Fernet token signature

    # Denormalized columns are populated.
    assert client.full_name_display == "María José  PÉREZ"
    assert client.full_name_search == "maría josé pérez"
    assert client.dni_cuil_search == "301234567"
    assert client.phone_search == "01145551234"
    assert client.city_display == "CABA"
    assert client.case_status == "consulta"
    assert str(client.first_visit_date) == "2026-04-15"


@pytest.mark.django_db
def test_read_client_round_trips_payload(firm_a, acme_client_data) -> None:
    client = create_client(firm=firm_a, data=acme_client_data)
    plain = read_client(firm=firm_a, client=client)

    assert plain["full_name"] == "  María José  PÉREZ "  # raw string preserved in payload
    assert plain["dni_cuil"] == "30.123.456-7"
    assert plain["case_status"] == "consulta"
    assert plain["id"] == client.pk
    assert isinstance(plain["document_checklist"], dict)


@pytest.mark.django_db
def test_update_client_keeps_unchanged_fields(firm_a, acme_client_data) -> None:
    client = create_client(firm=firm_a, data=acme_client_data)
    updated = update_client(
        firm=firm_a,
        client=client,
        data={"phone": "5555", "case_status": "en proceso"},
    )

    plain = read_client(firm=firm_a, client=updated)
    assert plain["phone"] == "5555"
    assert plain["full_name"] == acme_client_data["full_name"]  # untouched
    assert updated.case_status == "en proceso"
    assert updated.phone_search == "5555"  # denormalized in sync


@pytest.mark.django_db
def test_invalid_case_status_rejected(firm_a, acme_client_data) -> None:
    bad = {**acme_client_data, "case_status": "imaginario"}
    with pytest.raises(ValueError, match="case_status"):
        create_client(firm=firm_a, data=bad)


@pytest.mark.django_db
def test_service_rejects_cross_tenant_update(firm_a, firm_b, acme_client_data) -> None:
    """update_client with the wrong firm must raise PermissionError."""
    client = create_client(firm=firm_a, data=acme_client_data)
    with pytest.raises(PermissionError):
        update_client(firm=firm_b, client=client, data={"phone": "9999"})


@pytest.mark.django_db
def test_service_rejects_cross_tenant_read(firm_a, firm_b, acme_client_data) -> None:
    client = create_client(firm=firm_a, data=acme_client_data)
    with pytest.raises(PermissionError):
        read_client(firm=firm_b, client=client)


@pytest.mark.django_db
def test_payload_encrypted_with_correct_dek(firm_a, firm_b, acme_client_data) -> None:
    """Decrypting firm A's payload with firm B's DEK must fail."""
    from cryptography.fernet import InvalidToken

    from encryption.envelope import decrypt_payload

    client = create_client(firm=firm_a, data=acme_client_data)
    with pytest.raises(InvalidToken):
        decrypt_payload(firm_b.dek, client.payload)


@pytest.mark.django_db
def test_action_round_trip(firm_a, acme_client_data) -> None:
    client = create_client(firm=firm_a, data=acme_client_data)
    action = create_action(
        firm=firm_a,
        client=client,
        data={
            "description": "Llamado a ART",
            "action_date": "2026-04-20",
            "next_action_date": "2026-04-27",
            "next_step": "Esperar respuesta",
        },
    )
    plain = read_action(firm=firm_a, action=action)
    assert plain["description"] == "Llamado a ART"
    assert plain["next_step"] == "Esperar respuesta"
    assert plain["completed"] is False
    assert plain["client_id"] == client.pk

    # Denormalized columns
    assert action.next_step == "Esperar respuesta"  # plaintext — used in dashboards
    assert "Esperar" not in action.payload  # but only `description` lives in payload


@pytest.mark.django_db
def test_action_belongs_to_correct_tenant(firm_a, firm_b, acme_client_data) -> None:
    """Cross-tenant create_action must fail (client belongs to firm A)."""
    client = create_client(firm=firm_a, data=acme_client_data)
    with pytest.raises(PermissionError):
        create_action(firm=firm_b, client=client, data={"description": "Sneaky"})


@pytest.mark.django_db
def test_no_cross_tenant_data_via_orm(firm_a, firm_b, acme_client_data) -> None:
    """Sanity: each firm's queryset only sees its own rows when filtered explicitly."""
    create_client(firm=firm_a, data=acme_client_data)
    create_client(firm=firm_b, data={**acme_client_data, "full_name": "Other Person"})

    a_clients = list(Client.objects.filter(tenant=firm_a))
    b_clients = list(Client.objects.filter(tenant=firm_b))
    assert len(a_clients) == 1
    assert len(b_clients) == 1
    assert a_clients[0].id != b_clients[0].id

    # Without the explicit filter, both rows are visible — we expect this in
    # dev (superuser bypasses RLS). Phase 5 hardening switches to a
    # non-superuser role; this assertion will flip in that test then.
    all_clients = list(Client.objects.all())
    assert len(all_clients) == 2


@pytest.mark.django_db
def test_no_cross_tenant_action_via_orm(firm_a, firm_b, acme_client_data) -> None:
    a_client = create_client(firm=firm_a, data=acme_client_data)
    b_client = create_client(firm=firm_b, data={**acme_client_data, "full_name": "Other"})
    create_action(firm=firm_a, client=a_client, data={"description": "A"})
    create_action(firm=firm_b, client=b_client, data={"description": "B"})

    assert Action.objects.filter(tenant=firm_a).count() == 1
    assert Action.objects.filter(tenant=firm_b).count() == 1
