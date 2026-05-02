"""
Business operations on tenants/users that need transactional integrity.
"""
from __future__ import annotations

from dataclasses import dataclass

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction

from encryption.envelope import generate_dek, wrap_dek

from .models import Firm, Membership, User


@dataclass(frozen=True)
class FirmRegistration:
    user: User
    firm: Firm
    membership: Membership


@transaction.atomic
def register_firm(
    *,
    email: str,
    password: str,
    firm_name: str,
    subdomain: str,
) -> FirmRegistration:
    """
    Create User + Firm + Membership(admin) + per-firm DEK in one transaction.

    Validation of `subdomain` (slug, length, reserved-list, uniqueness) and
    `email` (uniqueness, format) is the caller's responsibility — the
    serializer does it before calling this. We still raise on collisions
    here in case of races.
    """
    email_norm = email.strip().lower()

    # Will raise django.core.exceptions.ValidationError if too weak.
    validate_password(password)

    user = User.objects.create_user(email=email_norm, password=password)

    dek = generate_dek()
    firm = Firm.objects.create(
        subdomain=subdomain.lower(),
        name=firm_name.strip(),
        wrapped_dek=wrap_dek(dek),
    )

    membership = Membership.objects.create(
        user=user,
        firm=firm,
        role=Membership.Role.ADMIN,
    )
    return FirmRegistration(user=user, firm=firm, membership=membership)


__all__ = ["FirmRegistration", "register_firm", "DjangoValidationError"]
