from typing import Dict, List

from utils.regex_utils import RegexUtils
from utils.text_utils import TextUtils
from ..base_strategy import BaseStrategy


class HMMStrategy(BaseStrategy):
    """Extraction strategy for HMM (Hyundai Merchant Marine) delivery orders."""

    name = "HMM"
    keywords = ["HMM", "HYUNDAI MERCHANT MARINE", "HYUNDAI MERCHANT", "HMM AUSTRALIA"]

    def match(self, text: str) -> bool:
        t = (text or "").upper()
        return any(keyword in t for keyword in self.keywords)

    @staticmethod
    def _extract_pin(text: str, containers: List[str]) -> str:
        block = RegexUtils.extract_between(text, "Container Information", "* EQ Return Facility Information") or ""
        pattern = r"(?=[A-Z0-9]{4,20}\b)[A-Z0-9]*\d[A-Z0-9]*"
        candidates = RegexUtils.find_all(block, pattern) or []
        container_set = {c.upper() for c in containers}
        for candidate in candidates:
            if candidate.upper() not in container_set:
                return candidate
        return ""

    @staticmethod
    def _extract_yard(text: str) -> str:
        block = RegexUtils.extract_between(text, "Location", "Notice") or ""
        lines = [line.strip(" :") for line in block.splitlines() if line.strip()]
        filtered: List[str] = []
        for line in lines:
            upper = line.upper()
            if upper in {"LOCATION", "PHONE NO.", "TURN-IN REF"}:
                continue
            if upper.startswith("NOTICE"):
                break
            cleaned = line.replace("...", "").strip(" .")
            if cleaned:
                filtered.append(cleaned)
            if len(filtered) >= 2:
                break
        return TextUtils.collapse_spaces(" ".join(filtered))

    def extract(self, text: str) -> List[Dict[str, str]]:
        containers = RegexUtils.iso_container_candidates(text)
        if not containers:
            return []

        pin = self._extract_pin(text, containers)
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
