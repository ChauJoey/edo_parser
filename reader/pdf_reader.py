import fitz  # PyMuPDF

class PDFReader:
    """Encapsulates PDF → text extraction.
    Upper layers call .read(...) and receive plain text only.
    """

    def read(self, file_path: str) -> str:
        try:
            with fitz.open(file_path) as doc:
                buf = []
                for page in doc:
                    buf.append(page.get_text())
            return "\n".join(s.strip("\n") for s in buf).strip()
        except Exception as e:
            print(f"[ERROR] Failed to read PDF: {e}")
            return ""
