"""
DB-level Row-Level Security enforcement.

The dev container connects as a Postgres superuser (which bypasses RLS), so
the rest of our tenant-isolation tests prove only the app-layer guards. This
test simulates the production scenario: SET ROLE into the non-superuser
runtime role created by tenants/0002_app_role.py, then verify:

  1. A query without `app.tenant_id` set returns ZERO rows from CRM tables.
  2. A query with the GUC set to firm A's id returns only firm A's rows.
  3. A query with the GUC set to firm B's id returns only firm B's rows.

If this test passes, RLS in prod will enforce tenant isolation even if a bug
slips through the application-layer queryset filters.
"""
from __future__ import annotations

import pytest
from django.db import connection
from django.test import override_settings


@pytest.fixture
def _isolated_db():
    """
    Use transactional_db so SET ROLE / SET LOCAL behave naturally — the
    default `db` fixture wraps each test in a transaction-with-savepoints
    that confuses role/GUC scoping.
    """
    pass


@override_settings(PUBLIC_BASE_DOMAIN="lawsaas.app")
@pytest.mark.django_db(transaction=True)
def test_rls_enforces_under_runtime_role(firm_a, firm_b) -> None:
    from crm.services import create_client

    create_client(firm=firm_a, data={"full_name": "A1"})
    create_client(firm=firm_a, data={"full_name": "A2"})
    create_client(firm=firm_b, data={"full_name": "B1"})

    with connection.cursor() as cursor:
        cursor.execute("SET ROLE lawsaas_app")
        try:
            # 1. No GUC set → policy yields 0 rows.
            cursor.execute("SELECT set_config('app.tenant_id', '', false)")
            cursor.execute("SELECT count(*) FROM crm_client")
            assert cursor.fetchone()[0] == 0

            # 2. Firm A's GUC → only A's rows.
            cursor.execute("SELECT set_config('app.tenant_id', %s, false)", [str(firm_a.id)])
            cursor.execute("SELECT count(*) FROM crm_client")
            assert cursor.fetchone()[0] == 2

            # 3. Firm B's GUC → only B's row.
            cursor.execute("SELECT set_config('app.tenant_id', %s, false)", [str(firm_b.id)])
            cursor.execute("SELECT count(*) FROM crm_client")
            assert cursor.fetchone()[0] == 1
        finally:
            cursor.execute("RESET ROLE")
            cursor.execute("SELECT set_config('app.tenant_id', '', false)")


@override_settings(PUBLIC_BASE_DOMAIN="lawsaas.app")
@pytest.mark.django_db(transaction=True)
def test_rls_blocks_writes_to_other_tenant(firm_a, firm_b) -> None:
    """
    Even with INSERT privileges, a row whose tenant_id doesn't match the GUC
    must be rejected by the policy's WITH CHECK clause.
    """
    from crm.services import create_client

    seeded = create_client(firm=firm_a, data={"full_name": "Seed"})

    with connection.cursor() as cursor:
        cursor.execute("SET ROLE lawsaas_app")
        try:
            # Pretend to be firm A
            cursor.execute(
                "SELECT set_config('app.tenant_id', %s, false)", [str(firm_a.id)]
            )
            # Try to UPDATE a firm-A row to belong to firm B.
            with pytest.raises(Exception):  # noqa: PT012
                cursor.execute(
                    "UPDATE crm_client SET tenant_id = %s WHERE id = %s",
                    [str(firm_b.id), seeded.id],
                )
        finally:
            cursor.execute("RESET ROLE")
            cursor.execute("SELECT set_config('app.tenant_id', '', false)")
