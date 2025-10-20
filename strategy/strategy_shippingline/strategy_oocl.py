from typing import Dict, List

from utils.regex_utils import RegexUtils
from utils.text_utils import TextUtils
from ..base_strategy import BaseStrategy


class OOCLStrategy(BaseStrategy):
    """Strategy dedicated to extracting OOCL delivery order details."""

    name = "OOCL"
    keywords = ["AGENT OOCL", "OOCL", "ORIENT OVERSEAS"]

    _PIN_PATTERNS: List[str] = [
        r"EMPTY RELEASE PIN(?: NUMBER)?\s*[:\-]?\s*(?P<value>[A-Z0-9]{4,12})",
        r"PICK[\s\-]*UP PIN\s*[:\-]?\s*(?P<value>[A-Z0-9]{4,12})",
        r"PIN(?: NUMBER)?\s*[:\-]?\s*(?P<value>[A-Z0-9]{4,12})",
    ]
    _YARD_PATTERNS: List[str] = [
        r"EMPTY RETURN (?:LOCATION|DEPOT)\s*[:\-]?\s*(?P<value>[\sA-Z0-9 \-/&,()]{3,200})",
        r"EMPTY RETURN TO\s*[:\-]?\s*(?P<value>[\sA-Z0-9 \-/&,()]{3,200})",
        r"RETURN LOCATION\s*[:\-]?\s*(?P<value>[\sA-Z0-9 \-/&,()]{3,200})",
    ]
    _YARD_STOP_PREFIXES: List[str] = [
        "CONTACT",
        "REMARK",
        "PIN",
        "EMPTY RETURN",
        "VESSEL",
    ]

    def match(self, text: str) -> bool:
        t = (text or "").upper()
        return any(k in t for k in (k.upper() for k in self.keywords))

    @staticmethod
    def _match_first(text: str, patterns: List[str], flags: int = RegexUtils.IGNORECASE | RegexUtils.MULTILINE) -> str:
        source = text or ""
        for pattern in patterns:
            rx = RegexUtils.compile(pattern, flags)
            match = rx.search(source)
            if not match:
                continue
            if "value" in match.groupdict():
                return match.group("value").strip()
            if match.groups():
                return match.group(1).strip()
            return match.group(0).strip()
        return ""

    def _extract_pin(self, text: str) -> str:
        pin = self._match_first(text, self._PIN_PATTERNS)
        if not pin:
            pin = RegexUtils.after(text, "PIN", r"[A-Z0-9]{4,12}") or ""
        return pin

    def _sanitize_yard_block(self, block: str) -> str:
        cleaned: List[str] = []
        for raw_line in (block or "").splitlines():
            stripped = raw_line.strip()
            if not stripped:
                break
            upper = stripped.upper()
            if any(upper.startswith(prefix) for prefix in self._YARD_STOP_PREFIXES):
                break
            cleaned.append(stripped)
        return "\n".join(cleaned).strip()

    def _collect_yard_lines(self, text: str, anchor: str) -> str:
        upper_text = (text or "").upper()
        idx = TextUtils.find_first_index(upper_text, anchor.upper())
        if idx is None:
            return ""

        tail = (text or "")[idx:].splitlines()
        if not tail:
            return ""

        collected: List[str] = []
        for raw_line in tail[1:]:
            stripped = raw_line.strip()
            if not stripped:
                break
            upper = stripped.upper()
            if any(upper.startswith(prefix) for prefix in self._YARD_STOP_PREFIXES):
                break
            collected.append(stripped)
            if len(collected) >= 6:
                break
        return "\n".join(collected).strip()

    def _extract_yard(self, text: str) -> str:
        yard = self._match_first(text, self._YARD_PATTERNS, flags=RegexUtils.IGNORECASE | RegexUtils.MULTILINE | RegexUtils.DOTALL)
        yard = self._sanitize_yard_block(yard)
        if yard:
            return yard

        between = RegexUtils.extract_between(text, "EMPTY RETURN LOCATION", "REMARKS")
        yard = self._sanitize_yard_block(between)
        if yard:
            return yard

        yard = self._collect_yard_lines(text, "EMPTY RETURN LOCATION")
        if yard:
            return yard

        fallback = RegexUtils.after(text, "EMPTY RETURN LOCATION", r"[A-Z0-9 \-/&,()]{3,80}") or ""
        return TextUtils.collapse_spaces(fallback)

    def extract(self, text: str) -> List[Dict[str, str]]:
        containers = RegexUtils.iso_container_candidates(text)
        pin = self._extract_pin(text)
        yard_raw = self._extract_yard(text)
        yard = TextUtils.collapse_spaces(yard_raw)
        if yard:
            yard = RegexUtils.split(r"\b(CONTACT|REMARKS?)\b", yard, flags=RegexUtils.IGNORECASE, maxsplit=1)[0].strip()

        results: List[Dict[str, str]] = []
        for container in containers:
            results.append(
                {
                    "Shipping Line": self.name,
                    "\u67dc\u53f7": container,
                    "PIN": pin,
                    "\u8fd8\u67dc\u573a": yard,
                }
            )
        return results
