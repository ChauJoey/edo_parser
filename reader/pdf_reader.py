from __future__ import annotations

from typing import List
import fitz  # PyMuPDF


class PDFReader:
    """Encapsulates PDF → text extraction.
    Upper layers call .read(...) or .read_bytes(...) and receive plain text only.
    """

    def read(self, file_path: str) -> str:
        """Read text from a local PDF file path."""
        try:
            with fitz.open(file_path) as doc:
                return self._extract_text_from_doc(doc)
        except Exception as e:
            print(f"[ERROR] Failed to read PDF from path: {e}")
            return ""

    def read_bytes(self, data: bytes) -> str:
        """Read text from in-memory PDF bytes (e.g., downloaded via DriveApp)."""
        try:
            if not data:
                print("[ERROR] Empty PDF data.")
                return ""
            # filetype 必须给 "pdf"，否则 PyMuPDF 不能正确识别
            with fitz.open(stream=data, filetype="pdf") as doc:
                return self._extract_text_from_doc(doc)
        except Exception as e:
            print(f"[ERROR] Failed to read PDF from bytes: {e}")
            return ""

    # ---------------- internal helpers ----------------

    @staticmethod
    def _extract_text_from_doc(doc: "fitz.Document") -> str:
        """Extract text from a fitz.Document, one page at a time."""
        buf: List[str] = []
        for page in doc:
            # 也可用 page.get_text("text")；默认等价
            buf.append(page.get_text())
        # 去掉单页末尾换行再合并，保持原有返回习惯
        return "\n".join(s.strip("\n") for s in buf).strip()
