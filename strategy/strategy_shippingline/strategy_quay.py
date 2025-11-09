from typing import Dict, List, Optional, Tuple
from utils.port_utils import PortExtractor

from utils.regex_utils import RegexUtils
from utils.text_utils import TextUtils
from ..base_strategy import BaseStrategy


class QUAYStrategy(BaseStrategy):
    """Extraction strategy for Quay Shipping delivery orders (Yang Ming)."""

    name = "QUAY"
    keywords = [
        "QUAY SHIPPING",
        "QUAY-SHIPPING",
        "QUAY SHIPPING AUSTRALIA",
    ]

    _CONTAINER_RX = RegexUtils.compile(r"^CONTAINER\s*[:\-]?\s*([A-Z]{4}\d{7})$", flags=RegexUtils.IGNORECASE)
    _PIN_RX = RegexUtils.compile(r"^PIN(?: NUMBER)?\s*[:\-]?\s*([A-Z0-9]{4,12})$", flags=RegexUtils.IGNORECASE)
    _YARD_PATTERNS: List[str] = [
        r"EMPTY CONTAINER TO BE RETURNED TO\s*[:\-]?\s*(?P<value>[\sA-Z0-9'&,./()-]{3,200})",
        r"EMPTY RETURN (?:LOCATION|DEPOT)\s*[:\-]?\s*(?P<value>[\sA-Z0-9'&,./()-]{3,200})",
    ]
    _YARD_STOP_PREFIXES: List[str] = [
        "TYPE",
        "SEAL",
        "GENRL",
        "HAZARD",
        "REEFER",
        "PACKS",
        "GOODS DESCRIPTION",
        "SIGNATURE",
        "FOR TERMINAL USE ONLY",
        "CONTAINER OR SEAL RECEIVED DAMAGED",
        "DETENTION CHARGES",
    ]

    def match(self, text: str) -> bool:
        t = (text or "").upper()
        return any(k in t for k in (k.upper() for k in self.keywords))

    @staticmethod
    def _match_first(text: str, patterns: List[str], flags: int = RegexUtils.IGNORECASE | RegexUtils.MULTILINE) -> str:
        src = text or ""
        for pattern in patterns:
            rx = RegexUtils.compile(pattern, flags)
            match = rx.search(src)
            if not match:
                continue
            groups = match.groupdict()
            if "value" in groups:
                return groups["value"].strip()
            if match.groups():
                return match.group(1).strip()
            return match.group(0).strip()
        return ""

    def extract(self, text: str) -> List[Dict[str, str]]:
        pairs = self._extract_container_pin_pairs(text)
        if not pairs:
            containers = RegexUtils.iso_container_candidates(text)
            if not containers:
                return []
            pin = self._fallback_pin(text)
            pairs = [(container, pin) for container in containers]

        yard = TextUtils.collapse_spaces(self._extract_yard(text))


        port = PortExtractor.extract(text)

        results: List[Dict[str, str]] = []
        for container, pin in pairs:
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

    def _extract_container_pin_pairs(self, text: str) -> List[Tuple[str, str]]:
        pairs: List[Tuple[str, str]] = []
        pending_container: Optional[str] = None

        for raw in (text or "").splitlines():
            stripped = raw.strip()
            if not stripped:
                continue

            container_match = self._CONTAINER_RX.match(stripped)
            if container_match:
                pending_container = container_match.group(1).upper()
                continue

            if pending_container:
                pin_match = self._PIN_RX.match(stripped)
                if pin_match:
                    pairs.append((pending_container, pin_match.group(1).upper()))
                    pending_container = None

        return pairs

    def _fallback_pin(self, text: str) -> str:
        pin = self._match_first(text, [r"\bPIN(?: NUMBER)?\s*[:\-]?\s*([A-Z0-9]{4,12})"])
        if pin:
            return pin.upper()
        fallback = RegexUtils.after(text, "PIN", r"[A-Z0-9]{4,12}") or ""
        return fallback.upper()

    def _sanitize_yard_block(self, block: str) -> str:
        cleaned: List[str] = []
        for raw in (block or "").splitlines():
            stripped = raw.strip()
            if not stripped:
                if cleaned:
                    break
                continue
            upper = stripped.upper()
            if any(upper.startswith(prefix) for prefix in self._YARD_STOP_PREFIXES):
                break
            cleaned.append(stripped)
        return "\n".join(cleaned).strip()

    def _extract_yard(self, text: str) -> str:
        yard = self._match_first(text, self._YARD_PATTERNS, flags=RegexUtils.IGNORECASE | RegexUtils.MULTILINE | RegexUtils.DOTALL)
        yard = self._sanitize_yard_block(yard)
        if yard:
            return yard

        between = RegexUtils.extract_between(text, "Empty Container to be Returned to", "Type")
        yard = self._sanitize_yard_block(between or "")
        if yard:
            return yard

        between = RegexUtils.extract_between(text, "EMPTY CONTAINER TO BE RETURNED TO", "TYPE")
        yard = self._sanitize_yard_block(between or "")
        if yard:
            return yard

        return ""