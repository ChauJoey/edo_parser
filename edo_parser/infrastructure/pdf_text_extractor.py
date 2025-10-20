from __future__ import annotations

from pathlib import Path
from typing import Protocol


class PdfExtractionError(RuntimeError):
    """Raised when the underlying PDF toolkit fails to extract text."""


class PdfBackend(Protocol):
    def extract_text(self, source: Path) -> str:  # pragma: no cover - interface definition
        ...


class PdfTextExtractor:
    """Extracts text from PDF files using an injected backend."""

    def __init__(self, backend: PdfBackend | None = None):
        self._backend = backend or _PyPdfBackend()

    def extract_text(self, source: Path) -> str:
        path = Path(source)
        try:
            text = self._backend.extract_text(path)
        except PdfExtractionError:
            raise
        except Exception as exc:  # pragma: no cover - defensive guard
            raise PdfExtractionError(f"Unexpected error while reading PDF: {path}") from exc
        if not text:
            raise PdfExtractionError(f"PDF appears empty: {path}")
        return text


class _PyPdfBackend:
    """Thin wrapper around PyPDF2 so the rest of the app never touches it directly."""

    def extract_text(self, source: Path) -> str:
        try:
            from PyPDF2 import PdfReader  # type: ignore import-not-found
        except ImportError as exc:  # pragma: no cover - runtime dependency check
            raise PdfExtractionError(
                "PyPDF2 is required to read PDF files. Install it via `pip install PyPDF2`."
            ) from exc

        try:
            with source.open("rb") as stream:
                reader = PdfReader(stream, strict=False)
                contents: list[str] = []
                for index, page in enumerate(reader.pages):
                    try:
                        page_text = page.extract_text() or ""
                    except Exception as exc:  # pragma: no cover - PyPDF2 specific path
                        raise PdfExtractionError(
                            f"Failed to extract text from page {index} in {source}"
                        ) from exc
                    contents.append(page_text.strip())
        except OSError as exc:
            raise PdfExtractionError(f"Cannot open PDF file: {source}") from exc

        return "\n".join(part for part in contents if part)
