import re


GREETING_PATTERNS = (
    r"^(hi|hey|hello|yo|sup|good morning|good afternoon|good evening)\b",
)

INTRO_PATTERNS = (
    r"\bmy name is\b",
    r"\bi am\b",
    r"\bi'm\b",
    r"\bcall me\b",
)

ROLE_PATTERNS = (
    r"\bboss\b",
    r"\bchief\b",
    r"\blead\b",
    r"\bmanager\b",
    r"\byou work for me\b",
    r"\bi am your boss\b",
)


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def is_greeting(message: str) -> bool:
    normalized = normalize_spaces(message).lower()
    return any(re.match(pattern, normalized) for pattern in GREETING_PATTERNS)


def is_unclear_input(message: str, confusion_detected: bool = False) -> bool:
    if confusion_detected:
        return True

    normalized = normalize_spaces(message).lower()
    return len(normalized.split()) <= 2 and not normalized.endswith(("?", "!"))


def is_self_introduction(message: str) -> bool:
    normalized = normalize_spaces(message).lower()
    return any(re.search(pattern, normalized) for pattern in INTRO_PATTERNS)


def is_role_claim(message: str) -> bool:
    normalized = normalize_spaces(message).lower()
    return any(re.search(pattern, normalized) for pattern in ROLE_PATTERNS)


def extract_name(message: str) -> str | None:
    normalized = normalize_spaces(message)
    patterns = [
        r"\bmy name is ([A-Za-z][A-Za-z'\-]{0,30})\b",
        r"\bcall me ([A-Za-z][A-Za-z'\-]{0,30})\b",
        r"\bi am ([A-Za-z][A-Za-z'\-]{0,30})\b",
        r"\bi'm ([A-Za-z][A-Za-z'\-]{0,30})\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, normalized, flags=re.I)
        if match:
            return match.group(1).strip().strip(".,!?")
    return None


def pretty_name(name: str) -> str:
    parts = re.split(r"([-\s'])", name.strip())
    polished: list[str] = []
    for part in parts:
        if part in {"-", " ", "'"}:
            polished.append(part)
        elif part:
            polished.append(part[:1].upper() + part[1:].lower())
    return "".join(polished).strip()


def looks_like_question(message: str) -> bool:
    normalized = normalize_spaces(message)
    question_starters = (
        "what",
        "why",
        "how",
        "when",
        "where",
        "who",
        "which",
        "can you",
        "could you",
        "would you",
        "do you",
    )
    lowered = normalized.lower()
    return lowered.endswith("?") or any(lowered.startswith(starter) for starter in question_starters)
