"""
Auth & tenant endpoints.

URL layout (mounted at /api/auth/ in lawsaas/urls.py):
    POST /api/auth/signup     public; creates User + Firm + Membership(admin) + DEK
    POST /api/auth/login      requires firm subdomain; verifies user is a member
    POST /api/auth/logout     requires session
    GET  /api/auth/me         requires session; returns user + role + firm
    GET  /api/auth/csrf       sets the csrftoken cookie (for the SPA)
"""
from __future__ import annotations

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django_ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from audit.services import log as audit_log

from .models import Firm, Membership
from .permissions import HasFirm
from .serializers import (
    FirmSerializer,
    LoginSerializer,
    MeSerializer,
    SignupSerializer,
)
from .services import register_firm


def _firm_url(firm: Firm) -> str:
    """Best-effort tenant URL for the redirect hint after signup."""
    base = settings.PUBLIC_BASE_DOMAIN
    scheme = "https" if not settings.DEBUG else "http"
    return f"{scheme}://{firm.subdomain}.{base}"


@method_decorator(
    ratelimit(key="ip", rate="3/h", method="POST", block=True), name="post"
)
class SignupView(APIView):
    """Public — creates a new firm + admin user. Rate-limited 3/hour per IP."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = register_firm(**serializer.validated_data)

        audit_log(
            request,
            "auth.signup",
            resource_type="firm",
            resource_id=None,  # firm.id is a UUID; encode in metadata instead
            metadata={"subdomain": result.firm.subdomain, "firm_id": str(result.firm.id)},
            user=result.user,
            firm=result.firm,
        )

        return Response(
            {
                "firm": FirmSerializer(result.firm).data,
                "redirect_url": _firm_url(result.firm),
            },
            status=status.HTTP_201_CREATED,
        )


@method_decorator(
    ratelimit(key="ip", rate="5/5m", method="POST", block=True), name="post"
)
class LoginView(APIView):
    """Login on a firm subdomain. Verifies membership. Rate-limited 5/5min per IP."""

    permission_classes = [AllowAny, HasFirm]

    def post(self, request: Request) -> Response:
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        firm = request.firm  # type: ignore[attr-defined]

        user = authenticate(
            request,
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        if user is None:
            audit_log(
                request,
                "auth.login_failed",
                metadata={"email": serializer.validated_data["email"]},
                firm=firm,
            )
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

        membership = (
            Membership.objects.filter(user=user, firm=firm).only("role").first()
        )
        if membership is None:
            audit_log(
                request,
                "auth.login_denied",
                metadata={"reason": "no_membership", "email": user.email},
                user=user,
                firm=firm,
            )
            return Response(
                {"detail": "User has no access to this firm."},
                status=status.HTTP_403_FORBIDDEN,
            )

        login(request, user)
        audit_log(
            request,
            "auth.login",
            metadata={"role": membership.role},
            user=user,
            firm=firm,
        )
        return Response(
            {
                "user": {"email": user.email},
                "role": membership.role,
                "firm": FirmSerializer(firm).data,
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        audit_log(request, "auth.logout")
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        firm = getattr(request, "firm", None)
        role = None
        if firm is not None:
            membership = (
                Membership.objects.filter(user=request.user, firm=firm).only("role").first()
            )
            role = membership.role if membership is not None else None

        payload = {
            "email": request.user.email,
            "role": role,
            "firm": FirmSerializer(firm).data if firm is not None else None,
        }
        # Use serializer for shape consistency; data already conforms.
        return Response(MeSerializer(payload).data)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfView(APIView):
    """GET this once from the SPA so the csrftoken cookie is set."""

    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        return Response({"csrfToken": get_token(request)})
