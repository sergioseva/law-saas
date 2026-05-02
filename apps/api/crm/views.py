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

from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from tenants.permissions import HasFirm, IsDelete, IsRead, IsWrite

from . import services
from .models import Action, Client, Document
from .serializers import (
    ActionSummarySerializer,
    ActionWriteSerializer,
    ClientSummarySerializer,
    ClientWriteSerializer,
    DocumentCreateSerializer,
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
        client_id = request.data.get("client")
        if not client_id:
            return Response(
                {"client": "This field is required."}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            client = Client.objects.get(pk=client_id, tenant=self.firm)
        except (Client.DoesNotExist, ValueError):
            return Response({"client": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        ser = DocumentCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        doc = services.create_document(
            firm=self.firm,
            client=client,
            **{
                k: v
                for k, v in ser.validated_data.items()
                if k in {"original_name", "stored_key", "mime_type", "size_bytes", "notes"}
            },
        )
        return Response(
            services.read_document(firm=self.firm, document=doc),
            status=status.HTTP_201_CREATED,
        )

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
