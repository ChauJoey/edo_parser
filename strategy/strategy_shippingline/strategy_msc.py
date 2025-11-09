from typing import Dict, List
from utils.port_utils import PortExtractor

from utils.regex_utils import RegexUtils
from utils.text_utils import TextUtils
from ..base_strategy import BaseStrategy


class MSCStrategy(BaseStrategy):
    """Extraction strategy for MSC (Mediterranean Shipping Company) delivery orders."""

    name = "MSC"
    keywords = [
        "MEDITERRANEAN SHIPPING COMPANY",
        "MSC (AUST)",
        "MSC AUSTRALIA",
        "MSC",
    ]

    def match(self, text: str) -> bool:
        t = (text or "").upper()
        return any(keyword in t for keyword in self.keywords)

    @staticmethod
    def _extract_pin(text: str) -> str:
        pattern = r"(?=[0-9A-Z]{4,20}\b)[0-9A-Z]*\d[0-9A-Z]*"
        pin = RegexUtils.after(text, "E-IDO PIN NUMBER", pattern)
        if pin:
            return pin
        return RegexUtils.after(text, "PIN", pattern) or ""

    @staticmethod
    def _extract_yard(text: str) -> str:
        block = RegexUtils.extract_between(text, "Empty Container Return Depot", "Cargo") or ""
        lines = [line.strip(" :") for line in block.splitlines() if line.strip()]
        if not lines:
            line = RegexUtils.after(text, "Empty Container Return Depot", r"[A-Z0-9 ,'/.-]{5,120}") or ""
            if line:
                lines = [line]
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