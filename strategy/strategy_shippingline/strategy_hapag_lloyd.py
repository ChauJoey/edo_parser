from typing import Dict, List

from utils.regex_utils import RegexUtils
from utils.text_utils import TextUtils
from ..base_strategy import BaseStrategy


class HapagLloydStrategy(BaseStrategy):
    """Extraction strategy for Hapag-Lloyd delivery orders."""

    name = "HAPAG LLOYD"
    keywords = [
        "HAPAG-LLOYD",
        "HAPAG LLOYD",
        "HAPAG LIOYD",
        "HAPAG LLOYD (AUSTRALIA)",
    ]

    def match(self, text: str) -> bool:
        t = (text or "").upper()
        return any(keyword in t for keyword in self.keywords)

    @staticmethod
    def _extract_pin(text: str) -> str:
        pattern = r"(?=[A-Z0-9-]{4,}\b)[A-Z0-9-]*\d[A-Z0-9-]*"
        pin = RegexUtils.after(text, "Reference:", pattern)
        if pin:
            return pin
        return RegexUtils.after(text, "Turn-In-Reference", pattern) or ""

    @staticmethod
    def _extract_yard(text: str) -> str:
        block = RegexUtils.extract_between(text, "Empty Return Depots", "Remarks") or ""
        lines = [line.strip(" :") for line in block.splitlines() if line.strip()]
        cleaned: List[str] = []
        for line in lines:
            upper = line.upper()
            if upper.startswith("HL") and RegexUtils.search(r"[0-9]{7,}", line):
                continue
            if "TURN-IN-REFERENCE" in upper:
                continue
            if upper.startswith(("MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY")):
                break
            cleaned.append(line)
        return TextUtils.collapse_spaces(" ".join(cleaned))

    def extract(self, text: str) -> List[Dict[str, str]]:
        containers = RegexUtils.iso_container_candidates(text)
        if not containers:
            return []

        pin = self._extract_pin(text)
        yard = self._extract_yard(text)

        records: List[Dict[str, str]] = []
        for container in containers:
            records.append(
                {
                    "Shipping Line": self.name,
                    "柜号": container,
                    "PIN": pin,
                    "还柜场": yard,
                }
            )
        return records
