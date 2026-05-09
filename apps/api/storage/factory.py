from __future__ import annotations

from functools import lru_cache

from django.conf import settings

from .base import Storage


@lru_cache(maxsize=1)
def get_storage() -> Storage:
    """Return the configured Storage backend.

    Picks R2Storage if R2 credentials are present, else LocalStorage.
    Cached for the process lifetime — call clear_cache() in tests if needed.
    """
    if getattr(settings, "R2_ACCESS_KEY_ID", "") and getattr(settings, "R2_BUCKET", ""):
        from .r2 import R2Storage

        return R2Storage()

    from .local import LocalStorage

    return LocalStorage()


def reset_storage_cache() -> None:
    get_storage.cache_clear()
