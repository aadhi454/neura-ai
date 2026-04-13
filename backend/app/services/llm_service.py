import re

from openai import OpenAI

from ..core.config import settings
from ..utils.intent import (
    extract_name,
    is_role_claim,
    looks_like_question,
    pretty_name,
)

client = None

if settings.groq_api_key:
    client = OpenAI(api_key=settings.groq_api_key, base_url=settings.groq_base_url)


GENERIC_REPLY_PATTERNS = [
    r"^i('?m| am) here[.! ]*$",
    r"^tell me what you need[.! ]*$",
    r"^how can i help[.! ]*$",
    r"^let me know if you need anything[.! ]*$",
    r"^i can help with that[.! ]*$",
    r"^sure[.! ]*$",
]

ROBOTIC_REPLY_PATTERNS = [
    r"\bhow may i help\b",
    r"\bplease describe\b",
    r"\bdescribe the issue\b",
    r"\bexact issue\b",
    r"\btell me clearly\b",
    r"\bsir\b",
    r"\bmaster\b",
    r"\bat your service\b",
]


def _normalize_reply(reply: str) -> str:
    text = reply.strip()
    text = re.sub(r"\n{3,}", "\n\n", text)

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return ""

    max_lines = max(1, settings.response_max_lines)
    lines = lines[:max_lines]

    cleaned_lines: list[str] = []
    for line in lines:
        line = re.sub(r"\s+", " ", line)
        line = re.sub(r"^[\-*\u2022]+\s*", "", line)
        line = re.sub(r"^(well|sure|okay|alright|got it|of course)[,!.:\s-]+", "", line, flags=re.I)
        if line:
            cleaned_lines.append(line.strip())

    text = "\n".join(cleaned_lines).strip()

    text = re.sub(r"\bwhatsapp\b", "what's up", text, flags=re.I)
    text = re.sub(r"\bwhats app\b", "what's up", text, flags=re.I)
    text = re.sub(r"\bvoice noted\b", "got it", text, flags=re.I)
    text = re.sub(r"\bvoice received\b", "got it", text, flags=re.I)
    text = re.sub(r"\bvoice heard\b", "i hear you", text, flags=re.I)
    text = re.sub(r"\bi heard you\b", "i hear you", text, flags=re.I)
    text = re.sub(r"\bwhat's on the agenda\b", "what’s on the agenda", text, flags=re.I)
    return text


def _grounded_reply_from_message(message: str, behavior_signals: dict | None = None) -> str:
    cleaned = re.sub(r"\s+", " ", (message or "").strip())
    lowered = cleaned.lower()
    name = extract_name(cleaned)
    role_claim = is_role_claim(cleaned)

    if not cleaned:
        return "Yeah, I’m here. What’s up?"

    if looks_like_question(cleaned):
        return "Got it. Let me answer that."

    if name and role_claim:
        return f"Alright, {pretty_name(name)}. What’s on the agenda?"

    if name:
        return f"Got it, {pretty_name(name)}. What’s up?"

    if role_claim:
        return "Alright. What’s on the agenda?"

    if lowered in {"hi", "hey", "hello", "yo", "sup"}:
        return "Hey… I’m here. What’s up?"

    if behavior_signals and behavior_signals.get("confusion", {}).get("detected"):
        return "Hmm… say that again, I didn’t catch it fully."

    return "Alright… what’s going on?"


def _polish_name_mentions(text: str, user_message: str | None) -> str:
    name = extract_name(user_message or "")
    if not name:
        return text

    pretty = pretty_name(name)
    if not pretty:
        return text

    pattern = re.compile(rf"\b{re.escape(name)}\b", flags=re.I)
    return pattern.sub(pretty, text)


def _polish_reply_text(text: str, user_message: str | None) -> str:
    polished = _normalize_reply(text)
    polished = _polish_name_mentions(polished, user_message)
    if polished and polished[-1] not in ".!?…":
        polished += "."
    return polished


def _is_generic_reply(reply: str) -> bool:
    normalized = re.sub(r"\s+", " ", reply.strip().lower())
    if any(re.match(pattern, normalized) for pattern in GENERIC_REPLY_PATTERNS):
        return True
    return any(re.search(pattern, normalized) for pattern in ROBOTIC_REPLY_PATTERNS)


def _enforce_actionable_reply(
    reply: str,
    user_message: str | None = None,
    behavior_signals: dict | None = None,
) -> str:
    text = _polish_reply_text(reply, user_message)
    if not text:
        return _grounded_reply_from_message(user_message or "", behavior_signals)

    if len(text) > settings.response_max_chars:
        text = text[: settings.response_max_chars].rstrip()
        if text and not text.endswith((".", "!", "?", "…")):
            text += "…"

    return text


def generate_reply(
    messages: list[dict],
    behavior_signals: dict | None = None,
    user_message: str | None = None,
) -> str:
    if client is None:
        return _enforce_actionable_reply(
            _grounded_reply_from_message(user_message or "", behavior_signals),
            user_message=user_message,
            behavior_signals=behavior_signals,
        )

    try:
        response = client.chat.completions.create(
            model=settings.groq_model,
            messages=messages,
            temperature=0.4,
            max_tokens=settings.response_max_tokens,
        )
        content = response.choices[0].message.content
        normalized = _polish_reply_text(content or "", user_message)
        if not normalized or _is_generic_reply(normalized):
            return _enforce_actionable_reply(
                _grounded_reply_from_message(user_message or "", behavior_signals),
                user_message=user_message,
                behavior_signals=behavior_signals,
            )
        return _enforce_actionable_reply(
            normalized,
            user_message=user_message,
            behavior_signals=behavior_signals,
        )
    except Exception:
        return _enforce_actionable_reply(
            _grounded_reply_from_message(user_message or "", behavior_signals),
            user_message=user_message,
            behavior_signals=behavior_signals,
        )
