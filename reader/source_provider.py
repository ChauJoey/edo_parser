import os
from pathlib import Path
from typing import Iterator


class SourceProvider:
    """统一的文件来源提供器：相对路径自动以“项目根目录”为基准解析。
    项目根目录 = 本文件所在目录的上一层（.../edo_parser）
    """

    def __init__(self, source: str, *, create_if_missing: bool = False):
        """
        source 可以是：
        - 相对路径：'input'  -> 解析为 <项目根>/input
        - 绝对路径：'C:/Users/...'
        - （预留）协议：'gdrive://folder_id' —— 以后扩展
        """
        self.folder = self._resolve_to_project_root(source)
        if not self.folder.exists():
            if create_if_missing:
                self.folder.mkdir(parents=True, exist_ok=True)
            else:
                raise FileNotFoundError(f"Source folder not found: {self.folder}")

    def iter_pdfs(self) -> Iterator[str]:
        """返回所有 PDF 文件的绝对路径（按文件名排序）"""
        # 仅遍历文件（不进子目录）；忽略隐藏文件
        for p in sorted(self.folder.iterdir(), key=lambda x: x.name.lower()):
            if not p.is_file():
                continue
            if p.name.startswith("."):
                continue
            if p.suffix.lower() == ".pdf":
                yield str(p.resolve())

    # ── helpers ────────────────────────────────────────────────────────────
    @staticmethod
    def _project_root() -> Path:
        # 当前文件：.../reader/source_provider.py
        # 项目根：parent.parent
        return Path(__file__).resolve().parent.parent

    @classmethod
    def _resolve_to_project_root(cls, source: str) -> Path:
        # 展开用户目录与环境变量，如 "~"、"%USERPROFILE%"
        raw = Path(os.path.expandvars(os.path.expanduser(source)))
        if raw.is_absolute():
            return raw.resolve()
        # 相对路径：以项目根目录为基准
        return (cls._project_root() / raw).resolve()
