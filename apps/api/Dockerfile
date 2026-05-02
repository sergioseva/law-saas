ARG PYTHON_VERSION=3.12-slim-bookworm

# ---------- base ----------
FROM python:${PYTHON_VERSION} AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_LINK_MODE=copy

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.4.18 /uv /usr/local/bin/uv

WORKDIR /app

# ---------- deps ----------
FROM base AS deps
COPY pyproject.toml ./
RUN uv sync --no-install-project

# ---------- dev ----------
FROM deps AS dev
COPY . .
EXPOSE 8000
CMD ["uv", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]

# ---------- prod ----------
FROM deps AS prod
COPY . .
RUN uv run python manage.py collectstatic --noinput || true
EXPOSE 8000
CMD ["uv", "run", "gunicorn", "lawsaas.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
