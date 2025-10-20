from typing import Dict, List

from ..base_strategy import BaseStrategy


class HamburgSudStrategy(BaseStrategy):
    """Placeholder strategy for Hamburg Süd delivery orders."""

    name = "HAMBURG SUD"
    keywords = [
        "HAMBURG SUD",
        "HAMBURG SÜD",
    ]

    def match(self, text: str) -> bool:
        t = (text or "").upper()
        return any(keyword in t for keyword in self.keywords)

    def extract(self, text: str) -> List[Dict[str, str]]:
        # TODO: implement dedicated extraction once sample documents are available.
        return []
