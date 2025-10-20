"""EDO parser package."""

from edo_parser.readers.factory import DocumentReaderFactory
from edo_parser.readers.pdf_reader import PdfDocumentReader

__all__ = ["DocumentReaderFactory", "PdfDocumentReader"]
