from typing import Dict, List
from utils.regex_utils import RegexUtils
from utils.text_utils import TextUtils
from .base_strategy import BaseStrategy
from .common_patterns import COMMON_PATTERNS

class GenericStrategy(BaseStrategy):
    """兜底策略：当无匹配船司时使用"""

    name = "generic"
    keywords = []

    def match(self, text: str) -> bool:
        # 永远返回 True，作为兜底策略
        return True

    def extract(self, text: str) -> List[Dict[str, str]]:
        containers = RegexUtils.iso_container_candidates(text)
        pin = RegexUtils.find_first(text, COMMON_PATTERNS["pin"]) or ""
        yard = RegexUtils.find_first(text, COMMON_PATTERNS["yard_hint"]) or ""

        if pin.upper().startswith("PIN"):
            pin = pin.split(":")[-1].strip().lstrip("-")

        yard = TextUtils.collapse_spaces(yard)
        results = []
        for c in containers:
            results.append({"柜号": c, "PIN": pin, "还柜场": yard})
        return results
