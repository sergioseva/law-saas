"""DRF permission classes — role enforcement."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from django.contrib.auth.models import AnonymousUser

from tenants.permissions import HasFirm, IsAdmin, IsDelete, IsRead, IsWrite


def _request(*, user, firm) -> MagicMock:
    request = MagicMock()
    request.user = user
    request.firm = firm
    return request


@pytest.mark.django_db
def test_has_firm_requires_request_firm(firm_a, admin_user) -> None:
    assert HasFirm().has_permission(_request(user=admin_user, firm=firm_a), None) is True
    assert HasFirm().has_permission(_request(user=admin_user, firm=None), None) is False


@pytest.mark.django_db
def test_unauthenticated_user_blocked_at_every_level(firm_a) -> None:
    req = _request(user=AnonymousUser(), firm=firm_a)
    assert IsRead().has_permission(req, None) is False
    assert IsWrite().has_permission(req, None) is False
    assert IsDelete().has_permission(req, None) is False
    assert IsAdmin().has_permission(req, None) is False


@pytest.mark.django_db
def test_user_without_membership_blocked(firm_a, firm_b, admin_membership, admin_user) -> None:
    """Admin of firm_a calling on firm_b is unauthorized."""
    req = _request(user=admin_user, firm=firm_b)
    assert IsRead().has_permission(req, None) is False
    assert IsWrite().has_permission(req, None) is False
    assert IsDelete().has_permission(req, None) is False
    assert IsAdmin().has_permission(req, None) is False


@pytest.mark.django_db
def test_secretario_only_reads(firm_a, secretario_user) -> None:
    req = _request(user=secretario_user, firm=firm_a)
    assert IsRead().has_permission(req, None) is True
    assert IsWrite().has_permission(req, None) is False
    assert IsDelete().has_permission(req, None) is False
    assert IsAdmin().has_permission(req, None) is False


@pytest.mark.django_db
def test_abogado_reads_and_writes(firm_a, abogado_user) -> None:
    req = _request(user=abogado_user, firm=firm_a)
    assert IsRead().has_permission(req, None) is True
    assert IsWrite().has_permission(req, None) is True
    assert IsDelete().has_permission(req, None) is False
    assert IsAdmin().has_permission(req, None) is False


@pytest.mark.django_db
def test_admin_can_do_everything(firm_a, admin_membership, admin_user) -> None:
    req = _request(user=admin_user, firm=firm_a)
    assert IsRead().has_permission(req, None) is True
    assert IsWrite().has_permission(req, None) is True
    assert IsDelete().has_permission(req, None) is True
    assert IsAdmin().has_permission(req, None) is True
