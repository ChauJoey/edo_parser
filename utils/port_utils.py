from __future__ import annotations

from typing import ClassVar, Iterable, Sequence

from utils.regex_utils import RegexUtils
from utils.text_utils import TextUtils


class PortExtractor:
    """Best-effort parser for Port of Discharge style fields across carriers."""

    _INLINE_REGEX = RegexUtils.compile(
        r"(?:PORT\s+OF\s+DISCHARGE|DISCHARGE\s+PORT|PORT\s+OF\s+DEST(?:INATION)?|PORT\s+DESTINATION|FINAL\s+DESTINATION|P\.?O\.?D\.?)"
        r"(?:\s*[:\-]\s*|\s+)"
        r"(?P<value>[A-Z0-9 ,./()&'\\-]{3,80})",
        flags=RegexUtils.IGNORECASE,
    )
    _ACCEPTED_HEADINGS: ClassVar[set[str]] = {
        "PORT OF DISCHARGE",
        "DISCHARGE PORT",
        "PORT OF DESTINATION",
        "PORT OF DEST",
        "PORT OF DESTN",
        "PORT OF DESTINATION / ETA",
        "PORT OF DESTINATION/ETA",
        "PORT",
        "PORT DESTINATION",
        "PORT DESTINATION / ETA",
        "POD",
        "P O D",
        "PORT OF ARRIVAL",
        "DESTINATION",
        "FINAL DESTINATION",
    }
    _KEYWORD_HEADINGS: ClassVar[Sequence[str]] = (
        "PORT OF DISCHARGE",
        "DISCHARGE PORT",
        "PORT OF DESTINATION",
        "PORT OF DEST",
        "PORT OF DESTN",
        "PORT DESTINATION",
        "FINAL DESTINATION",
    )
    _SKIP_HEADINGS: ClassVar[set[str]] = {
        "ETA",
        "ETD",
        "ATA",
        "ATD",
        "DATE",
        "VESSEL",
        "VESSEL / VOYAGE",
        "VESSEL / VOYAGE / LLOYDS",
        "VESSEL VOYAGE",
        "VOYAGE",
        "PLACE OF DELIVERY",
        "PLACE OF EMPTY RETURN",
        "PLACE OF RECEIPT",
        "PLACE OF RECEIPT / DEL",
        "PLACE OF DELIVERY / RETURN",
        "CONSIGNEE",
        "SHIPPER",
        "CARGO OPERATOR",
        "TERMINAL",
        "PIN",
        "PIN CODE",
        "PIN NUMBER",
        "PIN CODE / RELEASE",
        "CONTAINER",
        "CONTAINER NO",
        "CONTAINER NUMBER",
        "CONTAINER PLACE OF AVAILABILITY",
        "BILL OF LADING",
        "BILL OF LADING NUMBER",
        "BOOKING NUMBER",
        "BOOKING NO",
        "IMPORT DELIVERY ORDER",
        "DELIVERY ORDER",
        "DESCRIPTION",
        "DETAILS",
        "NOTES",
        "REFERENCE",
        "REF",
        "NOTICE",
        "CARGO RELEASED TO",
        "IMO NUMBER",
    }
    _BREAK_HEADINGS: ClassVar[set[str]] = {
        "PORT OF LOADING",
        "PORT OF LOAD",
        "LOAD PORT",
        "LOADING PORT",
        "EXPORT PORT",
        "PORT OF ORIGIN",
        "PLACE OF RECEIPT",
    }
    _STATE_HINTS: ClassVar[Sequence[str]] = (" NSW", " VIC", " QLD", " WA", " SA", " NT", " TAS", " ACT")
    _LOCATION_HINTS: ClassVar[Sequence[str]] = (
        "SYD",
        "MELB",
        "MEL ",
        "BRIS",
        "BNE",
        "ADELAIDE",
        "ADE ",
        "FREMANTLE",
        "FREM",
        "PERTH",
        "BOTANY",
        "PORT KEMBLA",
        "PORT MELBOURNE",
        "PORT HEDLAND",
        "PORTLAND",
        "GEELONG",
        "NEWCASTLE",
        "DARWIN",
        "HOBART",
        "TOWNSVILLE",
        "GLADSTONE",
        "MACKAY",
    )
    _NEGATIVE_HINTS: ClassVar[Sequence[str]] = (
        "SHIPPING",
        "LOGISTICS",
        "LINES",
        " LINE",
        "PTY LTD",
        "LIMITED",
        "DEPOT",
        "EMPTY",
        "RETURN",
        "AVAILABILITY",
        "ECP",
    )
    _MAX_LOOKAHEAD: ClassVar[int] = 8
    _MAX_LOOKBACK: ClassVar[int] = 2

    @classmethod
    def extract(cls, text: str) -> str:
        if not text:
            return ""

        lines = [cls._sanitize_line(line) for line in text.splitlines()]
        for idx, line in enumerate(lines):
            if not line:
                continue

            inline = cls._value_from_heading_line(line)
            if inline:
                return inline

            if cls._contains_keyword(line):
                forward = cls._scan(lines, range(idx + 1, idx + cls._MAX_LOOKAHEAD + 1))
                if forward:
                    return forward
                backward = cls._scan(lines, range(idx - 1, idx - cls._MAX_LOOKBACK - 1, -1))
                if backward:
                    return backward

        fallback = cls._scan(lines, range(len(lines)), respect_breaks=False)
        if fallback:
            return fallback

        return ""

    @classmethod
    def _scan(cls, lines: Sequence[str], indices: Iterable[int], *, respect_breaks: bool = True) -> str:
        total_lines = len(lines)
        for idx in indices:
            if idx < 0 or idx >= total_lines:
                continue

            raw = lines[idx]
            if not raw:
                continue

            normalized = cls._normalize_heading(raw)
            if respect_breaks and normalized in cls._BREAK_HEADINGS:
                break
            if normalized in cls._SKIP_HEADINGS:
                continue

            candidate = cls._candidate_value(raw)
            if not candidate:
                continue

            score = cls._score_candidate(candidate)
            if score > 0:
                return candidate

        return ""

    @classmethod
    def _candidate_value(cls, line: str) -> str:
        value = cls._value_from_heading_line(line)
        if value:
            return value
        return cls._clean_candidate(line)

    @classmethod
    def _value_from_heading_line(cls, line: str) -> str:
        cleaned = line.replace("\u00a0", " ").strip()
        if not cleaned:
            return ""

        inline_match = cls._INLINE_REGEX.search(cleaned)
        if inline_match:
            candidate = cls._clean_candidate(inline_match.group("value"))
            if candidate:
                return candidate

        for sep in (":", "-", "–"):
            if sep in cleaned:
                head, tail = cleaned.split(sep, 1)
                head_norm = cls._normalize_heading(head)
                if head_norm in cls._ACCEPTED_HEADINGS:
                    candidate = cls._clean_candidate(tail)
                    if candidate:
                        return candidate
                break

        return ""

    @classmethod
    def _contains_keyword(cls, line: str) -> bool:
        upper_line = cls._normalize_heading(line)
        if not upper_line:
            return False
        if upper_line in cls._ACCEPTED_HEADINGS:
            return True
        for keyword in cls._KEYWORD_HEADINGS:
            if keyword in upper_line:
                return True
        if upper_line in {"POD", "P O D"}:
            return True
        return False

    @classmethod
    def _clean_candidate(cls, value: str) -> str:
        stripped = value.strip(" :\t")
        stripped = TextUtils.collapse_spaces(stripped)
        if not stripped:
            return ""

        upper = stripped.upper()
        if upper in cls._ACCEPTED_HEADINGS or upper in cls._SKIP_HEADINGS:
            return ""
        if "@" in stripped or "|" in stripped:
            return ""
        if "/" in stripped and "PORT" not in upper:
            return ""
        if RegexUtils.fullmatch(r"[A-Z]{4}\d{7}", stripped, flags=RegexUtils.IGNORECASE):
            return ""
        if (
            RegexUtils.fullmatch(r"[A-Z0-9]{6,}", stripped, flags=RegexUtils.IGNORECASE)
            and " " not in stripped
            and any(ch.isdigit() for ch in stripped)
        ):
            return ""
        if RegexUtils.fullmatch(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}", stripped, flags=RegexUtils.IGNORECASE):
            return ""
        if RegexUtils.fullmatch(r"[A-Z]{3}\s+\d{1,2}\s+\d{4}", stripped, flags=RegexUtils.IGNORECASE):
            return ""
        digit_count = sum(1 for ch in stripped if ch.isdigit())
        if digit_count >= 4:
            has_hint = any(
                hint in upper for hint in ("PORT", "AUSTRALIA", "AUST") + tuple(cls._LOCATION_HINTS)
            ) or any(state.strip() and state.strip() in upper for state in cls._STATE_HINTS)
            if not has_hint:
                return ""
        if any(token in upper for token in cls._NEGATIVE_HINTS):
            return ""

        letters = sum(1 for ch in stripped if ch.isalpha())
        if letters < 2:
            return ""

        return stripped

    @classmethod
    def _score_candidate(cls, value: str) -> int:
        upper = value.upper()
        score = 0

        if RegexUtils.search(r"\bPORT\b", upper, flags=RegexUtils.IGNORECASE):
            score += 3
        elif "HARBOUR" in upper or "HARBOR" in upper:
            score += 3

        if any(token in upper for token in ("TERMINAL", "WHARF", "GATE", "BERTH", "DOCK")):
            score += 1

        for hint in cls._LOCATION_HINTS:
            if hint in upper:
                score += 2
                break

        if any(state in upper for state in cls._STATE_HINTS):
            score += 1

        if "AUSTRALIA" in upper or "AUST" in upper:
            score += 1

        if any(token in upper for token in cls._NEGATIVE_HINTS):
            score -= 2

        return score

    @staticmethod
    def _sanitize_line(line: str) -> str:
        cleaned = "".join(ch if ch.isprintable() else " " for ch in (line or ""))
        return cleaned.strip()

    @staticmethod
    def _normalize_heading(value: str) -> str:
        cleaned = "".join(ch if ch.isalnum() or ch.isspace() or ch in {"/"} else " " for ch in (value or "").upper())
        return TextUtils.collapse_spaces(cleaned).rstrip(":")
