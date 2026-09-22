"""Discord thumbs reactions that change which scheduled messages are used."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.config import get_user_data_dir
from core.error_handling import handle_errors
from core.file_operations import load_json_data, save_json_data
from core.logger import get_component_logger
from messages.message_data_manager import (
    add_message,
    edit_message,
    get_recent_messages,
    is_ai_generated_message_category,
    load_user_messages,
    update_sent_message_metadata,
)

logger = get_component_logger("message")

SIMILAR_MESSAGES_PER_THUMBS_UP = 2
_UP_REPLY = "I'll send more messages like that."
_UP_AI_REPLY = "I'll write more messages like that."
_UP_KEEP_REPLY = "I'll keep sending more messages like that."
_UP_FAILED_REPLY = (
    "I liked that one, but I couldn't write new messages just now. "
    "Try thumbs up again in a bit."
)
_DOWN_REPLY = "I won't send that message again."


@handle_errors("loading message reaction feedback", default_return={"liked": [], "retired_texts": []})
def load_message_feedback(user_id: str) -> dict[str, Any]:
    """Return liked examples and retired message texts for a user."""
    payload = load_json_data(_feedback_path(user_id))
    data = payload if isinstance(payload, dict) else {}
    liked_raw = data.get("liked")
    retired_raw = data.get("retired_texts")
    liked = liked_raw if isinstance(liked_raw, list) else []
    retired = retired_raw if isinstance(retired_raw, list) else []
    return {
        "liked": [item for item in liked if isinstance(item, dict) and item.get("text")],
        "retired_texts": [str(text) for text in retired if str(text).strip()],
    }


@handle_errors("saving message reaction feedback", default_return=False)
def save_message_feedback(user_id: str, feedback: dict[str, Any]) -> bool:
    """Persist liked examples and retired message texts."""
    path = _feedback_path(user_id)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    save_json_data(
        {
            "liked": list(feedback.get("liked") or []),
            "retired_texts": list(feedback.get("retired_texts") or []),
        },
        path,
    )
    return True


@handle_errors("checking retired message text", default_return=False)
def text_is_retired(user_id: str, text: str) -> bool:
    """Return True when this exact message text was thumbs-downed."""
    key = _text_key(text)
    if not key:
        return False
    return any(_text_key(item) == key for item in load_message_feedback(user_id)["retired_texts"])


@handle_errors("excluding retired messages", default_return=[])
def exclude_retired_messages(user_id: str, messages: list[dict]) -> list[dict]:
    """Drop candidate templates whose text was thumbs-downed."""
    return [msg for msg in messages if not text_is_retired(user_id, str(msg.get("text") or ""))]


@handle_errors("building personalized reaction instructions", default_return="")
def personalized_reaction_instructions(user_id: str, category: str) -> str:
    """Return prompt text that steers a personalized category from reactions."""
    feedback = load_message_feedback(user_id)
    liked = [
        str(item.get("text") or "").strip()
        for item in feedback["liked"]
        if item.get("category") == category and str(item.get("text") or "").strip()
    ][:3]
    retired = [text.strip() for text in feedback["retired_texts"] if str(text).strip()][:8]
    parts: list[str] = []
    if liked:
        parts.append(
            "Write in the same spirit as these liked messages: " + " | ".join(liked)
        )
    if retired:
        parts.append(
            "Do not reuse or closely paraphrase these rejected messages: "
            + " | ".join(retired)
        )
    return " ".join(parts)


@handle_errors("parsing similar message drafts", default_return=[])
def parse_similar_messages(raw: str, source_text: str, limit: int = SIMILAR_MESSAGES_PER_THUMBS_UP) -> list[str]:
    """Split model output into new messages that are not copies of the source."""
    chunks = [part.strip() for part in (raw or "").split("---") if part.strip()]
    if len(chunks) <= 1:
        chunks = [line.strip() for line in (raw or "").splitlines() if line.strip()]
    source_key = _text_key(source_text)
    results: list[str] = []
    seen: set[str] = set()
    for chunk in chunks:
        text = _clean_draft(chunk)
        key = _text_key(text)
        if not key or key == source_key or key in seen or len(text) > 500:
            continue
        seen.add(key)
        results.append(text)
        if len(results) >= limit:
            break
    return results


@handle_errors("generating similar messages", default_return=[])
def generate_similar_message_texts(user_id: str, source_text: str) -> list[str]:
    """Ask the assistant model for new messages that resemble a liked one."""
    from ai.chat.chatbot import get_ai_chatbot

    chatbot = get_ai_chatbot()
    if not getattr(chatbot, "lm_studio_available", False):
        logger.info("Skipping similar-message generation because the model is unavailable")
        return []
    prompt = (
        f"Write exactly {SIMILAR_MESSAGES_PER_THUMBS_UP} short supportive messages "
        "similar to the message below. Match its tone, topic, and approximate length. "
        "Do not copy it. Separate the messages with a line that contains only ---.\n"
        f"Message:\n{source_text.strip()}"
    )
    raw = chatbot.generate_response(prompt, user_id=user_id, mode="personalized")
    return parse_similar_messages(raw, source_text)


@handle_errors(
    "applying message reaction",
    default_return={"status": "failed", "reply": ""},
)
def apply_message_reaction(user_id: str, discord_message_id: str, kind: str) -> dict[str, str]:
    """Apply a thumbs-up or thumbs-down to one scheduled library or personalized message."""
    if kind not in {"up", "down"}:
        return {"status": "ignored", "reply": ""}
    delivery = _find_delivery(user_id, discord_message_id)
    if not delivery:
        return {"status": "ignored", "reply": ""}

    metadata = delivery.get("metadata") if isinstance(delivery.get("metadata"), dict) else {}
    text = str(delivery.get("sent_text") or "")
    category = str(delivery.get("category") or "")
    if category == "checkin":
        return {"status": "ignored", "reply": ""}
    template_id = str(delivery.get("message_template_id") or "")
    previous = str(metadata.get("reaction") or "")
    similar_generated = bool(metadata.get("similar_generated"))

    if kind == "down":
        _retire_text(user_id, text)
        _remove_liked(user_id, category, text)
        _set_template_active(user_id, category, template_id, False)
        _mark_delivery(user_id, str(delivery.get("id") or ""), {"reaction": "down"})
        return {"status": "retired", "reply": _DOWN_REPLY}

    _remember_liked(user_id, category, text)
    _unretire_text(user_id, text)
    _set_template_active(user_id, category, template_id, True)
    if similar_generated or (previous == "up" and is_ai_generated_message_category(category)):
        _mark_delivery(user_id, str(delivery.get("id") or ""), {"reaction": "up"})
        reply = _UP_AI_REPLY if is_ai_generated_message_category(category) else _UP_KEEP_REPLY
        return {"status": "liked", "reply": reply}

    if is_ai_generated_message_category(category):
        _mark_delivery(
            user_id,
            str(delivery.get("id") or ""),
            {"reaction": "up", "similar_generated": True},
        )
        return {"status": "liked", "reply": _UP_AI_REPLY}

    added = _add_similar_library_messages(user_id, category, text, template_id)
    if not added:
        _mark_delivery(user_id, str(delivery.get("id") or ""), {"reaction": "up"})
        return {"status": "failed", "reply": _UP_FAILED_REPLY}
    _mark_delivery(
        user_id,
        str(delivery.get("id") or ""),
        {"reaction": "up", "similar_generated": True},
    )
    return {"status": "liked", "reply": _UP_REPLY}


@handle_errors("building message feedback path", default_return="")
def _feedback_path(user_id: str) -> str:
    """Return the per-user file that stores reaction feedback."""
    return str(Path(get_user_data_dir(user_id)) / "messages" / "message_feedback.json")


@handle_errors("normalizing message reaction text", default_return="")
def _text_key(text: str) -> str:
    """Return a case-insensitive key for comparing message text."""
    return " ".join(str(text or "").split()).casefold()


@handle_errors("cleaning similar message draft", default_return="")
def _clean_draft(text: str) -> str:
    """Strip quotes and list numbering from one generated draft."""
    cleaned = text.strip().strip('"').strip()
    for prefix in ("1.", "2.", "1)", "2)"):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix) :].strip()
    return cleaned


@handle_errors("finding delivery for Discord reaction", default_return=None)
def _find_delivery(user_id: str, discord_message_id: str) -> dict[str, Any] | None:
    """Return the sent message that matches a Discord message id."""
    target = str(discord_message_id or "").strip()
    if not target:
        return None
    for delivery in get_recent_messages(user_id, limit=1000):
        metadata = delivery.get("metadata") if isinstance(delivery.get("metadata"), dict) else {}
        if str(metadata.get("discord_message_id") or "") == target:
            return delivery
    return None


@handle_errors("marking delivery reaction", default_return=None)
def _mark_delivery(user_id: str, delivery_id: str, updates: dict[str, Any]) -> None:
    """Store the latest reaction on the sent-message record."""
    if delivery_id:
        update_sent_message_metadata(user_id, delivery_id, updates)


@handle_errors("setting message template active flag", default_return=False)
def _set_template_active(user_id: str, category: str, template_id: str, active: bool) -> bool:
    """Turn a library template on or off. Personalized messages have no template."""
    if not template_id or is_ai_generated_message_category(category):
        return False
    messages = load_user_messages(user_id, category)
    if not any(str(msg.get("id") or "") == template_id for msg in messages):
        return False
    edit_message(user_id, category, template_id, {"active": active})
    return True


@handle_errors("retiring message text", default_return=None)
def _retire_text(user_id: str, text: str) -> None:
    """Remember an exact message text so it is not sent again."""
    cleaned = " ".join(str(text or "").split())
    if not cleaned:
        return
    feedback = load_message_feedback(user_id)
    if any(_text_key(item) == _text_key(cleaned) for item in feedback["retired_texts"]):
        return
    feedback["retired_texts"].append(cleaned)
    save_message_feedback(user_id, feedback)


@handle_errors("restoring retired message text", default_return=None)
def _unretire_text(user_id: str, text: str) -> None:
    """Allow a previously thumbs-downed text after a later thumbs up."""
    key = _text_key(text)
    feedback = load_message_feedback(user_id)
    feedback["retired_texts"] = [
        item for item in feedback["retired_texts"] if _text_key(item) != key
    ]
    save_message_feedback(user_id, feedback)


@handle_errors("remembering liked message", default_return=None)
def _remember_liked(user_id: str, category: str, text: str) -> None:
    """Keep a liked message as an example for later generation."""
    cleaned = " ".join(str(text or "").split())
    if not cleaned or not category:
        return
    feedback = load_message_feedback(user_id)
    key = _text_key(cleaned)
    if any(
        item.get("category") == category and _text_key(str(item.get("text") or "")) == key
        for item in feedback["liked"]
    ):
        return
    feedback["liked"].append({"category": category, "text": cleaned})
    save_message_feedback(user_id, feedback)


@handle_errors("removing liked message", default_return=None)
def _remove_liked(user_id: str, category: str, text: str) -> None:
    """Drop a liked example after that same message is thumbs-downed."""
    key = _text_key(text)
    feedback = load_message_feedback(user_id)
    feedback["liked"] = [
        item
        for item in feedback["liked"]
        if not (item.get("category") == category and _text_key(str(item.get("text") or "")) == key)
    ]
    save_message_feedback(user_id, feedback)


@handle_errors("adding similar library messages", default_return=[])
def _add_similar_library_messages(
    user_id: str, category: str, source_text: str, template_id: str
) -> list[str]:
    """Create library messages that resemble a thumbs-upped message."""
    drafts = generate_similar_message_texts(user_id, source_text)
    if not drafts:
        return []
    schedule = {"days": ["ALL"], "periods": ["ALL"]}
    for message in load_user_messages(user_id, category):
        if str(message.get("id") or "") == template_id and isinstance(message.get("schedule"), dict):
            schedule = {
                "days": message["schedule"].get("days") or ["ALL"],
                "periods": message["schedule"].get("periods") or ["ALL"],
            }
            break
    added: list[str] = []
    for text in drafts:
        if text_is_retired(user_id, text):
            continue
        add_message(
            user_id,
            category,
            {
                "text": text,
                "category": category,
                "active": True,
                "schedule": schedule,
                "metadata": {"inspired_by": template_id},
            },
        )
        added.append(text)
    return added
