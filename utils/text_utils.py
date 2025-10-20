import re
from typing import Optional

class TextUtils:
    @staticmethod
    def collapse_spaces(s: str) -> str:
        """压缩多余空格"""
        return re.sub(r"\s+", " ", s or "").strip()

    @staticmethod
    def keep_lines(s: str, start: int, end: int) -> str:
        """截取指定行范围 [start, end)"""
        lines = (s or "").splitlines()
        start = max(0, start)
        end = min(len(lines), max(start, end))
        return "\n".join(lines[start:end])

    @staticmethod
    def slice_around(text: str, pos: int, ctx: int = 60) -> str:
        """返回位置 pos 前后 ctx 个字符，便于调试上下文"""
        pos = max(0, min(len(text), pos))
        return text[max(0, pos-ctx):min(len(text), pos+ctx)]

    @staticmethod
    def normalize_upper_no_space(s: str) -> str:
        """去空格并大写化"""
        return re.sub(r"\s+", "", (s or "").upper())

    @staticmethod
    def find_first_index(text: str, needle: str) -> Optional[int]:
        """返回 needle 首次出现的索引"""
        i = (text or "").find(needle)
        return i if i >= 0 else None
