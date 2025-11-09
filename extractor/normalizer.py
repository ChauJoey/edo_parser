from __future__ import annotations

from typing import Dict, List

from utils.text_utils import TextUtils

# Keep in sync with configs/yard_mapping.json if that file is introduced later.
_YARD_MAPPING = {
    "BOTANY 1": "Botany Park 1",
    "BOTANY PARK 1": "Botany Park 1",
    "BOTANY PARK I": "Botany Park 1",
}


class Normalizer:
    """Normalize extracted EDO fields so downstream logic receives consistent data."""

    @staticmethod
    def norm_shipping_line(value: str) -> str:
        return TextUtils.normalize_upper_no_space(value)

    @staticmethod
    def norm_ctn_number(value: str) -> str:
        return TextUtils.normalize_upper_no_space(value)

    @staticmethod
    def norm_pin(value: str) -> str:
        return (value or "").strip().upper()

    @staticmethod
    def norm_empty_park(value: str) -> str:
        yard_key = TextUtils.collapse_spaces((value or "").upper())
        mapped = _YARD_MAPPING.get(yard_key)
        if mapped:
            return mapped
        return TextUtils.collapse_spaces(value or "")

    @staticmethod
    def norm_port(value: str) -> str:
        return TextUtils.collapse_spaces(value or "")

    @staticmethod
    def norm_perview_link(value: str) -> str:
        return (value or "").strip()

    @staticmethod
    def apply(records: List[Dict[str, str]]) -> List[Dict[str, str]]:
        normalised: List[Dict[str, str]] = []
        for record in records:
            normalised.append(
                {
                    "Shipping Line": Normalizer.norm_shipping_line(record.get("Shipping Line", "")),
                    "CTN NUMBER": Normalizer.norm_ctn_number(record.get("CTN NUMBER", record.get("柜号", ""))),
                    "EDO PIN": Normalizer.norm_pin(record.get("EDO PIN", record.get("PIN", ""))),
                    "Empty Park": Normalizer.norm_empty_park(record.get("Empty Park", record.get("还柜场", ""))),
                    "Port of Discharge": Normalizer.norm_port(
                        record.get("Port of Discharge", record.get("port", record.get("停靠码头", "")))
                    ),
                    "Perview Link": Normalizer.norm_perview_link(record.get("Perview Link", "")),
                }
            )
        return normalised
