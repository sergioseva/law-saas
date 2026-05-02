"""
Email-based auth backend.

We don't store usernames; `User.USERNAME_FIELD = "email"` already wires that up
for `django.contrib.auth`, but we keep this explicit class so the lookup is
case-insensitive (defensible default for emails).
"""
from __future__ import annotations

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import AbstractBaseUser

from .models import User


class EmailBackend(ModelBackend):
    def authenticate(  # type: ignore[override]
        self,
        request,
        username: str | None = None,
        password: str | None = None,
        **kwargs,
    ) -> AbstractBaseUser | None:
        # `username` here is the email (Django passes the value of USERNAME_FIELD).
        email = (username or kwargs.get("email") or "").strip().lower()
        if not email or not password:
            return None
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            User().set_password(password)  # constant-time placeholder
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
