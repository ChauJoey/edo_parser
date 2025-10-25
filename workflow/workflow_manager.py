from __future__ import annotations

import re
from typing import List, Optional

from extractor.normalizer import Normalizer
from extractor.strategy_factory import get_matching_strategy
from google_base.GoogleDrive.DriveApp import DriveApp, DriveFile
from reader.pdf_reader import PDFReader


class WorkflowManager:
    """EDO workflow implemented purely with DriveApp (no local file handling)."""

    def __init__(self, source: Optional[str] = None, *, verbose: bool = True):
        """
        Args:
            source: Optional Google Drive folder (URL, gdrive://ID, or raw ID).
                When omitted the default Input folder from GoogleConfig is used.
            verbose: Whether to print progress logs.
        """
        self.reader = PDFReader()
        self.drive_app = DriveApp()
        self.verbose = verbose
        self._source_folder_id = self._normalize_source(source)

    def run(self) -> None:
        files = self._list_source_files()
        for drive_file in files:
            data = self.drive_app.download_file_bytes(drive_file.id)
            new_name = self.process_file(drive_file, data)
            if self.verbose:
                if new_name:
                    print(f"[OK] {drive_file.name} -> {new_name}")
                else:
                    print(f"[SKIP] {drive_file.name}")

    def process_file(self, drive_file: DriveFile, data: bytes) -> Optional[str]:
        """Process a single Drive PDF and return the new remote name if moved."""
        text = self.reader.read_bytes(data)
        if not text:
            return None

        strategy = get_matching_strategy(text)
        records = strategy.extract(text)
        if not records:
            return None

        normalized = Normalizer.apply(records)
        preview_link = self._build_file_view_url(drive_file.id)
        for entry in normalized:
            entry["file_view_url"] = preview_link
        if self.verbose:
            print(f"[RECORDS:NORM] {drive_file.name} -> {normalized}")

        containers = self._unique(
            [r.get("柜号", "").strip() for r in normalized if r.get("柜号")]
        )
        if not containers:
            return None

        target = f"{'_'.join(containers)}.pdf"
        success = self._move_to_output(drive_file.id, target)
        if success:
            return target

        # fallback to Fail folder naming
        fail_name = f"[FAIL]{target}"
        self._move_to_fail(drive_file.id, fail_name)
        return None


    # ---------- helpers ----------

    def _list_source_files(self) -> List[DriveFile]:
        if self._source_folder_id:
            return self.drive_app.list_files_in_folder(
                self._source_folder_id, mime_type="application/pdf"
            )
        return self.drive_app.list_input_files()

    @staticmethod
    def _unique(items: List[str]) -> List[str]:
        seen, out = set(), []
        for x in items:
            if x and x not in seen:
                seen.add(x)
                out.append(x)
        return out

    def _move_to_output(self, file_id: str, target_name: str) -> bool:
        try:
            self.drive_app.move_to_output(file_id, rename_to=target_name)
            return True
        except Exception as exc:
            print(f"[WARN] Failed to move '{target_name}' to Output: {exc}")
            return False

    def _move_to_fail(self, file_id: str, target_name: str) -> None:
        try:
            self.drive_app.move_to_fail(file_id, rename_to=target_name)
        except Exception as exc:
            print(f"[WARN] Failed to move '{target_name}' to Fail: {exc}")

    @staticmethod
    def _build_file_view_url(file_id: str) -> str:
        return f"https://drive.google.com/file/d/{file_id}/view"

    def _normalize_source(self, source: Optional[str]) -> Optional[str]:
        if not source:
            return None
        source = source.strip()
        if not source:
            return None
        if source.startswith("gdrive://"):
            return source[len("gdrive://"):].strip()
        if "drive.google.com" in source:
            drive_id = self._extract_drive_id_from_url(source)
            if drive_id:
                return drive_id
        if self._looks_like_drive_id(source):
            return source
        raise ValueError("Source must be a Google Drive folder ID or URL.")

    @staticmethod
    def _looks_like_drive_id(value: str) -> bool:
        return bool(re.fullmatch(r"[a-zA-Z0-9_-]+", value))

    @staticmethod
    def _extract_drive_id_from_url(source: str) -> Optional[str]:
        patterns = [
            r"/folders/([a-zA-Z0-9\-_]+)",
            r"/file/d/([a-zA-Z0-9\-_]+)",
            r"[?&]id=([a-zA-Z0-9\-_]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, source)
            if match:
                return match.group(1)
        tail = source.rstrip("/").split("/")[-1]
        return tail or None


if __name__ == "__main__":
    WorkflowManager(verbose=True).run()
