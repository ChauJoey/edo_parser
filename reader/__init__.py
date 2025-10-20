"""
Reader package: provides text extraction from source files (PDF, images, etc.).
Exposes a unified interface so upper layers never import third-party libs.
"""

from .pdf_reader import PDFReader  # noqa: F401
from .source_provider import SourceProvider  # noqa: F401