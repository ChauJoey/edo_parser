import os
from typing import List, Optional
from reader.pdf_reader import PDFReader
from reader.source_provider import SourceProvider
from extractor.strategy_factory import get_matching_strategy
from extractor.normalizer import Normalizer
from utils.file_utils import FileUtils


class WorkflowManager:
    """Tiny, readable workflow: one loop + one file processor.
    - No third‑party in workflow layer
    - All details delegated to reader/strategy/normalizer/utils
    - Optional verbose logs kept minimal
    """

    def __init__(self, source: str, *, output: str = "output", verbose: bool = True):
        self.source = SourceProvider(source)
        self.reader = PDFReader()
        self.verbose = verbose
        self.output_folder = SourceProvider._resolve_to_project_root(output)
        self.output_folder.mkdir(parents=True, exist_ok=True)

    # ── Public API ──────────────────────────────────────────────────────────
    def run(self) -> None:
        for path in self.source.iter_pdfs():
            new_path = self.process_file(path)
            if self.verbose:
                if new_path:
                    print(f"[OK] {os.path.basename(path)} → {os.path.basename(new_path)}")
                else:
                    print(f"[SKIP] {os.path.basename(path)}")

    def process_file(self, file_path: str) -> Optional[str]:
        """Process a single PDF and return the new path if renamed."""
        text = self.reader.read(file_path)

        # print(text) #test

        if not text:
            return None

        strategy = get_matching_strategy(text)

        records = strategy.extract(text)
        if not records:
            return None

        normalized = Normalizer.apply(records)
        if self.verbose:
            print(f"[RECORDS:NORM] {os.path.basename(file_path)} → {normalized}")

        containers = self._unique([r.get("柜号", "").strip() for r in normalized if r.get("柜号")])
        if not containers:
            return None

        target = f"{containers[0]}.pdf" if len(containers) == 1 else f"{containers[0]}_multi.pdf"

        return FileUtils.safe_rename(file_path, target, dest_folder=str(self.output_folder))

    # ── Small helpers ──────────────────────────────────────────────────────
    @staticmethod
    def _pdfs_in(folder: str) -> List[str]:
        for name in os.listdir(folder):
            if name.lower().endswith(".pdf"):
                yield os.path.join(folder, name)

    @staticmethod
    def _unique(items: List[str]) -> List[str]:
        seen, out = set(), []
        for x in items:
            if x and x not in seen:
                seen.add(x)
                out.append(x)
        return out

if __name__ == "__main__":
    wf = WorkflowManager(source="input", output="output", verbose=True)
    wf.run()
