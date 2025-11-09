from typing import Dict, List
from utils.port_utils import PortExtractor

from utils.regex_utils import RegexUtils
from utils.text_utils import TextUtils
from ..base_strategy import BaseStrategy


class ONEStrategy(BaseStrategy):
    """Strategy tuned for Ocean Network Express (ONE) delivery orders."""

    name = "ONE"
    keywords = ["OCEAN NETWORK EXPRESS"]

    _PIN_PATTERNS: List[str] = [
        r"\bPIN(?: NUMBER)?\s*[:\-]?\s*(?P<value>[A-Z0-9]{4,12})",
    ]

    _YARD_PATTERNS: List[str] = [
        r"EMPTY RETURN (?:LOCATION|DEPOT)\s*[:\-]?\s*(?P<value>[\sA-Z0-9'&,./()-]{3,120})",
        r"PLACE OF EMPTY RETURN\s*[:\-]?\s*(?P<value>[\sA-Z0-9'&,./()-]{3,120})",
    ]

    _YARD_STOP_PREFIXES: List[str] = [
        "SEAL",
        "TOTAL",
        "ENS",
        "PAGE",
        "SECURE",
        "SIGNED BY",
        "NOTICE",
    ]

    def match(self, text: str) -> bool:
        t = (text or "").upper()
        return all(keyword.upper() in t for keyword in self.keywords)

    @staticmethod
    def _match_first(text: str, patterns: List[str], flags: int = RegexUtils.IGNORECASE | RegexUtils.MULTILINE) -> str:
        source = text or ""
        for pattern in patterns:
            rx = RegexUtils.compile(pattern, flags)
            match = rx.search(source)
            if not match:
                continue
            groups = match.groupdict()
            if "value" in groups:
                return groups["value"].strip()
            if match.groups():
                return match.group(1).strip()
            return match.group(0).strip()
        return ""

    def _extract_pin(self, text: str) -> str:
        pin = self._match_first(text, self._PIN_PATTERNS, flags=RegexUtils.IGNORECASE | RegexUtils.MULTILINE)
        if pin:
            return pin

        lines = (text or "").splitlines()
        for idx, raw in enumerate(lines):
            if "PIN" not in raw.upper():
                continue
            candidate = raw.split(":", 1)[-1].strip()
            if RegexUtils.fullmatch(r"[A-Z0-9]{4,12}", candidate, flags=0):
                return candidate
            if idx + 1 < len(lines):
                candidate_next = lines[idx + 1].strip()
                if RegexUtils.fullmatch(r"[A-Z0-9]{4,12}", candidate_next, flags=0):
                    return candidate_next
        return ""

    def _collect_yard(self, text: str) -> str:
        upper_text = (text or "").upper()
        anchor = "EMPTY RETURN"
        idx = TextUtils.find_first_index(upper_text, anchor)
        if idx is None:
            return ""

        lines = (text or "")[idx:].splitlines()
        if not lines:
            return ""


        location_parts: List[str] = []
        address_parts: List[str] = []
        saw_location_end = False

        first_line = lines[0]
        if ":" in first_line:
            initial = first_line.split(":", 1)[-1].strip()
            if initial:
                location_parts.append(initial)
                if ")" in initial:
                    saw_location_end = True

        for raw in lines[1:10]:
            stripped = raw.strip()
            if not stripped:
                continue
            upper = stripped.upper()
            if any(upper.startswith(prefix) for prefix in self._YARD_STOP_PREFIXES):
                break
            if upper.startswith("ADDRESS"):
                address_parts.append(stripped.split(":", 1)[-1].strip())
                continue
            if not saw_location_end:
                location_parts.append(stripped)
                if ")" in stripped:
                    saw_location_end = True
                continue
            address_parts.append(stripped)

        location = " ".join(location_parts).strip()
        address = " ".join(address_parts).strip()

        if address:
            address = RegexUtils.sub(r"\(TEL.*?$", "", address, flags=RegexUtils.IGNORECASE).strip()

        if location:
            if address and address in location:
                location = location.replace(address, "").strip()
            return location
        return address

    def extract(self, text: str) -> List[Dict[str, str]]:
        containers = RegexUtils.iso_container_candidates(text)
        pin = self._extract_pin(text)
        yard = TextUtils.collapse_spaces(self._collect_yard(text))

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