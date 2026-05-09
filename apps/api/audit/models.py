"""
Append-only audit log.

Every sensitive operation (auth, CRUD on client/action/document, exports) writes
a row here. The DB-level constraint we DON'T have yet is "no UPDATE / no DELETE"
— that's a Phase 5 hardening migration once we move runtime to a non-superuser
role. For now, the discipline is convention: only audit.services.log writes to
this table, and there's no admin / serializer / viewset surface that mutates it.
"""
from __future__ import annotations

from django.conf import settings
from django.db import models


class AuditLogEntry(models.Model):
    tenant = models.ForeignKey(
        "tenants.Firm",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_entries",
        db_column="tenant_id",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_entries",
    )
    action = models.CharField(max_length=64)
    resource_type = models.CharField(max_length=32, blank=True, default="")
    resource_id = models.BigIntegerField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "-created_at"]),
            models.Index(fields=["action", "-created_at"]),
        ]

    def __str__(self) -> str:
        who = self.user.email if self.user_id else "anon"
        what = self.action
        target = (
            f" {self.resource_type}#{self.resource_id}"
            if self.resource_type and self.resource_id
            else ""
        )
        return f"{who} {what}{target}"
