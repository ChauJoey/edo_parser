from __future__ import annotations

from abc import ABC, abstractmethod
from functools import wraps
from typing import Dict, List

from utils.port_utils import PortExtractor


class BaseStrategy(ABC):
    """Base contract for individual shipping line extraction strategies."""

    name: str = "base"
    keywords: List[str] = []
    PORT_FIELD: str = "Port of Discharge"
    PORT_FIELD_ALIASES: List[str] = ["Port of Discharge", "port", "\u505c\u9760\u7801\u5934"]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        extract_impl = cls.__dict__.get("extract")
        if not extract_impl or getattr(extract_impl, "_port_wrapped", False):
            return

        @wraps(extract_impl)
        def wrapped_extract(self, text: str) -> List[Dict[str, str]]:
            records = extract_impl(self, text)
            if not isinstance(records, list):
                return records
            port_value = PortExtractor.extract(text)
            normalized_port = port_value or ""
            alias_candidates = []
            if cls.PORT_FIELD:
                alias_candidates.append(cls.PORT_FIELD)
            alias_candidates.extend(getattr(cls, "PORT_FIELD_ALIASES", []))

            normalized_aliases: List[str] = []
            seen_aliases = set()
            for alias in alias_candidates:
                normalized = (alias or "").strip()
                if not normalized or normalized in seen_aliases:
                    continue
                seen_aliases.add(normalized)
                normalized_aliases.append(normalized)

            for record in records:
                if isinstance(record, dict):
                    for alias in normalized_aliases:
                        record.setdefault(alias, normalized_port)
            return records

        wrapped_extract._port_wrapped = True  # type: ignore[attr-defined]
        cls.extract = wrapped_extract  # type: ignore[assignment]

    @abstractmethod
    def match(self, text: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def extract(self, text: str) -> List[Dict[str, str]]:
        raise NotImplementedError
