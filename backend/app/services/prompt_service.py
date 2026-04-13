import json

from ..prompts.persona import NEURA_PERSONA
from ..utils.intent import (
    is_greeting,
    is_role_claim,
    is_self_introduction,
    is_unclear_input,
)


def _behavior_policy(behavior_signals: dict) -> tuple[str, str]:
    repetition = behavior_signals.get("repetition", {})
    procrastination = behavior_signals.get("procrastination", {})
    confusion = behavior_signals.get("confusion", {})

    repetition_score = repetition.get("score", 0) or 0
    procrastination_score = procrastination.get("score", 0) or 0
    confusion_score = confusion.get("score", 0) or 0

    if repetition.get("detected") and repetition_score >= 2:
        return (
            "Tone: firmer and more direct. The user is repeating the same topic. Keep it natural, avoid fluff, and move to action.",
            "Action mode: direct and natural. Cut the fluff and move the user forward.",
        )

    if procrastination.get("detected") and procrastination_score >= 2:
        return (
            "Tone: motivating but slightly strict. The user is delaying or avoiding. Nudge them toward a small real step.",
            "Action mode: practical push. Give one tiny step they can start right now.",
        )

    if confusion.get("detected") and confusion_score >= 2:
        return (
            "Tone: patient and clarifying. The user sounds uncertain. Ask one simple follow-up or rephrase naturally.",
            "Action mode: clarification. Ask one simple question or give a quick example.",
        )

    if repetition.get("detected"):
        return (
            "Tone: concise and mildly corrective. The user is repeating themselves. Do not sound scripted.",
            "Action mode: firm guidance. Be direct and avoid repeating yourself.",
        )

    if procrastination.get("detected"):
        return (
            "Tone: encouraging and focused. The user may be procrastinating. Use a short push, not a lecture.",
            "Action mode: practical nudge. Give one tiny task the user can start now.",
        )

    if confusion.get("detected"):
        return (
            "Tone: calm and clarifying. The user may need a simpler answer. Keep it short and natural.",
            "Action mode: simple guidance. Keep it concrete and easy to follow.",
        )

    return (
        "Tone: warm, slightly witty, direct, and modern.",
        "Action mode: one clear next step. Keep it useful, specific, and natural.",
    )


def build_messages(
    user_message: str,
    context_bundle: dict,
    behavior_signals: dict,
) -> list[dict]:
    behavior_summary = json.dumps(behavior_signals, ensure_ascii=True, separators=(",", ":"))
    response_style, action_guidance = _behavior_policy(behavior_signals)
    recent_history = context_bundle.get("recent_history") or []
    summary = context_bundle.get("summary")
    summary_line = f"Memory summary: {summary}\n" if summary else "Memory summary: none\n"
    greeting_line = (
        "User greeting detected. Reply casually and naturally, like a real assistant.\n"
        if is_greeting(user_message)
        else ""
    )
    intro_line = (
        "User is introducing themselves. Acknowledge it naturally and keep it brief.\n"
        if is_self_introduction(user_message)
        else ""
    )
    role_line = (
        "User claims a role or rank. Acknowledge it playfully but respectfully without sounding formal.\n"
        if is_role_claim(user_message)
        else ""
    )
    unclear_line = (
        "User input seems unclear. Ask for a quick repeat in a natural, human way.\n"
        if is_unclear_input(user_message, behavior_signals.get("confusion", {}).get("detected", False))
        else ""
    )

    system_prompt = (
        f"{NEURA_PERSONA.strip()}\n\n"
        f"Behavior signals (structured): {behavior_summary}\n"
        f"{response_style}\n"
        f"{action_guidance}\n"
        f"{summary_line}"
        f"{greeting_line}"
        f"{intro_line}"
        f"{role_line}"
        f"{unclear_line}"
        "Primary rule: respond to the user's exact words first. Do not ignore the input and do not drift into generic support language.\n"
        "If the user introduces themselves, acknowledge the name naturally.\n"
        "If the user claims a role, respond naturally and respectfully without sounding theatrical.\n"
        "If the user asks a question, answer that question directly.\n"
        "Never replace the user's message with generic emotional support or unrelated assistant filler.\n"
        "Use the conversation history to resolve follow-up questions and pronouns correctly.\n"
        "Treat the history as structured messages, not a summary.\n"
        "Return only the final answer. No preamble, no reasoning, no bullet points.\n"
        "Keep the answer short and natural, usually 1-2 sentences.\n"
        "Avoid support-sounding or theatrical phrases like 'How may I help you today', 'Please describe your issue', 'tell me clearly', 'describe the issue', 'exact issue', 'sir', 'master', or 'at your service'.\n"
        "Use simple, natural English.\n"
        "Avoid generic motivational text, vague advice, and robotic sentence structure.\n"
        "If the same issue repeats, respond more firmly and use direct instructions."
    )

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(recent_history)
    messages.append({"role": "user", "content": user_message})
    return messages
