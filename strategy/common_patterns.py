from utils.regex_utils import RegexUtils

COMMON_PATTERNS = {
    "container": RegexUtils.compile(r"\b[A-Z]{4}\s*\d{7}\b"),
    "pin": RegexUtils.compile(r"\b[P]?IN[:\s-]*([A-Z0-9]{4,12})\b"),
    "yard_hint": RegexUtils.compile(r"\b(Depot|Terminal|Yard|Park|Port|Botany)\b[\w\s\-]*"),
}
