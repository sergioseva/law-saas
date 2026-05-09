"""
Storage abstraction.

Two implementations:
  - LocalStorage: writes to settings.MEDIA_ROOT (dev / single-host deploys).
  - R2Storage: S3-compatible via boto3 (production).

Selection is automatic — if R2 credentials are configured, use R2; else local.

The interface is intentionally narrow: save / open / delete / size. URLs are
not part of the interface — the API streams downloads through Django, which
keeps the dev and prod behavior identical from the client's point of view.
Add presigned-URL support as a Phase 5 optimization once we have measurable
egress costs to optimize against.
"""
from __future__ import annotations

from .base import FileNotFoundInStorage, Storage
from .factory import get_storage

__all__ = ["FileNotFoundInStorage", "Storage", "get_storage"]
