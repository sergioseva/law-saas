"""
Initial CRM migration — Client, Action, Document.

Hand-written; replace with `manage.py makemigrations crm` output if it diverges.
"""
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("tenants", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Client",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("payload", models.TextField(help_text="Encrypted JSON blob (Fernet, per-firm DEK).")),
                ("full_name_display", models.CharField(blank=True, max_length=200, null=True)),
                (
                    "full_name_search",
                    models.CharField(blank=True, db_index=True, max_length=200, null=True),
                ),
                (
                    "dni_cuil_search",
                    models.CharField(blank=True, db_index=True, max_length=32, null=True),
                ),
                (
                    "phone_search",
                    models.CharField(blank=True, db_index=True, max_length=32, null=True),
                ),
                ("city_display", models.CharField(blank=True, max_length=120, null=True)),
                (
                    "case_status",
                    models.CharField(
                        choices=[
                            ("consulta", "consulta"),
                            ("en proceso", "en proceso"),
                            ("demanda iniciada", "demanda iniciada"),
                            ("cerrado", "cerrado"),
                        ],
                        default="consulta",
                        max_length=32,
                    ),
                ),
                (
                    "case_type",
                    models.CharField(
                        choices=[
                            ("Extrajudicial", "Extrajudicial"),
                            ("Judicial", "Judicial"),
                        ],
                        default="Extrajudicial",
                        max_length=32,
                    ),
                ),
                (
                    "case_label",
                    models.CharField(
                        blank=True,
                        choices=[("", ""), ("+10", "+10"), ("-10", "-10")],
                        default="",
                        max_length=8,
                    ),
                ),
                ("first_visit_date", models.DateField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "tenant",
                    models.ForeignKey(
                        db_column="tenant_id",
                        on_delete=models.deletion.CASCADE,
                        related_name="clients",
                        to="tenants.firm",
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["tenant", "case_status", "case_type", "first_visit_date"],
                        name="crm_client_tenant_status_idx",
                    ),
                    models.Index(
                        fields=["tenant", "-created_at"],
                        name="crm_client_tenant_created_idx",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="Action",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("payload", models.TextField(help_text="Encrypted JSON blob (Fernet, per-firm DEK).")),
                ("action_date", models.DateField(blank=True, null=True)),
                ("next_action_date", models.DateField(blank=True, null=True)),
                (
                    "next_step",
                    models.TextField(
                        blank=True,
                        help_text="Plaintext on purpose — used in dashboard rollups.",
                        null=True,
                    ),
                ),
                ("completed", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "client",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="actions",
                        to="crm.client",
                    ),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        db_column="tenant_id",
                        on_delete=models.deletion.CASCADE,
                        related_name="actions",
                        to="tenants.firm",
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["client", "-action_date"],
                        name="crm_action_client_date_idx",
                    ),
                    models.Index(
                        fields=["client", "next_action_date"],
                        name="crm_action_client_next_idx",
                    ),
                    models.Index(
                        fields=["next_action_date", "completed"],
                        name="crm_action_next_done_idx",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="Document",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("original_name_encrypted", models.TextField()),
                (
                    "stored_key",
                    models.TextField(help_text="Opaque R2 object key, e.g. firm-<uuid>/<random>."),
                ),
                ("notes_encrypted", models.TextField(blank=True, null=True)),
                (
                    "mime_type",
                    models.CharField(default="application/octet-stream", max_length=120),
                ),
                ("size_bytes", models.BigIntegerField(default=0)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                (
                    "client",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="documents",
                        to="crm.client",
                    ),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        db_column="tenant_id",
                        on_delete=models.deletion.CASCADE,
                        related_name="documents",
                        to="tenants.firm",
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["client", "-uploaded_at"],
                        name="crm_document_client_up_idx",
                    ),
                ],
            },
        ),
    ]
