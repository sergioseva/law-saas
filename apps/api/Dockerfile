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

# Install uv. 0.5.x handles PEP 735 [dependency-groups] correctly — earlier
# 0.4 builds skipped them silently with `uv sync --no-install-project`, which
# meant pytest/ruff/mypy weren't actually present in the venv.
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /usr/local/bin/uv

WORKDIR /app

# ---------- deps ----------
FROM base AS deps
COPY pyproject.toml ./
# --all-groups: install main + every dependency group (i.e., dev too).
RUN uv sync --no-install-project --all-groups

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
