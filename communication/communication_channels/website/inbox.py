"""Persist outbound messages for the always-on website channel."""

import secrets

from core.config import ensure_user_directory, get_user_file_path
from core.error_handling import handle_errors
from core.file_operations import load_json_data, save_json_data
from core.logger import get_component_logger
from core.time_utilities import now_timestamp_full

logger = get_component_logger("communication_manager")
MAX_INBOX_MESSAGES = 40
MAX_CHAT_TURNS = 80


@handle_errors("loading website inbox", default_return=[])
def list_website_messages(user_id: str) -> list[dict]:
    """Return stored website deliveries for one user, oldest first."""
    if not isinstance(user_id, str) or not user_id.strip():
        return []
    path = get_user_file_path(user_id, "website_inbox")
    if not path:
        return []
    loaded = load_json_data(path)
    messages = loaded.get("messages") if isinstance(loaded, dict) else None
    if not isinstance(messages, list):
        return []
    visible = []
    for item in messages:
        if not isinstance(item, dict):
            continue
        text = item.get("text")
        message_id = item.get("id")
        if not isinstance(text, str) or not text.strip():
            continue
        if not isinstance(message_id, str) or not message_id:
            continue
        visible.append(
            {
                "id": message_id,
                "text": text,
                "category": item.get("category") if isinstance(item.get("category"), str) else "",
                "created_at": item.get("created_at") if isinstance(item.get("created_at"), str) else "",
            }
        )
    return visible


@handle_errors("storing website delivery", default_return=False)
def deliver_to_website(user_id: str, message: str, category: str = "") -> bool:
    """Store one outbound message for every user, beside their email or Discord channel."""
    if not isinstance(user_id, str) or not user_id.strip():
        return False
    if not isinstance(message, str) or not message.strip():
        return False
    if not ensure_user_directory(user_id):
        return False
    path = get_user_file_path(user_id, "website_inbox")
    if not path:
        return False
    loaded = load_json_data(path)
    messages = loaded.get("messages") if isinstance(loaded, dict) else None
    if not isinstance(messages, list):
        messages = []
    messages.append(
        {
            "id": secrets.token_urlsafe(9),
            "text": message.strip(),
            "category": category if isinstance(category, str) else "",
            "created_at": now_timestamp_full(),
        }
    )
    saved = save_json_data(
        {"messages": messages[-MAX_INBOX_MESSAGES:], "turns": _chat_turns(loaded)},
        path,
    )
    if not saved:
        logger.error(f"Could not store a website delivery for user {user_id}")
    return bool(saved)


@handle_errors("reading website chat turns", default_return=[])
def _chat_turns(loaded) -> list:
    """Return the saved website conversation turns from one inbox document."""
    turns = loaded.get("turns") if isinstance(loaded, dict) else None
    return turns if isinstance(turns, list) else []


@handle_errors("reading one website chat turn", default_return=None)
def _visible_turn(item: dict) -> dict | None:
    """Return one stored chat turn the home page can show."""
    text = item.get("text")
    role = item.get("role")
    turn_id = item.get("id")
    if role not in {"you", "mhm"}:
        return None
    if not isinstance(text, str) or not text.strip():
        return None
    if not isinstance(turn_id, str) or not turn_id:
        return None
    return {
        "id": turn_id,
        "role": role,
        "text": text.strip(),
        "created_at": item.get("created_at") if isinstance(item.get("created_at"), str) else "",
    }


@handle_errors("loading website chat", default_return=[])
def list_website_chat_turns(user_id: str) -> list[dict]:
    """Return the website conversation for one user, oldest first."""
    if not isinstance(user_id, str) or not user_id.strip():
        return []
    path = get_user_file_path(user_id, "website_inbox")
    if not path:
        return []
    visible = []
    for item in _chat_turns(load_json_data(path)):
        if not isinstance(item, dict):
            continue
        turn = _visible_turn(item)
        if turn:
            visible.append(turn)
    return visible


@handle_errors("storing website chat", default_return=False)
def append_website_chat_exchange(user_id: str, user_message: str, reply: str) -> bool:
    """Keep one website message and MHM's reply so the next login can show them."""
    if not isinstance(user_id, str) or not user_id.strip():
        return False
    if not isinstance(user_message, str) or not user_message.strip():
        return False
    if not isinstance(reply, str) or not reply.strip():
        return False
    if not ensure_user_directory(user_id):
        return False
    path = get_user_file_path(user_id, "website_inbox")
    if not path:
        return False
    loaded = load_json_data(path)
    messages = loaded.get("messages") if isinstance(loaded, dict) else None
    if not isinstance(messages, list):
        messages = []
    turns = _chat_turns(loaded)
    created_at = now_timestamp_full()
    turns.append(
        {
            "id": secrets.token_urlsafe(9),
            "role": "you",
            "text": user_message.strip(),
            "created_at": created_at,
        }
    )
    turns.append(
        {
            "id": secrets.token_urlsafe(9),
            "role": "mhm",
            "text": reply.strip(),
            "created_at": created_at,
        }
    )
    saved = save_json_data(
        {"messages": messages, "turns": turns[-MAX_CHAT_TURNS:]},
        path,
    )
    if not saved:
        logger.error(f"Could not store website chat for user {user_id}")
    return bool(saved)
