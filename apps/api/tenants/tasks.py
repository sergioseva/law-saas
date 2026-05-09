"""
Celery tasks for tenant-side concerns (currently: action reminder emails).

Schedule lives in lawsaas/celery.py — Beat fires send_action_reminders once
a day in Argentina time.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage
from django.db.models import Q

logger = logging.getLogger(__name__)

REMINDER_WINDOW_DAYS = 3


@shared_task
def send_action_reminders() -> dict:
    """
    Scan every firm for actions whose next_action_date lands in the next 3 days
    and aren't completed. Send a digest to the firm's admins + abogados.

    Returns a small per-firm summary so it's visible in Celery Flower / logs.
    """
    from crm.models import Action

    from .models import Firm, Membership

    today = date.today()
    cutoff = today + timedelta(days=REMINDER_WINDOW_DAYS)

    summary: dict[str, int] = {}

    for firm in Firm.objects.all():
        upcoming = (
            Action.objects.filter(tenant=firm, completed=False)
            .filter(next_action_date__gte=today, next_action_date__lte=cutoff)
            .order_by("next_action_date", "id")
        )
        if not upcoming.exists():
            summary[firm.subdomain] = 0
            continue

        recipients = list(
            Membership.objects.filter(
                firm=firm, role__in=[Membership.Role.ADMIN, Membership.Role.ABOGADO]
            )
            .select_related("user")
            .values_list("user__email", flat=True)
        )
        if not recipients:
            summary[firm.subdomain] = 0
            continue

        body = _render_digest(firm=firm, actions=upcoming)
        subject = f"Próximas actuaciones — {firm.name}"

        message = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipients,
        )
        try:
            message.send(fail_silently=False)
            summary[firm.subdomain] = upcoming.count()
        except Exception:  # noqa: BLE001
            logger.exception("Failed to send reminders for firm=%s", firm.subdomain)
            summary[firm.subdomain] = -1

    return summary


def _render_digest(*, firm, actions) -> str:
    """Plain-text digest. HTML can come later when we have a templating story."""
    from crm.services import read_action

    lines = [
        f"Estudio: {firm.name}",
        "",
        "Tenés las siguientes actuaciones pendientes en los próximos 3 días:",
        "",
    ]
    for action in actions[:50]:  # cap so emails don't get unwieldy
        plain = read_action(firm=firm, action=action)
        client_name = _client_name(firm=firm, client=action.client)
        when = action.next_action_date.strftime("%d/%m/%Y")
        step = plain.get("next_step") or plain.get("description") or "(sin descripción)"
        lines.append(f"  • {when} — {client_name}: {step}")

    lines.extend(
        [
            "",
            "Ingresá a tu panel para más detalles.",
            "",
            "— law-saas",
        ]
    )
    return "\n".join(lines)


def _client_name(*, firm, client) -> str:
    if client.full_name_display:
        return client.full_name_display
    try:
        from crm.services import read_client

        plain = read_client(firm=firm, client=client)
        return plain.get("full_name") or f"Cliente #{client.pk}"
    except Exception:  # noqa: BLE001
        return f"Cliente #{client.pk}"
