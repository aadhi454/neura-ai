from __future__ import annotations

from ..utils.text import normalize_text


REPETITION_THRESHOLD = 1

PROCRASTINATION_KEYWORDS = [
    "lazy",
    "procrastinate",
    "procrastinating",
    "delay",
    "delaying",
    "later",
    "tomorrow",
    "can't start",
    "cant start",
    "postpone",
    "postponing",
    "avoid",
]

CONFUSION_KEYWORDS = [
    "confused",
    "not sure",
    "unsure",
    "don't understand",
    "dont understand",
    "what do you mean",
    "what does that mean",
    "vague",
    "unclear",
    "i guess",
]


def _word_set(text: str) -> set[str]:
    normalized = normalize_text(text)
    return {word for word in normalized.split(" ") if word}


def _jaccard_similarity(left: str, right: str) -> float:
    left_words = _word_set(left)
    right_words = _word_set(right)
    if not left_words or not right_words:
        return 0.0

    overlap = left_words & right_words
    union = left_words | right_words
    return len(overlap) / len(union)


def _detect_repetition(message: str, recent_messages: list[dict]) -> dict:
    normalized_message = normalize_text(message)
    recent_user_messages = [
        item.get("content", item.get("message", ""))
        for item in recent_messages
        if item.get("role") == "user"
    ]

    exact_matches = sum(
        1 for item in recent_user_messages if normalize_text(item) == normalized_message
    )
    similar_matches = sum(
        1
        for item in recent_user_messages
        if normalize_text(item) != normalized_message
        and _jaccard_similarity(item, message) >= 0.6
    )

    score = exact_matches + similar_matches
    detected = score >= REPETITION_THRESHOLD

    return {
        "detected": detected,
        "score": score,
        "evidence": {
            "exact_matches": exact_matches,
            "similar_matches": similar_matches,
        },
    }


def _detect_procrastination(message: str) -> dict:
    normalized_message = normalize_text(message)
    matched_keywords = [keyword for keyword in PROCRASTINATION_KEYWORDS if keyword in normalized_message]
    score = len(matched_keywords)

    return {
        "detected": score > 0,
        "score": score,
        "evidence": matched_keywords,
    }


def _detect_confusion(message: str) -> dict:
    normalized_message = normalize_text(message)
    matched_keywords = [keyword for keyword in CONFUSION_KEYWORDS if keyword in normalized_message]

    vague_question = normalized_message.endswith("?") and len(normalized_message.split()) <= 4
    score = len(matched_keywords) + (1 if vague_question else 0)

    return {
        "detected": score > 0,
        "score": score,
        "evidence": {
            "matched_keywords": matched_keywords,
            "vague_question": vague_question,
        },
    }


def detect_behavior(message: str, recent_messages: list[dict]) -> dict:
    repetition = _detect_repetition(message, recent_messages)
    procrastination = _detect_procrastination(message)
    confusion = _detect_confusion(message)

    return {
        "repetition": repetition,
        "procrastination": procrastination,
        "confusion": confusion,
    }


def behavior_tags_from_signals(signals: dict) -> list[str]:
    tags: list[str] = []

    if signals.get("repetition", {}).get("detected"):
        tags.append("repetitive")
    if signals.get("procrastination", {}).get("detected"):
        tags.append("procrastination")
    if signals.get("confusion", {}).get("detected"):
        tags.append("confused")

    return tags
