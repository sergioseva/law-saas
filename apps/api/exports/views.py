"""
Export endpoints — kick off Celery tasks and poll their status.

POST /api/exports/excel  → enqueues build_excel_export, returns task_id
POST /api/exports/pdf    → enqueues build_pdf_export, returns task_id
GET  /api/exports/<task_id> → status + download URL when ready
GET  /api/exports/<task_id>/download → streams the produced file

The download endpoint enforces tenant scoping (an export for firm A can't be
fetched from a session in firm B) by storing the firm id alongside the
result-bound storage key.
"""
from __future__ import annotations

from urllib.parse import quote

from celery.result import AsyncResult
from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from storage import FileNotFoundInStorage, get_storage
from tenants.permissions import HasFirm, IsRead

from .tasks import build_excel_export, build_pdf_export


class _Base(APIView):
    permission_classes = [IsAuthenticated, HasFirm, IsRead]


class ExcelExportView(_Base):
    def post(self, request: Request) -> Response:
        firm = request.firm  # type: ignore[attr-defined]
        result = build_excel_export.delay(str(firm.id))
        return Response(
            {"task_id": result.id, "status": "queued"},
            status=status.HTTP_202_ACCEPTED,
        )


class PdfExportView(_Base):
    def post(self, request: Request) -> Response:
        firm = request.firm  # type: ignore[attr-defined]
        result = build_pdf_export.delay(str(firm.id))
        return Response(
            {"task_id": result.id, "status": "queued"},
            status=status.HTTP_202_ACCEPTED,
        )


class ExportStatusView(_Base):
    """GET /api/exports/<task_id>"""

    def get(self, request: Request, task_id: str) -> Response:
        result = AsyncResult(task_id)
        firm = request.firm  # type: ignore[attr-defined]

        if result.failed():
            return Response({"task_id": task_id, "status": "failed"})
        if not result.ready():
            return Response({"task_id": task_id, "status": "pending"})

        descriptor = result.result or {}
        stored_key = descriptor.get("stored_key", "")
        # Tenant guard: stored_key encodes the firm id; reject if it doesn't
        # match the requesting firm.
        if not stored_key.startswith(f"exports/firm-{firm.id}/"):
            return Response(
                {"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            {
                "task_id": task_id,
                "status": "ready",
                "size_bytes": descriptor.get("size_bytes"),
                "mime_type": descriptor.get("mime_type"),
                "download_url": f"/api/exports/{task_id}/download",
            }
        )


class ExportDownloadView(_Base):
    """GET /api/exports/<task_id>/download — streams the produced file."""

    def get(self, request: Request, task_id: str) -> StreamingHttpResponse | Response:
        result = AsyncResult(task_id)
        firm = request.firm  # type: ignore[attr-defined]

        if not result.ready() or result.failed():
            return Response(
                {"detail": "Export is not ready."},
                status=status.HTTP_404_NOT_FOUND,
            )
        descriptor = result.result or {}
        stored_key: str = descriptor.get("stored_key", "")
        if not stored_key.startswith(f"exports/firm-{firm.id}/"):
            return Response(
                {"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND
            )

        try:
            stream = get_storage().open(stored_key)
        except FileNotFoundInStorage:
            return Response(
                {"detail": "Export file expired or missing."},
                status=status.HTTP_404_NOT_FOUND,
            )

        suggested = stored_key.rsplit("/", 1)[-1]
        ascii_safe = quote(suggested)
        response = StreamingHttpResponse(
            _read_in_chunks(stream),
            content_type=descriptor.get("mime_type", "application/octet-stream"),
        )
        if descriptor.get("size_bytes"):
            response["Content-Length"] = str(descriptor["size_bytes"])
        response["Content-Disposition"] = (
            f"attachment; filename*=UTF-8''{ascii_safe}"
        )
        return response


def _read_in_chunks(fileobj, chunk_size: int = 64 * 1024):
    try:
        while chunk := fileobj.read(chunk_size):
            yield chunk
    finally:
        try:
            fileobj.close()
        except Exception:
            pass
