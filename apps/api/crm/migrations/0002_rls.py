"""
Enable Postgres Row Level Security on the CRM tables.

The TenantMiddleware sets `app.tenant_id` per request; these policies filter
every query on crm_* by it.

CAVEAT: RLS is bypassed by Postgres superusers. The default postgres docker
image creates the configured POSTGRES_USER as a superuser, so for *local
dev* RLS does not enforce. In production, use a non-superuser role:

    CREATE ROLE lawsaas_app LOGIN PASSWORD '...' NOSUPERUSER NOCREATEDB NOCREATEROLE;
    GRANT USAGE ON SCHEMA public TO lawsaas_app;
    GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO lawsaas_app;
    GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO lawsaas_app;

…then point Django's DATABASES default at `lawsaas_app`.

Phase 5 (production hardening) does this swap and adds a DB-level isolation
test. In Phase 2, isolation is enforced by:
  1. TenantManager auto-applies filter(tenant=request.firm).
  2. Serializers reject mismatched tenant_id in payloads.
  3. These RLS policies (when running as non-superuser).
"""
from django.db import migrations


_TABLES = ("crm_client", "crm_action", "crm_document")


def _enable_rls() -> str:
    parts = []
    for table in _TABLES:
        parts.append(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        parts.append(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")
        parts.append(
            f"CREATE POLICY tenant_isolation ON {table} "
            "USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid) "
            "WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);"
        )
    return "\n".join(parts)


def _disable_rls() -> str:
    parts = []
    for table in _TABLES:
        parts.append(f"DROP POLICY IF EXISTS tenant_isolation ON {table};")
        parts.append(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;")
        parts.append(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
    return "\n".join(parts)


class Migration(migrations.Migration):
    dependencies = [
        ("crm", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(sql=_enable_rls(), reverse_sql=_disable_rls()),
    ]
