"""
DRF viewsets for CRM resources.

Action-aware permissions:
    list, retrieve  -> IsRead
    create, update, partial_update -> IsWrite
    destroy         -> IsDelete

Tenant scoping: every queryset is filtered by `request.firm` in get_queryset().
Cross-tenant requests get a 404 (not 403) — we don't reveal that the row
exists in another firm.
"""
from __future__ import annotations

from urllib.parse import quote

from django.conf import settings
from django.db.models import Q
from django.http import StreamingHttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from encryption.envelope import decrypt_text
from tenants.permissions import HasFirm, IsDelete, IsRead, IsWrite

from . import services
from .models import Action, Client, Document
from .serializers import (
    ActionSummarySerializer,
    ActionWriteSerializer,
    ClientSummarySerializer,
    ClientWriteSerializer,
    DocumentSummarySerializer,
)


class _TenantScopedViewSet(viewsets.ModelViewSet):
    """Common base — resolves request.firm and applies it to every queryset."""

    permission_classes = [IsAuthenticated, HasFirm, IsRead]

    def get_permissions(self):  # noqa: D401
        action = getattr(self, "action", None)
        if action in {"list", "retrieve"}:
            classes = [IsAuthenticated, HasFirm, IsRead]
        elif action == "destroy":
            classes = [IsAuthenticated, HasFirm, IsDelete]
        else:
            classes = [IsAuthenticated, HasFirm, IsWrite]
        return [c() for c in classes]

    @property
    def firm(self):
        return self.request.firm  # type: ignore[attr-defined]


class ClientViewSet(_TenantScopedViewSet):
    queryset = Client.objects.all()
    lookup_value_regex = r"\d+"

    def get_queryset(self):
        qs = Client.objects.filter(tenant=self.firm)

        params = self.request.query_params
        if (q := params.get("q")):
            normalized = q.strip().lower()
            digits = "".join(ch for ch in q if ch.isdigit())
            term_filter = Q(full_name_search__icontains=normalized)
            if digits:
                term_filter |= Q(dni_cuil_search__startswith=digits)
                term_filter |= Q(phone_search__contains=digits)
            qs = qs.filter(term_filter)

        if (status_val := params.get("case_status")):
            qs = qs.filter(case_status=status_val)
        if (type_val := params.get("case_type")):
            qs = qs.filter(case_type=type_val)
        if (city := params.get("city")):
            qs = qs.filter(city_display__iexact=city.strip())

        return qs.order_by("-created_at")

    def list(self, request: Request, *args, **kwargs) -> Response:
        page = self.paginate_queryset(self.get_queryset())
        ser = ClientSummarySerializer(page or self.get_queryset(), many=True)
        if page is not None:
            return self.get_paginated_response(ser.data)
        return Response(ser.data)

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        client = self.get_object()
        return Response(services.read_client(firm=self.firm, client=client))

    def create(self, request: Request, *args, **kwargs) -> Response:
        ser = ClientWriteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        client = services.create_client(firm=self.firm, data=dict(ser.validated_data))
        return Response(
            services.read_client(firm=self.firm, client=client),
            status=status.HTTP_201_CREATED,
        )

    def update(self, request: Request, *args, **kwargs) -> Response:
        client = self.get_object()
        ser = ClientWriteSerializer(data=request.data, partial=False)
        ser.is_valid(raise_exception=True)
        client = services.update_client(
            firm=self.firm, client=client, data=dict(ser.validated_data)
        )
        return Response(services.read_client(firm=self.firm, client=client))

    def partial_update(self, request: Request, *args, **kwargs) -> Response:
        client = self.get_object()
        ser = ClientWriteSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        client = services.update_client(
            firm=self.firm, client=client, data=dict(ser.validated_data)
        )
        return Response(services.read_client(firm=self.firm, client=client))


