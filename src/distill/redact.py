import re

REGEX_REDACTORS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b[\w._%+-]+@[\w.-]+\.[A-Za-z]{2,}\b"), "[EMAIL]"),
    (re.compile(r"\b(?:\d[ -]*?){13,16}\b"), "[CARD]"),
    (re.compile(r"\b(?:0|\+84)[\s-]?\d{2,3}[\s-]?\d{3,4}[\s-]?\d{3,4}\b"), "[PHONE_VN]"),
    (re.compile(r"\bsk-[a-zA-Z0-9]{20,}\b"), "[API_KEY]"),
    (re.compile(r"\bglpat-[a-zA-Z0-9_-]{20,}\b"), "[GITLAB_TOKEN]"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"), "[JWT]"),
]


def redact(text: str) -> str:
    for pattern, replacement in REGEX_REDACTORS:
        text = pattern.sub(replacement, text)
    return text
