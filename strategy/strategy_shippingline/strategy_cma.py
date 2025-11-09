from typing import Dict, List
from utils.port_utils import PortExtractor

from utils.regex_utils import RegexUtils
from utils.text_utils import TextUtils
from ..base_strategy import BaseStrategy


class CMAStrategy(BaseStrategy):
    """CMA CGM 船司提柜指令解析策略"""

    name = "CMA_CGM"
    keywords = ["CMA CGM", "CMA"]

    def match(self, text: str) -> bool:
        t = (text or "").upper()
        result = any(k in t for k in (k.upper() for k in self.keywords))
        if result:
            print("Is detected as CMA_CGM.")
        return result

    def extract(self, text: str) -> List[Dict[str, str]]:
        containers = RegexUtils.iso_container_candidates(text)
        pin = RegexUtils.after(text, "PIN", r"[A-Z0-9]{4,12}") or ""
        yard = RegexUtils.after(text, "DEPOT", r"[A-Za-z0-9\-\\s]{3,40}") or ""
        yard = TextUtils.collapse_spaces(yard)


        port = PortExtractor.extract(text)

        results = []
        for c in containers:
            results.append({"柜号": c, "PIN": pin, "还柜场": yard})
        for record in results:
            record.setdefault("Port of Discharge", port)
            record.setdefault("\u505c\u9760\u7801\u5934", port)
        return results