"""
Audit-log helper. Call from views; never call from anywhere else.

Failure mode: never raise. The audit log is a sidecar; if writing fails for
any reason we log a warning and continue, because a 500 from a successful
business op just because we couldn't write an audit row is worse than a
gap in audit history.
"""
from __future__ import annotations

import logging
from typing import Any

from django.http import HttpRequest

logger = logging.getLogger(__name__)


def _client_ip(request: HttpRequest) -> str | None:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip() or None
    return request.META.get("REMOTE_ADDR") or None


def log(
    request: HttpRequest,
    action: str,
    *,
    resource_type: str = "",
    resource_id: int | None = None,
    metadata: dict[str, Any] | None = None,
    user=None,
    firm=None,
) -> None:
    """Write a single AuditLogEntry. Best-effort: never raises."""
    from .models import AuditLogEntry

    try:
        AuditLogEntry.objects.create(
            tenant=firm if firm is not None else getattr(request, "firm", None),
            user=user
            if user is not None and getattr(user, "is_authenticated", False)
            else (
                request.user
                if getattr(request, "user", None) and request.user.is_authenticated
                else None
            ),
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata=metadata or {},
            ip_address=_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:1000],
        )
    except Exception:  # noqa: BLE001
        logger.warning("audit.log failed", exc_info=True)
