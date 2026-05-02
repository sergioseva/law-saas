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
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

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


class SignupView(APIView):
    """Public — creates a new firm + admin user."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = register_firm(**serializer.validated_data)

        return Response(
            {
                "firm": FirmSerializer(result.firm).data,
                "redirect_url": _firm_url(result.firm),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """Login on a firm subdomain. Verifies membership in that firm."""

    permission_classes = [AllowAny, HasFirm]

    def post(self, request: Request) -> Response:
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            request,
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        if user is None:
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

        firm = request.firm  # type: ignore[attr-defined]
        membership = (
            Membership.objects.filter(user=user, firm=firm).only("role").first()
        )
        if membership is None:
            return Response(
                {"detail": "User has no access to this firm."},
                status=status.HTTP_403_FORBIDDEN,
            )

        login(request, user)
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
