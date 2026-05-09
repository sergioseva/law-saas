from __future__ import annotations

from abc import ABC, abstractmethod
from typing import BinaryIO


class FileNotFoundInStorage(Exception):
    """Raised when a stored_key has no corresponding object."""


class Storage(ABC):
    """Minimal blob-storage interface — see storage/__init__.py for rationale."""

    @abstractmethod
    def save(self, key: str, fileobj: BinaryIO, *, content_type: str) -> int:
        """Persist `fileobj` at `key`. Returns the number of bytes written."""

    @abstractmethod
    def open(self, key: str) -> BinaryIO:
        """Open a stored object for reading. Raises FileNotFoundInStorage if absent."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remove a stored object. Idempotent — no error if already gone."""

    @abstractmethod
    def exists(self, key: str) -> bool: ...
