# law-saas

Multi-tenant SaaS rewrite of the [`law-system`](../law-system) desktop app. Django 5 + DRF backend, Next.js 14 frontend, Postgres, Celery + Redis, Cloudflare R2 for files, deployed as docker-compose on a DigitalOcean droplet with Next.js on Vercel.

The full architecture and phased plan lives in `~/.claude/plans/i-received-this-project-mutable-hammock.md`. This README only covers the things you need to *do* to get going.

## Layout

```
apps/api    Django + DRF (the backend)
apps/web    Next.js 14 App Router (the frontend)
infra       docker-compose, Caddyfile, deploy script
docs        domain-model.md and other long-form docs
.github     CI workflows
```

## External actions to take (Phase 0)

These cannot be automated — do them in roughly this order:

- [ ] **Buy the domain.** `lawsaas.app` (or chosen alternative) at any registrar. Point its nameservers at Cloudflare.
- [ ] **Cloudflare DNS.** Add the zone, create a wildcard `A` record (`*` → droplet IP, proxy *off* — Caddy needs the real IP for DNS-01) and an `app` `A` record pointing to Vercel (or a CNAME — Vercel will tell you).
- [ ] **Cloudflare API token.** Create a scoped token (Zone:DNS:Edit on the zone only). Save it; Caddy needs it for the wildcard cert.
- [ ] **DO droplet.** $12/mo, 2 GB / 1 vCPU, Debian 12 or Ubuntu 24.04. Install Docker + Compose plugin. SSH-keys-only, disable password auth.
- [ ] **GitHub repo.** Push this monorepo (private). Add a deploy key for the droplet so `git pull` works there.
- [ ] **Vercel project.** Connect the GitHub repo, set root to `apps/web`, framework "Next.js", env var `NEXT_PUBLIC_API_BASE=https://api.lawsaas.app`.
- [ ] **Sentry.** Free account, two projects (`api`, `web`). Save DSNs.
- [ ] **Resend.** Free account, verified sender domain. Save API key.
- [ ] **Cloudflare R2.** Create a bucket per environment (`lawsaas-prod`, `lawsaas-dev`). Save access key + secret.

## Local development

Prerequisites: Docker + Compose, `pnpm`, `uv` (for managing the Python environment if you ever want to run the API outside Docker).

```bash
# First boot
cp infra/.env.example infra/.env
# Generate a master key:
python -c "from cryptography.fernet import Fernet; print('MASTER_KEK=' + Fernet.generate_key().decode())" >> infra/.env

cd infra
docker compose up -d

# Apply migrations
docker compose exec api uv run python manage.py migrate

# Run the frontend
cd ../apps/web
pnpm install
pnpm dev
```

The API is at `http://localhost:8000`, the Next.js dev server at `http://localhost:3000`. `lvh.me` resolves all subdomains to `127.0.0.1` automatically — use `acme.lvh.me`, `app.lvh.me`, etc., for local subdomain testing.

### Auth endpoints (Phase 1, wired up)

| Method | URL | Notes |
|---|---|---|
| POST | `/api/auth/signup` | Public on `app.*`; creates `User + Firm + Membership(admin) + DEK` atomically. |
| POST | `/api/auth/login` | Requires firm subdomain. Verifies user has Membership in that firm. |
| POST | `/api/auth/logout` | Clears session. |
| GET  | `/api/auth/me` | Returns current user + role + firm. |
| GET  | `/api/auth/csrf` | Sets the `csrftoken` cookie for the SPA. |
| GET  | `/api/schema/` and `/api/docs/` | drf-spectacular OpenAPI schema and Swagger UI. |

### CRM endpoints (Phase 2, wired up)

All require a firm subdomain + active session.

| Method | URL | Notes |
|---|---|---|
| GET    | `/api/clients?q=&case_status=&case_type=&city=` | Paginated summary list. `q` searches across name/DNI/phone. |
| POST   | `/api/clients` | Create. Requires write role. |
| GET    | `/api/clients/<id>` | Decrypted detail. |
| PATCH  | `/api/clients/<id>` | Partial update; merges with existing payload. |
| DELETE | `/api/clients/<id>` | Admin only. |
| GET    | `/api/actions?client=&completed=` | Paginated summary. |
| POST   | `/api/actions` | Body must include `client` (id). |
| POST   | `/api/actions/<id>/complete` | Convenience: mark as completed. |
| GET/PATCH/DELETE | `/api/actions/<id>` | Standard CRUD. |
| POST   | `/api/documents` | Metadata-only in Phase 2; bytes go via R2 in Phase 4. |
| GET    | `/api/documents?client=` | Paginated summary. |
| GET/DELETE | `/api/documents/<id>` | (PUT/PATCH return 405 — replace by delete + re-upload.) |

Roles: `admin` (full access), `abogado` (read+write), `secretario` (read-only). Permission classes live in `apps/api/tenants/permissions.py`.

### Running tests

```bash
cd infra
docker compose exec api uv run pytest
```

Tests cover: envelope encryption round-trip, tenant middleware (subdomain extraction, firm resolution), signup (atomic creation, reserved/duplicate/format rejection, weak-password rejection, transactional rollback), login (membership-required, bad-password 401, no-firm-host 403), logout, /me, and the four DRF permission classes against three role fixtures.

## Production deploy

```bash
# On the droplet, first time only
git clone git@github.com:<you>/law-saas.git /opt/law-saas
cd /opt/law-saas/infra
cp .env.prod.example .env.prod
# Fill in MASTER_KEK, POSTGRES_PASSWORD, SECRET_KEY, SENTRY_DSN, R2 creds, RESEND_API_KEY, CLOUDFLARE_API_TOKEN
docker compose -f docker-compose.prod.yml up -d

# Subsequent deploys
./infra/deploy.sh
```

## Encryption: master KEK

The master KEK lives **only** in `infra/.env.prod` on the droplet. It is referenced from `apps/api/encryption/`. Do not commit it. Generate it once with:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

If this key is lost, **all firm data is unrecoverable**. Back up the contents of `.env.prod` to a password manager / sealed envelope.

## License

Private. All rights reserved.
