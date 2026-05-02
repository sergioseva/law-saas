#!/usr/bin/env bash
# Deploy script for the DO droplet. Run from /opt/law-saas/infra.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> Pulling latest code"
git pull --ff-only

cd infra

echo "==> Building images"
docker compose -f docker-compose.prod.yml build

echo "==> Applying migrations"
docker compose -f docker-compose.prod.yml run --rm api uv run python manage.py migrate

echo "==> Collecting static files"
docker compose -f docker-compose.prod.yml run --rm api uv run python manage.py collectstatic --noinput

echo "==> Restarting services"
docker compose -f docker-compose.prod.yml up -d

echo "==> Pruning dangling images"
docker image prune -f

echo "==> Done."
