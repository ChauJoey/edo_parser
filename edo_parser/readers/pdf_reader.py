from __future__ import annotations

from pathlib import Path

from edo_parser.core.document_reader import DocumentContent, DocumentReadError, DocumentReader
from edo_parser.infrastructure.pdf_text_extractor import PdfExtractionError, PdfTextExtractor


class PdfDocumentReader(DocumentReader):
    """Reads textual content from PDF files."""

    def __init__(self, extractor: PdfTextExtractor | None = None):
        self._extractor = extractor or PdfTextExtractor()

    def supports(self, source: Path) -> bool:
        return source.suffix.lower() == ".pdf"

    def read(self, source: Path) -> DocumentContent:
        if not source.exists():
            raise DocumentReadError(f"PDF file not found: {source}")
        if not source.is_file():
            raise DocumentReadError(f"Path is not a file: {source}")

        try:
            text = self._extractor.extract_text(source)
        except PdfExtractionError as exc:
            raise DocumentReadError(str(exc)) from exc

        return DocumentContent(text=text, source=source)
