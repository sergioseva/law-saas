"""
Initial migration — User, Firm, Membership.

Hand-written because we don't have a live Django install at the time of authoring.
If `python manage.py makemigrations tenants` later produces a divergent file, replace
this module with the generated one.
"""
import uuid

import django.utils.timezone
from django.conf import settings
from django.db import migrations, models

import tenants.models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "last_login",
                    models.DateTimeField(blank=True, null=True, verbose_name="last login"),
                ),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text=(
                            "Designates that this user has all permissions without "
                            "explicitly assigning them."
                        ),
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "first_name",
                    models.CharField(blank=True, max_length=150, verbose_name="first name"),
                ),
                (
                    "last_name",
                    models.CharField(blank=True, max_length=150, verbose_name="last name"),
                ),
                (
                    "is_staff",
                    models.BooleanField(
                        default=False,
                        help_text="Designates whether the user can log into this admin site.",
                        verbose_name="staff status",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text=(
                            "Designates whether this user should be treated as active. "
                            "Unselect this instead of deleting accounts."
                        ),
                        verbose_name="active",
                    ),
                ),
                (
                    "date_joined",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="date joined"
                    ),
                ),
                ("email", models.EmailField(max_length=254, unique=True)),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text=(
                            "The groups this user belongs to. A user will get all "
                            "permissions granted to each of their groups."
                        ),
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "verbose_name": "user",
                "verbose_name_plural": "users",
                "abstract": False,
            },
            managers=[
                ("objects", tenants.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name="Firm",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("subdomain", models.SlugField(max_length=63, unique=True)),
                ("name", models.CharField(max_length=200)),
                (
                    "wrapped_dek",
                    models.TextField(
                        help_text="Per-firm data encryption key, wrapped with the master KEK.",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "indexes": [
                    models.Index(fields=["subdomain"], name="tenants_firm_subdom_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="Membership",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("admin", "Administrador"),
                            ("abogado", "Abogado"),
                            ("secretario", "Secretario"),
                        ],
                        default="abogado",
                        max_length=16,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "firm",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="memberships",
                        to="tenants.firm",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="memberships",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(fields=["firm", "role"], name="tenants_memb_firm_role_idx"),
                ],
                "unique_together": {("user", "firm")},
            },
        ),
    ]
