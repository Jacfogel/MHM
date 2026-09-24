"""Website conversation replies through the shared message handler."""

from core.error_handling import handle_errors

WEBSITE_CHANNEL = "website"
MAX_SUGGESTIONS = 8
FALLBACK_REPLY = (
    "I'm having trouble processing your request right now. Please try again in a moment."
)


@handle_errors("shaping website chat reply", default_return=None)
def chat_payload(response) -> dict | None:
    """Return the plain reply and suggestion buttons a browser can render."""
    message = getattr(response, "message", "")
    if not isinstance(message, str) or not message.strip():
        message = "MHM could not answer that just now. Please try again."
    raw = getattr(response, "suggestions", None) or []
    suggestions = []
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, str):
                continue
            text = item.strip()
            if text and text not in suggestions:
                suggestions.append(text)
            if len(suggestions) >= MAX_SUGGESTIONS:
                break
    return {
        "reply": message,
        "suggestions": suggestions,
        "completed": bool(getattr(response, "completed", True)),
    }


@handle_errors(
    "building website chat reply",
    default_return={
        "reply": FALLBACK_REPLY,
        "suggestions": [],
        "completed": True,
    },
)
def website_chat_reply(user_id: str, message: str) -> dict:
    """Send one website message through the same path as Discord and email."""
    from communication.message_processing.interaction_manager import handle_user_message

    payload = chat_payload(handle_user_message(user_id, message, WEBSITE_CHANNEL))
    if payload is None:
        return {
            "reply": FALLBACK_REPLY,
            "suggestions": [],
            "completed": True,
        }
    return payload
