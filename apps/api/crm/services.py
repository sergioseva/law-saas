"""
Domain services — the encrypted-payload + denormalized-search-columns pattern.

Models stay dumb (they don't know about encryption). All read/write to a Client
or Action goes through these services so encryption and denormalization are
guaranteed to stay in sync.

Pattern:
    payload (encrypted JSON) ←→ data dict (Python)
    denormalized columns      ←  derived from data dict on every save

Tenant safety:
    Every public function here takes an explicit `firm: Firm`. We never let
    callers bypass the tenant boundary — even at the service layer.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from django.db import transaction

from encryption.envelope import (
    decrypt_payload,
    decrypt_text,
    encrypt_payload,
    encrypt_text,
)
from tenants.models import Firm

from .constants import CASE_LABELS, CASE_STATUSES, CASE_TYPES, DOCUMENT_CHECKLIST_ITEMS
from .models import Action, Client, Document
from .normalize import digits_only, display_or_none, normalize_text

# Fields stored encrypted inside Client.payload.
_CLIENT_PAYLOAD_FIELDS = {
    "full_name",
    "dni_cuil",
    "birth_date",
    "phone",
    "email",
    "address",
    "city",
    "employer",
    "insurer",
    "case_reason",
    "discharge_condition",
    "occupational_disease",
    "document_checklist",
    "profile_photo_path",
}

# Fields stored encrypted inside Action.payload.
_ACTION_PAYLOAD_FIELDS = {"description"}


def _coerce_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    # datetime is a subclass of date, so check the more specific type first.
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value), "%Y-%m-%d").date()


def _client_index_values(data: dict) -> dict:
    """Extract the denormalized search/sort columns from a client data dict."""
    case_status = data.get("case_status") or "consulta"
    if case_status not in CASE_STATUSES:
        raise ValueError(f"Invalid case_status: {case_status!r}")

    case_type = data.get("case_type") or "Extrajudicial"
    if case_type not in CASE_TYPES:
        raise ValueError(f"Invalid case_type: {case_type!r}")

    case_label = data.get("case_label") or ""
    if case_label not in CASE_LABELS:
        raise ValueError(f"Invalid case_label: {case_label!r}")

    return {
        "full_name_display": display_or_none(data.get("full_name")),
        "full_name_search": normalize_text(data.get("full_name")),
        "dni_cuil_search": digits_only(data.get("dni_cuil")),
        "phone_search": digits_only(data.get("phone")),
        "city_display": display_or_none(data.get("city")),
        "case_status": case_status,
        "case_type": case_type,
        "case_label": case_label,
        "first_visit_date": _coerce_date(data.get("first_visit_date")),
    }


def _action_index_values(data: dict) -> dict:
    return {
        "action_date": _coerce_date(data.get("action_date")),
        "next_action_date": _coerce_date(data.get("next_action_date")),
        "next_step": (data.get("next_step") or "").strip() or None,
        "completed": bool(data.get("completed")),
    }


def _split_client_data(data: dict) -> tuple[dict, dict]:
    """Split a client input dict into (payload_dict, index_columns)."""
    index = _client_index_values(data)
    # Default checklist if missing
    payload = {k: v for k, v in data.items() if k in _CLIENT_PAYLOAD_FIELDS}
    payload.setdefault(
        "document_checklist", {item: False for item in DOCUMENT_CHECKLIST_ITEMS}
    )
    return payload, index


def _split_action_data(data: dict) -> tuple[dict, dict]:
    index = _action_index_values(data)
    payload = {k: v for k, v in data.items() if k in _ACTION_PAYLOAD_FIELDS}
    return payload, index


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


@transaction.atomic
def create_client(*, firm: Firm, data: dict) -> Client:
    payload, index = _split_client_data(data)
    return Client.objects.create(
        tenant=firm,
        payload=encrypt_payload(firm.dek, payload),
        **index,
    )


@transaction.atomic
def update_client(*, firm: Firm, client: Client, data: dict) -> Client:
    if client.tenant_id != firm.id:
        raise PermissionError("Client does not belong to this firm.")

    existing = decrypt_payload(firm.dek, client.payload)
    merged = {**existing, **data}
    payload, index = _split_client_data(merged)

    client.payload = encrypt_payload(firm.dek, payload)
    for k, v in index.items():
        setattr(client, k, v)
    client.save()
    return client


def read_client(*, firm: Firm, client: Client) -> dict:
    if client.tenant_id != firm.id:
        raise PermissionError("Client does not belong to this firm.")

    payload = decrypt_payload(firm.dek, client.payload)
    return {
        **payload,
        "id": client.pk,
        "case_status": client.case_status,
        "case_type": client.case_type,
        "case_label": client.case_label,
        "first_visit_date": (
            client.first_visit_date.isoformat() if client.first_visit_date else None
        ),
        "city": client.city_display,
        "created_at": client.created_at.isoformat(),
        "updated_at": client.updated_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# Action
# ---------------------------------------------------------------------------


@transaction.atomic
def create_action(*, firm: Firm, client: Client, data: dict) -> Action:
    if client.tenant_id != firm.id:
        raise PermissionError("Client does not belong to this firm.")

    payload, index = _split_action_data(data)
    return Action.objects.create(
        tenant=firm,
        client=client,
        payload=encrypt_payload(firm.dek, payload),
        **index,
    )


@transaction.atomic
def update_action(*, firm: Firm, action: Action, data: dict) -> Action:
    if action.tenant_id != firm.id:
        raise PermissionError("Action does not belong to this firm.")

    existing = decrypt_payload(firm.dek, action.payload)
    merged = {**existing, **data}
    payload, index = _split_action_data(merged)

    action.payload = encrypt_payload(firm.dek, payload)
    for k, v in index.items():
        setattr(action, k, v)
    action.save()
    return action


def read_action(*, firm: Firm, action: Action) -> dict:
    if action.tenant_id != firm.id:
        raise PermissionError("Action does not belong to this firm.")

    payload = decrypt_payload(firm.dek, action.payload)
    return {
        **payload,
        "id": action.pk,
        "client_id": action.client_id,
        "action_date": action.action_date.isoformat() if action.action_date else None,
        "next_action_date": (
            action.next_action_date.isoformat() if action.next_action_date else None
        ),
        "next_step": action.next_step,
        "completed": action.completed,
        "created_at": action.created_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# Document — metadata only; bytes go to R2 in Phase 4.
# ---------------------------------------------------------------------------


@transaction.atomic
def create_document(
    *,
    firm: Firm,
    client: Client,
    original_name: str,
    stored_key: str,
    mime_type: str,
    size_bytes: int,
    notes: str | None = None,
) -> Document:
    if client.tenant_id != firm.id:
        raise PermissionError("Client does not belong to this firm.")

    return Document.objects.create(
        tenant=firm,
        client=client,
        original_name_encrypted=encrypt_text(firm.dek, original_name) or "",
        stored_key=stored_key,
        notes_encrypted=encrypt_text(firm.dek, notes),
        mime_type=mime_type,
        size_bytes=size_bytes,
    )


def read_document(*, firm: Firm, document: Document) -> dict:
    if document.tenant_id != firm.id:
        raise PermissionError("Document does not belong to this firm.")

    return {
        "id": document.pk,
        "client_id": document.client_id,
        "original_name": decrypt_text(firm.dek, document.original_name_encrypted),
        "notes": decrypt_text(firm.dek, document.notes_encrypted),
        "stored_key": document.stored_key,
        "mime_type": document.mime_type,
        "size_bytes": document.size_bytes,
        "uploaded_at": document.uploaded_at.isoformat(),
    }
