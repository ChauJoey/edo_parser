from typing import Dict, List
from utils.text_utils import TextUtils

# 示例映射表，后续可放到 configs/yard_mapping.json
_YARD_MAPPING = {
    "BOTANY 1": "Botany Park 1",
    "BOTANY PARK 1": "Botany Park 1",
    "BOTANY PARK I": "Botany Park 1",
}

class Normalizer:
    """负责字段标准化"""
    @staticmethod
    def norm_shippingLine(shipping: str) -> str:
        return TextUtils.normalize_upper_no_space(shipping)

    @staticmethod
    def norm_container(code: str) -> str:
        return TextUtils.normalize_upper_no_space(code)

    @staticmethod
    def norm_pin(pin: str) -> str:
        return (pin or "").strip().upper()

    @staticmethod
    def norm_yard(yard: str) -> str:
        y = TextUtils.collapse_spaces((yard or "").upper())
        return _YARD_MAPPING.get(y, yard.strip())

    @staticmethod
    def apply(records: List[Dict[str, str]]) -> List[Dict[str, str]]:
        out = []
        for r in records:
            out.append({
                "Shipping Line": Normalizer.norm_shippingLine(r.get("Shipping Line", "")) ,
                "柜号": Normalizer.norm_container(r.get("柜号", "")),
                "PIN": Normalizer.norm_pin(r.get("PIN", "")),
                "还柜场": Normalizer.norm_yard(r.get("还柜场", "")),
            })
        return out
