"""
DRF serializers for CRM resources.

Two shapes per resource:
- *Summary serializer*: denormalized columns only (no decryption). Used for
  list endpoints — fast and never touches the firm DEK.
- *Detail serializer*: full payload merged with metadata. Used for retrieve
  and create/update return values.

Validation is partly here (field-level) and partly in services.py (cross-field
business rules + invariants like case_status whitelist).
"""
from __future__ import annotations

from rest_framework import serializers

from .constants import (
    ALLOWED_DOCUMENT_EXTENSIONS,
    CASE_LABELS,
    CASE_STATUSES,
    CASE_TYPES,
)
from .models import Action, Client, Document


class ClientSummarySerializer(serializers.ModelSerializer):
    """List-view shape — only denormalized columns, no decryption."""

    class Meta:
        model = Client
        fields = [
            "id",
            "full_name_display",
            "case_status",
            "case_type",
            "case_label",
            "first_visit_date",
            "city_display",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class ClientWriteSerializer(serializers.Serializer):
    """Input shape for create/update — accepts the flat domain dict."""

    full_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    dni_cuil = serializers.CharField(max_length=32, required=False, allow_blank=True)
    birth_date = serializers.DateField(required=False, allow_null=True)
    phone = serializers.CharField(max_length=32, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    address = serializers.CharField(max_length=200, required=False, allow_blank=True)
    city = serializers.CharField(max_length=120, required=False, allow_blank=True)
    employer = serializers.CharField(max_length=200, required=False, allow_blank=True)
    insurer = serializers.CharField(max_length=200, required=False, allow_blank=True)
    case_reason = serializers.CharField(required=False, allow_blank=True)
    discharge_condition = serializers.CharField(
        max_length=64, required=False, allow_blank=True
    )
    occupational_disease = serializers.CharField(
        max_length=8, required=False, allow_blank=True
    )

    case_status = serializers.ChoiceField(
        choices=CASE_STATUSES, required=False, default="consulta"
    )
    case_type = serializers.ChoiceField(
        choices=CASE_TYPES, required=False, default="Extrajudicial"
    )
    case_label = serializers.ChoiceField(
        choices=CASE_LABELS, required=False, default="", allow_blank=True
    )
    first_visit_date = serializers.DateField(required=False, allow_null=True)

    document_checklist = serializers.DictField(
        child=serializers.BooleanField(), required=False
    )


class ActionSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Action
        fields = [
            "id",
            "client",
            "action_date",
            "next_action_date",
            "next_step",
            "completed",
            "created_at",
        ]
        read_only_fields = fields


class ActionWriteSerializer(serializers.Serializer):
    description = serializers.CharField(allow_blank=True, required=False)
    action_date = serializers.DateField(required=False, allow_null=True)
    next_action_date = serializers.DateField(required=False, allow_null=True)
    next_step = serializers.CharField(allow_blank=True, required=False)
    completed = serializers.BooleanField(required=False, default=False)


class DocumentSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            "id",
            "client",
            "stored_key",
            "mime_type",
            "size_bytes",
            "uploaded_at",
        ]
        read_only_fields = fields


class DocumentCreateSerializer(serializers.Serializer):
    """
    Phase 2.2 minimal shape — record metadata only. The actual upload flow
    (pre-signed POST URL + R2 redirect) lands in Phase 4.
    """

    original_name = serializers.CharField(max_length=255)
    stored_key = serializers.CharField(max_length=500)
    mime_type = serializers.CharField(max_length=120)
    size_bytes = serializers.IntegerField(min_value=0)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_original_name(self, value: str) -> str:
        ext = value.rsplit(".", 1)[-1].lower() if "." in value else ""
        if ext not in ALLOWED_DOCUMENT_EXTENSIONS:
            raise serializers.ValidationError(f"File type .{ext} is not allowed.")
        return value
