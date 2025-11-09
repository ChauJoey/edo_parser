from typing import Dict, List
from utils.port_utils import PortExtractor

from utils.regex_utils import RegexUtils
from utils.text_utils import TextUtils
from ..base_strategy import BaseStrategy


class EvergreenStrategy(BaseStrategy):
    """Extraction strategy for Evergreen Line delivery orders."""

    name = "EVERGREEN LINE"
    keywords = [
        "EVERGREEN LINE",
        "EVERGREEN MARINE",
        "EVERGREEN SHIPPING",
        "EVERGREEN",
    ]

    def match(self, text: str) -> bool:
        t = (text or "").upper()
        return any(keyword in t for keyword in self.keywords)

    @staticmethod
    def _extract_pin(text: str) -> str:
        return RegexUtils.after(text, "EIDO Pin", r"[0-9]{4,12}") or ""

    @staticmethod
    def _extract_yard(text: str) -> str:
        block = RegexUtils.extract_between(text, "Please return following container", "Container Number") or ""
        cleaned = RegexUtils.sub(r"[.:]+", " ", block)
        cleaned = RegexUtils.sub(r"^by\s+[0-9/]+\s+to\s+", "", cleaned.strip(), flags=RegexUtils.IGNORECASE)
        lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
        return TextUtils.collapse_spaces(" ".join(lines))

    def extract(self, text: str) -> List[Dict[str, str]]:
        containers = RegexUtils.iso_container_candidates(text)
        if not containers:
            return []

        pin = self._extract_pin(text)
        yard = self._extract_yard(text)


        port = PortExtractor.extract(text)

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
        for record in records:
            record.setdefault("Port of Discharge", port)
            record.setdefault("\u505c\u9760\u7801\u5934", port)
        return records