"""
DRF serializers for the auth/tenant endpoints.
"""
from __future__ import annotations

import re

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Firm, Membership, User

# RFC-1035-ish: 3–63 chars, lowercase letters/digits/hyphens, no leading/trailing hyphen.
_SUBDOMAIN_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{1,61}[a-z0-9])?$")


class SignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=12)
    firm_name = serializers.CharField(min_length=1, max_length=200)
    subdomain = serializers.CharField(min_length=3, max_length=63)

    def validate_email(self, value: str) -> str:
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value

    def validate_subdomain(self, value: str) -> str:
        value = value.strip().lower()
        if not _SUBDOMAIN_RE.match(value):
            raise serializers.ValidationError(
                "Use 3–63 lowercase letters, digits, or hyphens. Cannot start or end with a hyphen."
            )
        if value in settings.RESERVED_SUBDOMAINS:
            raise serializers.ValidationError("This subdomain is reserved.")
        if Firm.objects.filter(subdomain=value).exists():
            raise serializers.ValidationError("This subdomain is taken.")
        return value

    def validate_password(self, value: str) -> str:
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class FirmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Firm
        fields = ["id", "subdomain", "name", "created_at"]
        read_only_fields = fields


class MeSerializer(serializers.Serializer):
    """Shape returned by /api/auth/me/ — user + role within current firm."""

    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=Membership.Role.choices, allow_null=True)
    firm = FirmSerializer(allow_null=True)