class ActionViewSet(_TenantScopedViewSet):
    queryset = Action.objects.all()
    lookup_value_regex = r"\d+"

    def get_queryset(self):
        qs = Action.objects.filter(tenant=self.firm)
        if (client_id := self.request.query_params.get("client")):
            qs = qs.filter(client_id=client_id)
        if (completed := self.request.query_params.get("completed")) is not None:
            if completed.lower() in {"true", "1"}:
                qs = qs.filter(completed=True)
            elif completed.lower() in {"false", "0"}:
                qs = qs.filter(completed=False)
        return qs.order_by("-action_date", "-id")

    def list(self, request: Request, *args, **kwargs) -> Response:
        page = self.paginate_queryset(self.get_queryset())
        ser = ActionSummarySerializer(page or self.get_queryset(), many=True)
        if page is not None:
            return self.get_paginated_response(ser.data)
        return Response(ser.data)

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        action = self.get_object()
        return Response(services.read_action(firm=self.firm, action=action))

    def create(self, request: Request, *args, **kwargs) -> Response:
        client_id = request.data.get("client")
        if not client_id:
            return Response(
                {"client": "This field is required."}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            client = Client.objects.get(pk=client_id, tenant=self.firm)
        except (Client.DoesNotExist, ValueError):
            return Response({"client": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        ser = ActionWriteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        action = services.create_action(
            firm=self.firm, client=client, data=dict(ser.validated_data)
        )
        return Response(
            services.read_action(firm=self.firm, action=action),
            status=status.HTTP_201_CREATED,
        )

    def update(self, request: Request, *args, **kwargs) -> Response:
        action = self.get_object()
        ser = ActionWriteSerializer(data=request.data, partial=False)
        ser.is_valid(raise_exception=True)
        action = services.update_action(
            firm=self.firm, action=action, data=dict(ser.validated_data)
        )
        return Response(services.read_action(firm=self.firm, action=action))

    def partial_update(self, request: Request, *args, **kwargs) -> Response:
        action = self.get_object()
        ser = ActionWriteSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        action = services.update_action(
            firm=self.firm, action=action, data=dict(ser.validated_data)
        )
        return Response(services.read_action(firm=self.firm, action=action))

    @action(detail=True, methods=["post"], url_path="complete")
    def mark_completed(self, request: Request, pk=None) -> Response:
        action = self.get_object()
        updated = services.update_action(firm=self.firm, action=action, data={"completed": True})
        return Response(services.read_action(firm=self.firm, action=updated))


class DocumentViewSet(_TenantScopedViewSet):
    queryset = Document.objects.all()
    lookup_value_regex = r"\d+"
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_queryset(self):
        qs = Document.objects.filter(tenant=self.firm)
        if (client_id := self.request.query_params.get("client")):
            qs = qs.filter(client_id=client_id)
        return qs.order_by("-uploaded_at")

    def list(self, request: Request, *args, **kwargs) -> Response:
        page = self.paginate_queryset(self.get_queryset())
        ser = DocumentSummarySerializer(page or self.get_queryset(), many=True)
        if page is not None:
            return self.get_paginated_response(ser.data)
        return Response(ser.data)

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        doc = self.get_object()
        return Response(services.read_document(firm=self.firm, document=doc))

    def create(self, request: Request, *args, **kwargs) -> Response:
        """
        Multipart upload — body must include `client` (id), `file`, optional `notes`.

        File size is bounded by settings.MAX_DOCUMENT_BYTES; the extension is
        whitelisted in services.upload_document. Stored key is opaque and
        firm-namespaced; the original filename lives encrypted in the row.
        """
        client_id = request.data.get("client")
        if not client_id:
            return Response(
                {"client": "This field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            client = Client.objects.get(pk=client_id, tenant=self.firm)
        except (Client.DoesNotExist, ValueError):
            return Response({"client": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        upload = request.FILES.get("file")
        if upload is None:
            return Response(
                {"file": "This field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if upload.size and upload.size > settings.MAX_DOCUMENT_BYTES:
            return Response(
                {"file": f"File exceeds {settings.MAX_DOCUMENT_BYTES // (1024 * 1024)} MB limit."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        notes = request.data.get("notes") or None
        try:
            doc = services.upload_document(
                firm=self.firm,
                client=client,
                file_obj=upload,
                original_name=upload.name,
                mime_type=upload.content_type or "application/octet-stream",
                notes=notes if isinstance(notes, str) else None,
            )
        except ValueError as exc:
            return Response({"file": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            services.read_document(firm=self.firm, document=doc),
            status=status.HTTP_201_CREATED,
        )

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        doc = self.get_object()
        services.delete_document(firm=self.firm, document=doc)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request: Request, pk=None) -> StreamingHttpResponse:
        doc = self.get_object()
        original_name = (
            decrypt_text(self.firm.dek, doc.original_name_encrypted) or f"document-{doc.pk}"
        )
        stream = services.open_document_stream(firm=self.firm, document=doc)
        response = StreamingHttpResponse(
            _read_in_chunks(stream),
            content_type=doc.mime_type or "application/octet-stream",
        )
        response["Content-Length"] = str(doc.size_bytes)
        # RFC 5987 — preserve UTF-8 names while staying ASCII-safe.
        ascii_safe = quote(original_name)
        response["Content-Disposition"] = (
            f"attachment; filename*=UTF-8''{ascii_safe}"
        )
        return response

    def update(self, request, *args, **kwargs):  # noqa: ARG002
        return Response(
            {"detail": "Documents cannot be updated; delete and re-upload."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def partial_update(self, request, *args, **kwargs):  # noqa: ARG002
        return Response(
            {"detail": "Documents cannot be updated; delete and re-upload."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )


def _read_in_chunks(fileobj, chunk_size: int = 64 * 1024):
    try:
        while chunk := fileobj.read(chunk_size):
            yield chunk
    finally:
        try:
            fileobj.close()
        except Exception:
            pass
