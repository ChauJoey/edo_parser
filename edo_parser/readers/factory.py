from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from edo_parser.core.document_reader import DocumentContent, DocumentReadError, DocumentReader


class DocumentReaderFactory:
    """Selects an appropriate reader for a given document."""

    def __init__(self, readers: Iterable[DocumentReader]):
        self._readers: List[DocumentReader] = list(readers)

    def register(self, reader: DocumentReader) -> None:
        if reader not in self._readers:
            self._readers.append(reader)

    def get_reader(self, source: Path) -> DocumentReader:
        for reader in self._readers:
            if reader.supports(source):
                return reader
        raise DocumentReadError(f"No reader available for file: {source}")

    def read(self, source: Path) -> DocumentContent:
        reader = self.get_reader(source)
        return reader.read(source)
