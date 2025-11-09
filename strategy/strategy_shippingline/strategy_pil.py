from typing import Dict, List, Optional
from utils.port_utils import PortExtractor

from utils.regex_utils import RegexUtils
from utils.text_utils import TextUtils
from ..base_strategy import BaseStrategy


class PILStrategy(BaseStrategy):
    """Extraction strategy for Pacific International Lines delivery orders."""

    name = "PIL"
    keywords = [
        "PACIFIC INTERNATIONAL LINES",
        "PIL AUSTRALIA",
        "PILSHIP.COM.AU",
    ]

    _PIN_PATTERNS: List[str] = [
        r"\bPIN(?: NUMBER)?\s*[:\-]?\s*(?P<value>(?=[A-Z0-9]*\d)[A-Z0-9]{4,16})",
    ]
    _YARD_STOP_PREFIXES: List[str] = [
        "STATUS",
        "TERMS & CONDITIONS",
        "DELIVERY ORDER",
        "ISSUED BY",
        "GOODS DETAILS",
        "ITEM NO",
    ]
    _PIN_RX = RegexUtils.compile(r"(?=[A-Z0-9]*\d)[A-Z0-9]{4,16}", flags=RegexUtils.IGNORECASE)

    def match(self, text: str) -> bool:
        t = (text or "").upper()
        return any(k in t for k in (k.upper() for k in self.keywords))

    def extract(self, text: str) -> List[Dict[str, str]]:
        containers = RegexUtils.iso_container_candidates(text)
        if not containers:
            return []
        pin = self._extract_pin(text)
        yard = TextUtils.collapse_spaces(self._extract_yard(text))


        port = PortExtractor.extract(text)

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
        for record in results:
            record.setdefault("Port of Discharge", port)
            record.setdefault("\u505c\u9760\u7801\u5934", port)
        return results

    def _extract_pin(self, text: str) -> str:
        pin = self._match_first(text)
        if pin:
            return pin

        lines = [(line or "").strip() for line in (text or "").splitlines()]
        for idx, raw in enumerate(lines):
            if not raw:
                continue
            upper = raw.upper()
            if not upper.startswith("PIN"):
                continue
            in_line = self._PIN_RX.search(raw)
            if in_line:
                return in_line.group(0).upper()
            next_value = self._next_value(lines, idx + 1)
            if next_value:
                return next_value
        return ""

    def _match_first(self, text: str) -> str:
        for pattern in self._PIN_PATTERNS:
            m = RegexUtils.search(pattern, text or "", flags=RegexUtils.IGNORECASE | RegexUtils.MULTILINE)
            if not m:
                continue
            groups = m.groupdict()
            candidate = (groups.get("value") or m.group(0)).strip().upper()
            if self._PIN_RX.fullmatch(candidate):
                return candidate
        return ""

    def _next_value(self, lines: List[str], start: int) -> str:
        for look_ahead in range(start, min(start + 12, len(lines))):
            candidate = lines[look_ahead].strip()
            if not candidate:
                continue
            if candidate.endswith(":"):
                continue
            if self._PIN_RX.fullmatch(candidate):
                return candidate.upper()
        return ""

    def _extract_yard(self, text: str) -> str:
        lines = [(line or "").strip() for line in (text or "").splitlines()]
        start_index: Optional[int] = None
        for idx, raw in enumerate(lines):
            if raw.upper().startswith("PLACE OF EMPTY RETURN"):
                start_index = idx + 1
                break
        if start_index is None:
            return ""

        collected: List[str] = []
        for raw in lines[start_index:]:
            stripped = raw.strip()
            if not stripped:
                if collected:
                    break
                continue
            upper = stripped.upper()
            if any(upper.startswith(prefix) for prefix in self._YARD_STOP_PREFIXES):
                break
            collected.append(stripped)
        return "\n".join(collected).strip()