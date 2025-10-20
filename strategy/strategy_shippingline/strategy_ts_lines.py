from typing import Dict, List

from utils.regex_utils import RegexUtils
from utils.text_utils import TextUtils
from ..base_strategy import BaseStrategy


class TSLINEStrategy(BaseStrategy):
    """Extraction strategy for T.S. Lines delivery orders."""

    name = "TS LINES"
    keywords = [
        "T.S. LINES",
        "TS LINES",
        "TSL - IMPORT DELIVERY ORDER",
    ]

    _TABLE_HEADERS = [
        "CONTAINER NO.",
        "PIN",
        "TYPE",
        "REEFER",
        "HAZ/DG",
        "SEAL",
        "WEIGHT",
        "EMPTY RETURN",
    ]

    _PIN_RX = RegexUtils.compile(r"(?=[A-Z0-9]*\d)[A-Z0-9]{4,16}", flags=RegexUtils.IGNORECASE)

    def match(self, text: str) -> bool:
        t = (text or "").upper()
        return any(k in t for k in (k.upper() for k in self.keywords))

    def extract(self, text: str) -> List[Dict[str, str]]:
        table = self._parse_table(text)
        containers = RegexUtils.iso_container_candidates(text)

        container = table.get("CONTAINER NO.") or (containers[0] if containers else "")
        pin = table.get("PIN") or self._fallback_pin(text)
        yard = table.get("EMPTY RETURN", "")

        container = (container or "").upper()
        if not container:
            return []

        pin = pin.upper() if pin else ""
        yard = TextUtils.collapse_spaces(yard)

        return [
            {
                "Shipping Line": self.name,
                "\u67dc\u53f7": container,
                "PIN": pin,
                "\u8fd8\u67dc\u573a": yard,
            }
        ]

    def _parse_table(self, text: str) -> Dict[str, str]:
        lines = [(line or "").strip() for line in (text or "").splitlines()]
        header_indices = []
        for idx, raw in enumerate(lines):
            if raw.upper() == self._TABLE_HEADERS[0]:
                header_indices.append(idx)
        for start in header_indices:
            if self._headers_match(lines, start):
                values = self._collect_values(lines, start + len(self._TABLE_HEADERS))
                if values:
                    return {header: values.get(header, "") for header in self._TABLE_HEADERS}
        return {}

    def _headers_match(self, lines: List[str], start: int) -> bool:
        for offset, header in enumerate(self._TABLE_HEADERS):
            idx = start + offset
            if idx >= len(lines):
                return False
            if lines[idx].upper() != header:
                return False
        return True

    def _collect_values(self, lines: List[str], start: int) -> Dict[str, str]:
        values: Dict[str, str] = {}
        collected: List[str] = []
        for raw in lines[start:]:
            if len(collected) >= len(self._TABLE_HEADERS):
                break
            stripped = raw.strip()
            if not stripped:
                continue
            collected.append(stripped)
        for header, value in zip(self._TABLE_HEADERS, collected):
            values[header] = value
        return values

    def _fallback_pin(self, text: str) -> str:
        match = RegexUtils.search(
            r"\bPIN\s*[:\-]?\s*(?P<value>(?=[A-Z0-9]*\d)[A-Z0-9]{4,16})",
            text or "",
            flags=RegexUtils.IGNORECASE,
        )
        if match:
            candidate = match.group("value").upper()
            if self._PIN_RX.fullmatch(candidate):
                return candidate
        return ""
