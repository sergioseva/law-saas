"""Reminder digest task — sends one email per firm with upcoming actions."""
from __future__ import annotations

from datetime import date, timedelta

import pytest
from django.core import mail
from django.test import override_settings


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_reminder_digest_includes_upcoming_excludes_completed_and_far(
    firm_a, firm_b, admin_membership, admin_user, abogado_user, secretario_user
) -> None:
    from crm.services import create_action, create_client
    from tenants.tasks import send_action_reminders

    # Firm A: client with several actions covering edge cases.
    client_a = create_client(firm=firm_a, data={"full_name": "Cliente Uno"})
    create_action(
        firm=firm_a,
        client=client_a,
        data={
            "description": "Próxima",
            "next_action_date": (date.today() + timedelta(days=2)).isoformat(),
        },
    )
    create_action(
        firm=firm_a,
        client=client_a,
        data={
            "description": "Pasada",
            "next_action_date": (date.today() - timedelta(days=1)).isoformat(),
        },
    )
    create_action(
        firm=firm_a,
        client=client_a,
        data={
            "description": "Lejos",
            "next_action_date": (date.today() + timedelta(days=30)).isoformat(),
        },
    )
    create_action(
        firm=firm_a,
        client=client_a,
        data={
            "description": "Hecha",
            "next_action_date": (date.today() + timedelta(days=1)).isoformat(),
            "completed": True,
        },
    )

    # Firm B: no upcoming actions
    create_client(firm=firm_b, data={"full_name": "Solo de B"})

    mail.outbox = []
    summary = send_action_reminders()

    assert summary[firm_a.subdomain] == 1  # only the "Próxima" action
    assert summary[firm_b.subdomain] == 0
    assert len(mail.outbox) == 1
    msg = mail.outbox[0]
    assert "Próximas actuaciones" in msg.subject
    assert firm_a.name in msg.subject
    # Recipients: admin + abogado in firm A; secretario excluded
    recipients = set(msg.to)
    assert admin_user.email in recipients
    assert abogado_user.email in recipients
    assert secretario_user.email not in recipients


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_reminder_skips_firms_without_recipients(firm_b) -> None:
    """Firm B has actions but no admin/abogado memberships → no email sent."""
    from crm.services import create_action, create_client
    from tenants.tasks import send_action_reminders

    client = create_client(firm=firm_b, data={"full_name": "Test"})
    create_action(
        firm=firm_b,
        client=client,
        data={
            "description": "x",
            "next_action_date": (date.today() + timedelta(days=2)).isoformat(),
        },
    )

    mail.outbox = []
    summary = send_action_reminders()

    assert summary[firm_b.subdomain] == 0
    assert len(mail.outbox) == 0
