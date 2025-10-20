from typing import Dict, List

from ..base_strategy import BaseStrategy


class BALStrategy(BaseStrategy):
    """Placeholder strategy for BAL shipping documents."""

    name = "BAL"
    keywords = [
        "BAL SHIPPING",
        "BAL TRANSPORT",
        "BAL TRANSPORT AGENCY",
    ]

    def match(self, text: str) -> bool:
        t = (text or "").upper()
        return any(keyword in t for keyword in self.keywords)

    def extract(self, text: str) -> List[Dict[str, str]]:
        # TODO: implement dedicated extraction once sample documents are available.
        return []
