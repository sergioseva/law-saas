"""
DRF permission classes — port of the legacy three-level RBAC.

Every domain endpoint should layer these on top of `IsAuthenticated`:

    @permission_classes([IsAuthenticated, HasFirm, IsWrite])
    def my_view(...): ...

The role check uses `request.firm` (set by TenantMiddleware) to look up the
caller's Membership in this tenant. A user without membership in the current
firm is treated as zero-level — even if logged in.
"""
from __future__ import annotations

from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from .models import Membership

_LEVEL = {
    Membership.Role.ADMIN: 30,
    Membership.Role.ABOGADO: 20,
    Membership.Role.SECRETARIO: 10,
}

_PERM_READ = 10
_PERM_WRITE = 20
_PERM_DELETE = 30
_PERM_ADMIN = 30


def _user_level(request: Request) -> int:
    """Return the request user's permission level inside `request.firm`."""
    firm = getattr(request, "firm", None)
    user = getattr(request, "user", None)
    if firm is None or user is None or not user.is_authenticated:
        return 0
    membership = (
        Membership.objects.filter(user=user, firm=firm).only("role").first()
    )
    if membership is None:
        return 0
    return _LEVEL.get(Membership.Role(membership.role), 0)


class HasFirm(BasePermission):
    """The request must be on a firm subdomain (TenantMiddleware resolved one)."""

    message = "Firm not found."

    def has_permission(self, request: Request, view) -> bool:
        return getattr(request, "firm", None) is not None


class IsRead(BasePermission):
    message = "Insufficient role for this action."

    def has_permission(self, request: Request, view) -> bool:
        return _user_level(request) >= _PERM_READ


class IsWrite(BasePermission):
    message = "Insufficient role for this action."

    def has_permission(self, request: Request, view) -> bool:
        return _user_level(request) >= _PERM_WRITE


class IsDelete(BasePermission):
    message = "Insufficient role for this action."

    def has_permission(self, request: Request, view) -> bool:
        return _user_level(request) >= _PERM_DELETE


class IsAdmin(BasePermission):
    message = "Admin role required."

    def has_permission(self, request: Request, view) -> bool:
        return _user_level(request) >= _PERM_ADMIN
