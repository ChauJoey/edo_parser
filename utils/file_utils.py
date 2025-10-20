import os
import shutil
from typing import Tuple

class FileUtils:
    @staticmethod
    def _split_name_ext(name: str) -> Tuple[str, str]:
        base, ext = os.path.splitext(name)
        return base, ext or ".pdf"

    @staticmethod
    def safe_rename(old_path: str, target_name: str, dest_folder: str | None = None) -> str:
        """
        在同一目录下安全重命名：
        - 如果目标文件已存在，自动追加 (-1), (-2) ... 避免覆盖
        - 返回新路径
        """
        folder = dest_folder or os.path.dirname(old_path)
        os.makedirs(folder, exist_ok=True)
        base, ext = FileUtils._split_name_ext(target_name)
        candidate = os.path.join(folder, f"{base}{ext}")
        idx = 1
        while os.path.exists(candidate):
            candidate = os.path.join(folder, f"{base}-({idx}){ext}")
            idx += 1
        if os.path.abspath(candidate) == os.path.abspath(old_path):
            return candidate
        shutil.copy2(old_path, candidate)
        return candidate
