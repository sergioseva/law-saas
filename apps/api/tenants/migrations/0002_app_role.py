"""
Create the runtime DB role used in production.

Why: the Postgres user docker-compose creates (POSTGRES_USER=lawsaas) is a
superuser, and Postgres RLS is bypassed for superusers — even with
FORCE ROW LEVEL SECURITY. Without a non-superuser role, the RLS policies
crm/0002_rls.py adds are ornamental in dev.

This migration creates a NOLOGIN role `lawsaas_app` with the minimum
privileges to run the app (DML on public.* tables, USAGE on sequences) and
grants membership to the existing superuser so tests + admin tasks can
SET ROLE into it.

In prod, Django connects as `lawsaas_app` directly (POSTGRES_USER=lawsaas_app
plus a separate migrations connection that runs as the superuser). For the
short term, we keep dev on the superuser and use SET ROLE in a focused test
that proves RLS enforces correctly under the constrained role.

Idempotent — running it twice is a no-op.
"""
from django.db import migrations


_CREATE_SQL = """
DO $$
DECLARE
    runtime_role text := 'lawsaas_app';
    runtime_user text := current_user;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = runtime_role) THEN
        EXECUTE format(
            'CREATE ROLE %I NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS',
            runtime_role
        );
    END IF;

    -- Allow the connecting role to SET ROLE into it.
    EXECUTE format('GRANT %I TO %I', runtime_role, runtime_user);
END $$;

GRANT USAGE ON SCHEMA public TO lawsaas_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO lawsaas_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO lawsaas_app;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO lawsaas_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO lawsaas_app;
"""

_REVERSE_SQL = """
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM lawsaas_app;
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM lawsaas_app;
REVOKE USAGE ON SCHEMA public FROM lawsaas_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM lawsaas_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON SEQUENCES FROM lawsaas_app;
DROP ROLE IF EXISTS lawsaas_app;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("tenants", "0001_initial"),
        ("crm", "0002_rls"),
        ("audit", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(sql=_CREATE_SQL, reverse_sql=_REVERSE_SQL),
    ]
