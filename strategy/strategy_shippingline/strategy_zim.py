from typing import Dict, List
from utils.port_utils import PortExtractor

from utils.regex_utils import RegexUtils
from utils.text_utils import TextUtils
from ..base_strategy import BaseStrategy


class ZIMStrategy(BaseStrategy):
    """Extraction strategy for ZIM Integrated Shipping Services delivery orders."""

    name = "ZIM"
    keywords = [
        "ZIM INTEGRATED SHIPPING",
        "ZIM INTEGRATED",
        "ZIM",
    ]

    def match(self, text: str) -> bool:
        t = (text or "").upper()
        return any(keyword in t for keyword in self.keywords)

    @staticmethod
    def _extract_pin(text: str) -> str:
        pattern = r"(?=[A-Z0-9]{4,20}\b)[A-Z0-9]*\d[A-Z0-9]*"
        return RegexUtils.after(text, "PIN Code", pattern) or ""

    @staticmethod
    def _extract_yard(text: str) -> str:
        block = RegexUtils.extract_between(text, "Pickup Depot", "Return Depot") or ""
        lines = [line.strip(" :") for line in block.splitlines() if line.strip()]

        filtered: List[str] = []
        for line in lines:
            upper = line.upper()
            if upper in {"PICKUP DEPOT", "PICKUP ADDRESS", "DEPOT ADDRESS"}:
                continue
            cleaned = line.strip(" .")
            if cleaned:
                filtered.append(cleaned)
        if not filtered:
            return ""

        ordered: List[str] = []
        facility = filtered[0]
        ordered.append(facility)
        gate = next((line for line in filtered if "GATE" in line.upper()), "")
        if gate and gate not in ordered:
            ordered.append(gate)
        for line in filtered[1:]:
            if line not in ordered:
                ordered.append(line)
        return TextUtils.collapse_spaces(" ".join(ordered))

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