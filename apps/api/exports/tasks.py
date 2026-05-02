"""
Celery tasks for async exports.

Phase 4 fleshes these out — the legacy `services/export_service.py` is the
specification for column choices and ordering.
"""
from celery import shared_task


@shared_task
def ping() -> str:
    """Smoke-test task — confirms the worker is wired up."""
    return "pong"
