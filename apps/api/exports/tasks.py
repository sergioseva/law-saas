"""
Celery tasks for async exports.

Each task takes a tenant_id, decrypts every client payload via the firm DEK
(under firm context — superuser tasks bypass tenant middleware, so the firm
is loaded explicitly), builds the file, persists to storage under an
exports/ prefix, and returns the stored_key. The polling endpoint maps the
task's result to a download URL.
"""
from __future__ import annotations

import io
import uuid
from typing import Iterator

from celery import shared_task

from .builders import build_excel, build_pdf


@shared_task
def ping() -> str:
    """Smoke-test task — confirms the worker is wired up."""
    return "pong"


def _iter_clients(firm_id: str) -> Iterator[dict]:
    """Decrypt + flatten every client of a firm. Lazy generator."""
    from crm.models import Client
    from crm.services import read_client
    from tenants.models import Firm

    firm = Firm.objects.get(pk=firm_id)
    for c in Client.objects.filter(tenant=firm).order_by("-created_at"):
        yield read_client(firm=firm, client=c)


def _save_export(firm_id: str, suffix: str, data: bytes, mime_type: str) -> dict:
    """Persist `data` under exports/<firm>/<random>.<suffix>; return descriptor."""
    from storage import get_storage

    storage = get_storage()
    key = f"exports/firm-{firm_id}/{uuid.uuid4().hex}.{suffix}"
    bio = io.BytesIO(data)
    storage.save(key, bio, content_type=mime_type)
    return {"stored_key": key, "size_bytes": len(data), "mime_type": mime_type}


@shared_task(bind=True)
def build_excel_export(self, firm_id: str) -> dict:
    rows = list(_iter_clients(firm_id))
    payload = build_excel(rows)
    return _save_export(
        firm_id=firm_id,
        suffix="xlsx",
        data=payload,
        mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@shared_task(bind=True)
def build_pdf_export(self, firm_id: str) -> dict:
    from tenants.models import Firm

    firm = Firm.objects.get(pk=firm_id)
    rows = list(_iter_clients(firm_id))
    payload = build_pdf(rows, firm_name=firm.name)
    return _save_export(
        firm_id=firm_id,
        suffix="pdf",
        data=payload,
        mime_type="application/pdf",
    )
