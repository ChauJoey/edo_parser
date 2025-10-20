import re
from typing import Iterator, List, Optional, Pattern

RegexPattern = str | Pattern


class RegexUtils:
    """Lightweight helpers that wrap Python's ``re`` module."""

    IGNORECASE = re.IGNORECASE
    MULTILINE = re.MULTILINE
    DOTALL = re.DOTALL
    VERBOSE = re.VERBOSE
    DEFAULT_FLAGS = re.IGNORECASE | re.MULTILINE

    @staticmethod
    def compile(pattern: str, flags: int = DEFAULT_FLAGS) -> Pattern:
        return re.compile(pattern, flags)

    @staticmethod
    def escape(text: str) -> str:
        return re.escape(text)

    @staticmethod
    def _ensure_pattern(pattern: RegexPattern, flags: int = DEFAULT_FLAGS) -> Pattern:
        if isinstance(pattern, re.Pattern):
            return pattern
        return re.compile(pattern, flags)

    @staticmethod
    def search(pattern: RegexPattern, text: str, *, flags: int = 0):
        rx = RegexUtils._ensure_pattern(pattern, flags)
        return rx.search(text or "")

    @staticmethod
    def match(pattern: RegexPattern, text: str, *, flags: int = 0):
        rx = RegexUtils._ensure_pattern(pattern, flags)
        return rx.match(text or "")

    @staticmethod
    def fullmatch(pattern: RegexPattern, text: str, *, flags: int = 0):
        rx = RegexUtils._ensure_pattern(pattern, flags)
        return rx.fullmatch(text or "")

    @staticmethod
    def finditer(pattern: RegexPattern, text: str, *, flags: int = 0) -> Iterator[re.Match]:
        rx = RegexUtils._ensure_pattern(pattern, flags)
        return rx.finditer(text or "")

    @staticmethod
    def split(pattern: RegexPattern, text: str, *, flags: int = 0, maxsplit: int = 0) -> List[str]:
        rx = RegexUtils._ensure_pattern(pattern, flags)
        return rx.split(text or "", maxsplit)

    @staticmethod
    def sub(pattern: RegexPattern, repl: str, text: str, *, flags: int = 0) -> str:
        rx = RegexUtils._ensure_pattern(pattern, flags)
        return rx.sub(repl, text or "")

    @staticmethod
    def find_first(text: str, pattern: RegexPattern, *, flags: int | None = None) -> Optional[str]:
        rx = RegexUtils._ensure_pattern(pattern, RegexUtils.DEFAULT_FLAGS if flags is None else flags)
        match = rx.search(text or "")
        return match.group(0).strip() if match else None

    @staticmethod
    def find_all(
        text: str,
        pattern: RegexPattern,
        *,
        flags: int | None = None,
        max_items: int | None = None,
    ) -> List[str]:
        rx = RegexUtils._ensure_pattern(pattern, RegexUtils.DEFAULT_FLAGS if flags is None else flags)
        out = [m.group(0).strip() for m in rx.finditer(text or "")]
        return out[:max_items] if max_items else out

    @staticmethod
    def extract_between(text: str, prefix: str, suffix: str, greedy: bool = False) -> Optional[str]:
        pat = RegexUtils.escape(prefix) + (r"(.*)" if greedy else r"(.*?)") + RegexUtils.escape(suffix)
        match = RegexUtils.search(pat, text or "", flags=RegexUtils.IGNORECASE | RegexUtils.DOTALL)
        return match.group(1).strip() if match else None

    @staticmethod
    def after(text: str, anchor: str, pattern: str, max_chars: int = 200) -> Optional[str]:
        i = (text or "").lower().find(anchor.lower())
        if i < 0:
            return None
        window = (text or "")[i:i + max_chars]
        match = RegexUtils.search(pattern, window, flags=RegexUtils.IGNORECASE)
        return match.group(0).strip() if match else None

    @staticmethod
    def iso_container_candidates(text: str) -> List[str]:
        pat = r"\b([A-Z]{4})\s*([0-9]{7})\b"
        rx = RegexUtils.compile(pat, flags=RegexUtils.IGNORECASE)
        out: List[str] = []
        for match in rx.finditer(text or ""):
            out.append((match.group(1) + match.group(2)).upper())
        seen, dedup = set(), []
        for container in out:
            if container not in seen:
                seen.add(container)
                dedup.append(container)
        return dedup
