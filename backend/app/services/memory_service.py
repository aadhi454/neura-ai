from ..db.database import (
    fetch_recent_messages,
    get_latest_summary,
    save_message,
    save_summary,
)
from ..core.config import settings


def remember_user_message(user_id: str, session_id: str, message: str) -> None:
    save_message(user_id, session_id, "user", message)


def remember_assistant_message(user_id: str, session_id: str, message: str) -> None:
    save_message(user_id, session_id, "assistant", message)


def get_recent_conversation_history(user_id: str, session_id: str) -> list[dict]:
    rows = fetch_recent_messages(user_id, session_id, settings.recent_message_limit)
    return [
        {"role": row["role"], "content": row["message"]}
        for row in rows
        if row.get("role") in {"user", "assistant"} and row.get("message")
    ]


def get_memory_summary(user_id: str, session_id: str) -> str | None:
    return get_latest_summary(user_id, session_id)


def store_memory_summary(user_id: str, session_id: str, summary: str) -> None:
    save_summary(user_id, session_id, summary)


def get_context_bundle(user_id: str, session_id: str) -> dict:
    return {
        "summary": get_memory_summary(user_id, session_id),
        "recent_history": get_recent_conversation_history(user_id, session_id),
    }
