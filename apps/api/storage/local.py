from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

from django.conf import settings

from .base import FileNotFoundInStorage, Storage


class LocalStorage(Storage):
    """File-system backend rooted at settings.MEDIA_ROOT."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root or settings.MEDIA_ROOT)

    def _path(self, key: str) -> Path:
        # Reject any traversal attempt — keys are firm-namespaced.
        key = key.lstrip("/")
        if ".." in Path(key).parts:
            raise ValueError(f"Invalid storage key: {key!r}")
        return self.root / key

    def save(self, key: str, fileobj: BinaryIO, *, content_type: str) -> int:
        del content_type  # local FS doesn't track this
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        bytes_written = 0
        with path.open("wb") as out:
            while chunk := fileobj.read(64 * 1024):
                out.write(chunk)
                bytes_written += len(chunk)
        return bytes_written

    def open(self, key: str) -> BinaryIO:
        path = self._path(key)
        if not path.exists():
            raise FileNotFoundInStorage(key)
        return path.open("rb")

    def delete(self, key: str) -> None:
        path = self._path(key)
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        # Best-effort: prune empty parent dirs up to root, ignore failures.
        parent = path.parent
        while parent != self.root and parent.exists():
            try:
                parent.rmdir()
            except OSError:
                break
            parent = parent.parent

    def exists(self, key: str) -> bool:
        return self._path(key).exists()


__all__ = ["LocalStorage"]


# Helper exposed for the tests + CLI inspection.
def list_keys() -> list[str]:
    root = Path(settings.MEDIA_ROOT)
    if not root.exists():
        return []
    return [
        str(p.relative_to(root))
        for p in root.rglob("*")
        if p.is_file()
    ]
