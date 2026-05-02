"""
Normalization helpers for denormalized search columns.

Ported from juridico_app/database.py:
- normalize_text: lowercase + collapse internal whitespace
- digits_only: strip everything but ASCII digits
"""
from __future__ import annotations


def normalize_text(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = " ".join(value.strip().lower().split())
    return cleaned or None


def digits_only(value: str | None) -> str | None:
    if not value:
        return None
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    return digits or None


def display_or_none(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.strip()
    return cleaned or None
