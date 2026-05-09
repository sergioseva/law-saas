"""
Envelope encryption helpers.

`MASTER_KEK` (in env) wraps each firm's `DEK`. The DEK encrypts the actual data.
Phase 2 wires this into the CRM models. Phase 1 only needs `wrap_dek` and
`unwrap_dek` so the signup flow can create a Firm with `wrapped_dek`.

Migration to a real KMS later means swapping `MASTER_KEK` for a KMS-backed key
without re-encrypting any data — that is the point of envelope encryption.
"""
from __future__ import annotations

import base64
import datetime as _dt
import json
import os
from typing import Any

from cryptography.fernet import Fernet


class _PayloadEncoder(json.JSONEncoder):
    """
    JSON encoder for payload dicts. Handles types that DRF likes to produce
    but stdlib json doesn't know:
      - datetime.date / datetime.datetime / datetime.time → ISO 8601 string
      - decimal.Decimal → str (preserves precision)
      - UUID → str
      - bytes (rare here) → base64
    """

    def default(self, o: Any) -> Any:  # type: ignore[override]
        if isinstance(o, _dt.datetime):
            return o.isoformat()
        if isinstance(o, _dt.date):
            return o.isoformat()
        if isinstance(o, _dt.time):
            return o.isoformat()
        from decimal import Decimal
        from uuid import UUID

        if isinstance(o, Decimal):
            return str(o)
        if isinstance(o, UUID):
            return str(o)
        if isinstance(o, bytes):
            return base64.b64encode(o).decode("ascii")
        return super().default(o)


def _master() -> Fernet:
    """
    Read the master key from the environment at call time.

    We deliberately do *not* read it from `django.conf.settings` — settings is
    captured at Django startup, which can race with test fixtures that set the
    env var. Reading os.environ here makes the resolution explicit and lazy.
    """
    key = os.environ.get("MASTER_KEK", "")
    if not key:
        raise RuntimeError("MASTER_KEK is not set")
    return Fernet(key.encode("ascii"))


def generate_dek() -> bytes:
    """Generate a fresh data encryption key (Fernet-formatted)."""
    return Fernet.generate_key()


def wrap_dek(dek: bytes) -> str:
    """Encrypt a DEK with the master KEK; return text suitable for DB storage."""
    return _master().encrypt(dek).decode("ascii")


def unwrap_dek(wrapped: str) -> bytes:
    """Inverse of `wrap_dek`."""
    return _master().decrypt(wrapped.encode("ascii"))


def encrypt_payload(dek: bytes, data: dict) -> str:
    raw = json.dumps(data, ensure_ascii=False, cls=_PayloadEncoder).encode("utf-8")
    return Fernet(dek).encrypt(raw).decode("ascii")


def decrypt_payload(dek: bytes, token: str) -> dict:
    raw = Fernet(dek).decrypt(token.encode("ascii"))
    return json.loads(raw)


def encrypt_text(dek: bytes, value: str | None) -> str | None:
    if value in (None, ""):
        return None
    assert value is not None
    return Fernet(dek).encrypt(value.encode("utf-8")).decode("ascii")


def decrypt_text(dek: bytes, token: str | None) -> str | None:
    if not token:
        return None
    return Fernet(dek).decrypt(token.encode("ascii")).decode("utf-8")


def random_bytes(n: int = 32) -> bytes:
    """Convenience for callers that want a non-Fernet random key."""
    return os.urandom(n)


def b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii")
