"""
Excel + PDF builders. Pure functions — they don't touch the DB or storage.
The Celery task supplies the rows; this module turns them into bytes.

Column choice and ordering is ported from
juridico_app/services/export_service.py.
"""
from __future__ import annotations

from io import BytesIO
from typing import Iterable

from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


_HEADERS = [
    "Apellido y Nombre",
    "DNI / CUIL",
    "Telefono",
    "Email",
    "Ciudad",
    "Empleador",
    "ART",
    "Primera visita",
    "Motivo",
    "Estado",
]


def _row_for_client(client_dict: dict) -> list[str]:
    return [
        client_dict.get("full_name") or "",
        client_dict.get("dni_cuil") or "",
        client_dict.get("phone") or "",
        client_dict.get("email") or "",
        client_dict.get("city") or "",
        client_dict.get("employer") or "",
        client_dict.get("insurer") or "",
        client_dict.get("first_visit_date") or "",
        client_dict.get("case_reason") or "",
        client_dict.get("case_status") or "",
    ]


def build_excel(clients: Iterable[dict]) -> bytes:
    wb = Workbook()
    sheet = wb.active
    sheet.title = "Clientes"
    sheet.append(_HEADERS)
    for c in clients:
        sheet.append(_row_for_client(c))
    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def build_pdf(clients: Iterable[dict], firm_name: str) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title=f"Clientes — {firm_name}")
    styles = getSampleStyleSheet()
    story = [
        Paragraph(f"Listado de clientes — {firm_name}", styles["Heading1"]),
        Spacer(1, 12),
    ]

    rows = [_HEADERS]
    for c in clients:
        rows.append(_row_for_client(c))

    table = Table(rows, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d1d5db")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(table)
    doc.build(story)
    return buffer.getvalue()
