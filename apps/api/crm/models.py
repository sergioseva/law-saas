"""
Domain models — Client, Action, Document.

Pattern (ported from the legacy app):
- Sensitive fields → encrypted JSON in `payload` column.
- Search/filter/sort fields → denormalized plaintext columns, kept in sync via
  `crm/services.py`.

Tenant isolation:
- Every row carries `tenant_id` (FK to Firm).
- Postgres RLS policies (see crm/migrations/0002_rls.py) filter every query
  by `current_setting('app.tenant_id')`. Devs cannot bypass this from app code.
"""
from __future__ import annotations

from django.db import models

from .constants import CASE_LABELS, CASE_STATUSES, CASE_TYPES


class Client(models.Model):
    tenant = models.ForeignKey(
        "tenants.Firm",
        on_delete=models.CASCADE,
        related_name="clients",
        db_column="tenant_id",
    )
    payload = models.TextField(
        help_text="Encrypted JSON blob (Fernet, per-firm DEK).",
    )

    # Denormalized plaintext columns — kept in sync via services.set_client_index.
    full_name_display = models.CharField(max_length=200, null=True, blank=True)
    full_name_search = models.CharField(max_length=200, null=True, blank=True, db_index=True)
    dni_cuil_search = models.CharField(max_length=32, null=True, blank=True, db_index=True)
    phone_search = models.CharField(max_length=32, null=True, blank=True, db_index=True)
    city_display = models.CharField(max_length=120, null=True, blank=True)
    case_status = models.CharField(
        max_length=32,
        choices=[(s, s) for s in CASE_STATUSES],
        default="consulta",
    )
    case_type = models.CharField(
        max_length=32,
        choices=[(t, t) for t in CASE_TYPES],
        default="Extrajudicial",
    )
    case_label = models.CharField(
        max_length=8,
        choices=[(label, label) for label in CASE_LABELS],
        default="",
        blank=True,
    )
    first_visit_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "case_status", "case_type", "first_visit_date"]),
            models.Index(fields=["tenant", "-created_at"]),
        ]

    def __str__(self) -> str:
        return self.full_name_display or f"Client #{self.pk}"


class Action(models.Model):
    """Actuación — an event/note attached to a Client."""

    tenant = models.ForeignKey(
        "tenants.Firm",
        on_delete=models.CASCADE,
        related_name="actions",
        db_column="tenant_id",
    )
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="actions")
    payload = models.TextField(help_text="Encrypted JSON blob (Fernet, per-firm DEK).")

    action_date = models.DateField(null=True, blank=True)
    next_action_date = models.DateField(null=True, blank=True)
    next_step = models.TextField(
        null=True,
        blank=True,
        help_text="Plaintext on purpose — used in dashboard rollups.",
    )
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["client", "-action_date"]),
            models.Index(fields=["client", "next_action_date"]),
            models.Index(fields=["next_action_date", "completed"]),
        ]

    def __str__(self) -> str:
        return f"Action #{self.pk} on Client #{self.client_id}"


class Document(models.Model):
    """File attached to a Client. Bytes live in R2 keyed by `stored_key`."""

    tenant = models.ForeignKey(
        "tenants.Firm",
        on_delete=models.CASCADE,
        related_name="documents",
        db_column="tenant_id",
    )
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="documents")
    original_name_encrypted = models.TextField()
    stored_key = models.TextField(help_text="Opaque R2 object key, e.g. firm-<uuid>/<random>.")
    notes_encrypted = models.TextField(null=True, blank=True)
    mime_type = models.CharField(max_length=120, default="application/octet-stream")
    size_bytes = models.BigIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["client", "-uploaded_at"]),
        ]

    def __str__(self) -> str:
        return f"Document #{self.pk} on Client #{self.client_id}"
