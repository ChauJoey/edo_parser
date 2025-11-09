from typing import Dict, List
from utils.port_utils import PortExtractor

from utils.regex_utils import RegexUtils
from utils.text_utils import TextUtils
from ..base_strategy import BaseStrategy


class ANLStrategy(BaseStrategy):
    """Strategy tailored for ANL delivery orders."""

    name = "ANL"
    keywords = ["ANL", "CMA-CGM GROUP AGENCIES"]

    _PIN_PATTERNS: List[str] = [
        r"\bPIN(?: NUMBER)?\s*[:\-]?\s*(?P<value>[A-Z0-9]{4,12})",
    ]
    _YARD_PATTERNS: List[str] = [
        r"EMPTY RETURN (?:ADDRESS|LOCATION|DEPOT)\s*[:\-]?\s*(?P<value>[\sA-Z0-9'&,./-]{3,200})",
        r"RETURN LOCATION\s*[:\-]?\s*(?P<value>[\sA-Z0-9'&,./-]{3,200})",
        r"DEPOT\s*[:\-]?\s*(?P<value>[\sA-Z0-9'&,./-]{3,200})",
    ]
    _YARD_STOP_PREFIXES: List[str] = [
        "TURN-IN-REF",
        "D&D",
        "DEPOSIT",
        "FREIGHT",
        "RELEASE",
        "TOTAL",
        "PAGE",
        "DELIVERY ORDER",
        "CONTAINERS",
        "ADDRESS",
        "EMAIL",
        "PHONE",
    ]
    _DATE_RX = RegexUtils.compile(r"\b\d{2}-[A-Z]{3}-\d{2,4}\b", flags=0)

    def match(self, text: str) -> bool:
        t = (text or "").upper()
        return any(k in t for k in (k.upper() for k in self.keywords))

    @staticmethod
    def _match_first(text: str, patterns: List[str], flags: int = RegexUtils.IGNORECASE | RegexUtils.MULTILINE) -> str:
        src = text or ""
        for pattern in patterns:
            rx = RegexUtils.compile(pattern, flags)
            match = rx.search(src)
            if not match:
                continue
            groups = match.groupdict()
            if "value" in groups:
                return groups["value"].strip()
            if match.groups():
                return match.group(1).strip()
            return match.group(0).strip()
        return ""

    def _extract_pin(self, text: str) -> str:
        pin = self._match_first(text, self._PIN_PATTERNS, flags=RegexUtils.IGNORECASE | RegexUtils.MULTILINE | RegexUtils.DOTALL)
        if pin:
            return pin

        lines = (text or "").splitlines()
        container_rx = RegexUtils.compile(r"^[A-Z]{4}\d{7}$", flags=0)
        for idx, raw in enumerate(lines):
            if raw.strip().upper() != "PIN":
                continue
            for look_ahead in range(idx + 1, min(idx + 8, len(lines))):
                candidate = lines[look_ahead].strip()
                if not candidate:
                    continue
                upper_candidate = candidate.upper()
                if upper_candidate.startswith("EXP DATE"):
                    continue
                if upper_candidate.startswith("WEB LINK"):
                    break
                if RegexUtils.fullmatch(r"[A-Z0-9]{4,12}", candidate, flags=0) and not container_rx.fullmatch(candidate):
                    return candidate
            for look_back in range(idx - 1, max(idx - 6, -1), -1):
                candidate = lines[look_back].strip()
                if not candidate:
                    continue
                upper_candidate = candidate.upper()
                if upper_candidate.startswith("PIN"):
                    continue
                if upper_candidate.startswith("EXP DATE"):
                    break
                if RegexUtils.fullmatch(r"[A-Z0-9]{4,12}", candidate, flags=0) and not container_rx.fullmatch(candidate):
                    return candidate
            break

        return RegexUtils.after(text, "PIN", r"[A-Z0-9]{4,12}") or ""

    def _sanitize_yard_block(self, block: str) -> str:

        cleaned: List[str] = []
        for raw in (block or "").splitlines():
            stripped = raw.strip()
            if not stripped:
                if cleaned:
                    break
                continue
            upper = stripped.upper()
            if any(upper.startswith(prefix) for prefix in self._YARD_STOP_PREFIXES):
                break
            if self._DATE_RX.search(stripped):
                break
            cleaned.append(stripped)
        return "\n".join(cleaned).strip()

    def _collect_yard_lines(self, text: str, anchor: str) -> str:
        upper_text = (text or "").upper()
        idx = TextUtils.find_first_index(upper_text, anchor.upper())
        if idx is None:
            return ""

        tail = (text or "")[idx:].splitlines()
        if not tail:
            return ""

        collected: List[str] = []
        for raw in tail[1:]:
            stripped = raw.strip()
            if not stripped:
                break
            upper = stripped.upper()
            if any(upper.startswith(prefix) for prefix in self._YARD_STOP_PREFIXES):
                break
            if self._DATE_RX.search(stripped):
                break
            collected.append(stripped)
            if len(collected) >= 6:
                break
        if collected:
            return "\n".join(collected).strip()

        lines = (text or "").splitlines()
        upper_lines = [ln.upper() for ln in lines]
        for pos, upper_line in enumerate(upper_lines):
            if anchor.upper() not in upper_line:
                continue
            collected_rev: List[str] = []
            for look_back in range(pos - 1, max(pos - 8, -1), -1):
                candidate = lines[look_back].strip()
                if not candidate:
                    if collected_rev:
                        break
                    continue
                upper_candidate = candidate.upper()
                if any(upper_candidate.startswith(prefix) for prefix in self._YARD_STOP_PREFIXES):
                    if collected_rev:
                        break
                    continue
                if self._DATE_RX.search(candidate):
                    break
                if RegexUtils.fullmatch(r"[A-Z]{4}\d{7}", candidate, flags=0):
                    continue
                collected_rev.append(candidate)
            collected_rev.reverse()
            return "\n".join(collected_rev).strip()
        return ""

    def _extract_yard(self, text: str) -> str:
        yard = self._match_first(text, self._YARD_PATTERNS, flags=RegexUtils.IGNORECASE | RegexUtils.MULTILINE | RegexUtils.DOTALL)
        yard = self._sanitize_yard_block(yard)
        if yard:
            return yard

        between = RegexUtils.extract_between(text, "EMPTY RETURN", "Turn-In-Ref")
        yard = self._sanitize_yard_block(between)
        if yard:
            return yard

        yard = self._collect_yard_lines(text, "EMPTY RETURN")
        if yard:
            return yard

        fallback = RegexUtils.after(text, "EMPTY RETURN", r"[A-Z0-9'&,./-]{3,80}") or ""
        return fallback.strip()

    def extract(self, text: str) -> List[Dict[str, str]]:
        containers = RegexUtils.iso_container_candidates(text)
        pin = self._extract_pin(text)
        yard = TextUtils.collapse_spaces(self._extract_yard(text))

        port = PortExtractor.extract(text)

        results: List[Dict[str, str]] = []
        for container in containers:
            results.append(
                {
                    "Shipping Line": self.name,
                    "\u67dc\u53f7": container,
                    "PIN": pin,
                    "\u8fd8\u67dc\u573a": yard,
                }
            )
        for record in results:
            record.setdefault("Port of Discharge", port)
            record.setdefault("\u505c\u9760\u7801\u5934", port)
        return results