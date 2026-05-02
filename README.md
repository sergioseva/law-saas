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
# Edit infra/.env — set MASTER_KEK to a random 32-byte base64 string for local dev.

cd infra
docker compose up -d

# Apply migrations
docker compose exec api uv run python manage.py migrate

# Create a superuser (used for the Django admin only, not the SaaS auth flow)
docker compose exec api uv run python manage.py createsuperuser

# Run the frontend
cd ../apps/web
pnpm install
pnpm dev
```

The API is at `http://localhost:8000`, the Next.js dev server at `http://localhost:3000`.

For local subdomain routing, edit `/etc/hosts`:
```
127.0.0.1   acme.lvh.me beta.lvh.me app.lvh.me api.lvh.me
```
Or use `lvh.me` (resolves all subdomains to 127.0.0.1) directly.

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
