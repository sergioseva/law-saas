"""
Tenant + auth models.

Phase 1 fleshes these out — at this stage we just want migrations to run and
the auth system to find the custom user model. The fields below are the
minimum to make `AUTH_USER_MODEL = "tenants.User"` work.
"""
import uuid
from functools import cached_property

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager["User"]):
    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Email-as-identity user. No global username — disambiguation is by email.
    Firm membership is a separate model so one user can belong to multiple firms.
    """

    username = None  # type: ignore[assignment]
    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()  # type: ignore[misc]

    def __str__(self) -> str:
        return self.email


class Firm(models.Model):
    """A tenant — one law firm."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subdomain = models.SlugField(unique=True, max_length=63)
    name = models.CharField(max_length=200)
    wrapped_dek = models.TextField(
        help_text="Per-firm data encryption key, wrapped with the master KEK.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["subdomain"])]

    def __str__(self) -> str:
        return f"{self.name} ({self.subdomain})"

    @cached_property
    def dek(self) -> bytes:
        """
        Decrypted per-firm data encryption key. Cached on the instance, which
        is per-request (TenantMiddleware constructs a fresh Firm per request).
        Callers pass this into encryption.envelope helpers.
        """
        from encryption.envelope import unwrap_dek

        return unwrap_dek(self.wrapped_dek)


class Membership(models.Model):
    """User ↔ Firm with role. The RBAC matrix is ported from the legacy app."""

    class Role(models.TextChoices):
        ADMIN = "admin", "Administrador"
        ABOGADO = "abogado", "Abogado"
        SECRETARIO = "secretario", "Secretario"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    firm = models.ForeignKey(Firm, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.ABOGADO)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "firm")]
        indexes = [models.Index(fields=["firm", "role"])]

    def __str__(self) -> str:
        return f"{self.user.email} @ {self.firm.subdomain} ({self.role})"
