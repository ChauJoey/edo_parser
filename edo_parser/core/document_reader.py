from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DocumentContent:
    """Represents the raw textual content extracted from a document."""

    text: str
    source: Path


class DocumentReadError(RuntimeError):
    """Raised when a document cannot be read or parsed."""


class DocumentReader(ABC):
    """Base contract for document readers."""

    @abstractmethod
    def read(self, source: Path) -> DocumentContent:
        """Extract raw text from the given document path."""

    @abstractmethod
    def supports(self, source: Path) -> bool:
        """Return True when the reader can handle the given file."""
