from ..schemas import ChatResponse
from .behavior_service import behavior_tags_from_signals, detect_behavior
from .llm_service import generate_reply
from .memory_service import (
    get_context_bundle,
    remember_assistant_message,
    remember_user_message,
)
from .prompt_service import build_messages


def process_chat_message(user_id: str, session_id: str, message: str) -> ChatResponse:
    cleaned_message = message.strip()
    if not cleaned_message:
        context_bundle = get_context_bundle(user_id, session_id)
        reply = "You went silent there… try again?"
        return ChatResponse(
            reply=reply,
            behavior_tags=[],
            behavior_signals={},
            recent_messages=len(context_bundle.get("recent_history", [])),
        )

    context_bundle = get_context_bundle(user_id, session_id)
    conversation_history = context_bundle.get("recent_history", [])
    behavior_signals = detect_behavior(cleaned_message, conversation_history)
    behavior_tags = behavior_tags_from_signals(behavior_signals)

    remember_user_message(user_id, session_id, cleaned_message)
    messages = build_messages(cleaned_message, context_bundle, behavior_signals)
    reply = generate_reply(messages, behavior_signals, user_message=cleaned_message)
    remember_assistant_message(user_id, session_id, reply)

    return ChatResponse(
        reply=reply,
        behavior_tags=behavior_tags,
        behavior_signals=behavior_signals,
        recent_messages=len(conversation_history),
    )
