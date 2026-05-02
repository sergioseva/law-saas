"""
Domain enumerations — ported from juridico_app/routes.py:36–49.
Spanish strings are canonical (the legacy app is Spanish-only).
"""
from __future__ import annotations

CASE_STATUSES = ("consulta", "en proceso", "demanda iniciada", "cerrado")
CASE_TYPES = ("Extrajudicial", "Judicial")
CASE_LABELS = ("", "+10", "-10")

DOCUMENT_CHECKLIST_ITEMS = (
    "DNI",
    "Denuncia",
    "Historia clinica",
    "Cd de la art",
    "Recibos de sueldo",
    "Informe",
    "Alta medica",
)

PHOTO_EXTENSIONS = frozenset({"png", "jpg", "jpeg", "webp"})
ALLOWED_DOCUMENT_EXTENSIONS = frozenset(
    {"pdf", "png", "jpg", "jpeg", "webp", "doc", "docx", "txt"}
)
PROFILE_PHOTO_SIZE = (280, 280)
MAX_DOCUMENT_BYTES = 16 * 1024 * 1024  # 16 MB

CLIENTS_PER_PAGE = 25
ACTIONS_PER_PAGE = 12
DOCUMENTS_PER_PAGE = 12
