"""
Shared pytest fixtures.

Tests use the `MASTER_KEK` env var (set by CI / docker-compose) — but if it's
absent we generate one for the test session so unit tests don't fail before
they start. Don't do this in prod.
"""
from __future__ import annotations

import os

import pytest
from cryptography.fernet import Fernet


def pytest_configure(config) -> None:  # noqa: ARG001
    if not os.environ.get("MASTER_KEK"):
        os.environ["MASTER_KEK"] = Fernet.generate_key().decode("ascii")


@pytest.fixture
def firm_a(db):
    from encryption.envelope import generate_dek, wrap_dek
    from tenants.models import Firm

    return Firm.objects.create(
        subdomain="acme",
        name="Acme & Asociados",
        wrapped_dek=wrap_dek(generate_dek()),
    )


@pytest.fixture
def firm_b(db):
    from encryption.envelope import generate_dek, wrap_dek
    from tenants.models import Firm

    return Firm.objects.create(
        subdomain="beta",
        name="Beta Legal",
        wrapped_dek=wrap_dek(generate_dek()),
    )


@pytest.fixture(autouse=True)
def _disable_ratelimit(settings):
    """Tests bombard auth/exports endpoints; turn off rate limiting by default.
    Specific tests can re-enable with `settings.RATELIMIT_ENABLE = True`."""
    settings.RATELIMIT_ENABLE = False


@pytest.fixture
def admin_user(db):
    from tenants.models import User

    return User.objects.create_user(email="admin@acme.test", password="adminpass-12345")


@pytest.fixture
def admin_membership(db, firm_a, admin_user):
    from tenants.models import Membership

    return Membership.objects.create(user=admin_user, firm=firm_a, role=Membership.Role.ADMIN)


@pytest.fixture
def abogado_user(db, firm_a):
    from tenants.models import Membership, User

    user = User.objects.create_user(email="abogado@acme.test", password="abogado-12345")
    Membership.objects.create(user=user, firm=firm_a, role=Membership.Role.ABOGADO)
    return user


@pytest.fixture
def secretario_user(db, firm_a):
    from tenants.models import Membership, User

    user = User.objects.create_user(email="sec@acme.test", password="secretario-12345")
    Membership.objects.create(user=user, firm=firm_a, role=Membership.Role.SECRETARIO)
    return user
