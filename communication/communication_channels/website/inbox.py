"""Persist outbound messages for the always-on website channel."""

import os
import secrets

from core.config import ensure_user_directory, get_user_file_path
from core.error_handling import handle_errors
from core.file_operations import load_json_data, update_json_data
from core.logger import get_component_logger
from core.time_utilities import now_timestamp_full

logger = get_component_logger("communication_manager")
MAX_INBOX_MESSAGES = 40
MAX_CHAT_TURNS = 80
_EMPTY_WEBSITE_INBOX = {"messages": [], "turns": []}


@handle_errors("reading website inbox", default_return=_EMPTY_WEBSITE_INBOX)
def _load_website_inbox(path: str) -> dict:
    """Return the saved inbox, or an empty one when the file is not there yet."""
    if not isinstance(path, str) or not path.strip() or not os.path.isfile(path):
        return {"messages": [], "turns": []}
    loaded = load_json_data(path)
    if not isinstance(loaded, dict):
        return {"messages": [], "turns": []}
    return loaded


@handle_errors("copying website inbox", default_return=_EMPTY_WEBSITE_INBOX)
def _read_website_inbox(path: str) -> dict:
    """Return a fresh inbox copy so one caller cannot change the empty default."""
    loaded = _load_website_inbox(path)
    if not isinstance(loaded, dict):
        loaded = _EMPTY_WEBSITE_INBOX
    messages = loaded.get("messages")
    turns = loaded.get("turns")
    return {
        "messages": list(messages) if isinstance(messages, list) else [],
        "turns": list(turns) if isinstance(turns, list) else [],
    }


@handle_errors("loading website inbox", default_return=[])
def list_website_messages(user_id: str) -> list[dict]:
    """Return stored website deliveries for one user, oldest first."""
    if not isinstance(user_id, str) or not user_id.strip():
        return []
    path = get_user_file_path(user_id, "website_inbox")
    if not path:
        return []
    loaded = _read_website_inbox(path)
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
        visible_item = {
            "id": message_id,
            "text": text,
            "category": item.get("category") if isinstance(item.get("category"), str) else "",
            "created_at": item.get("created_at") if isinstance(item.get("created_at"), str) else "",
        }
        delivery_id = item.get("delivery_id")
        if isinstance(delivery_id, str) and delivery_id:
            visible_item["delivery_id"] = delivery_id
        visible.append(visible_item)
    return visible


@handle_errors("storing website delivery", default_return=False)
def deliver_to_website(
    user_id: str,
    message: str,
    category: str = "",
    *,
    delivery_id: str | None = None,
) -> bool:
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
    website_message = {
        "id": secrets.token_urlsafe(9),
        "text": message.strip(),
        "category": category if isinstance(category, str) else "",
        "created_at": now_timestamp_full(),
    }
    if isinstance(delivery_id, str) and delivery_id.strip():
        website_message["delivery_id"] = delivery_id.strip()

    @handle_errors("building website delivery update", user_friendly=False, default_return=None)
    def add_message(current):
        """Append to the latest inbox document while its file lock is held."""
        loaded = current if isinstance(current, dict) else _EMPTY_WEBSITE_INBOX
        existing = loaded.get("messages")
        messages = list(existing) if isinstance(existing, list) else []
        messages.append(website_message)
        return {
            "messages": messages[-MAX_INBOX_MESSAGES:],
            "turns": list(_chat_turns(loaded)),
        }

    saved = update_json_data(path, add_message, default={"messages": [], "turns": []})
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
    for item in _chat_turns(_read_website_inbox(path)):
        if not isinstance(item, dict):
            continue
        turn = _visible_turn(item)
        if turn:
            visible.append(turn)
    return visible


@handle_errors("sorting a conversation turn", default_return=(0.0, 1, 0))
def _turn_sort_key(item: dict, index: int) -> tuple[float, int, int]:
    """Oldest first. A person speaks before MHM when both share a timestamp."""
    from core.time_utilities import timestamp_sort_key_from_dict

    role_order = 0 if item.get("role") == "you" else 1
    return (timestamp_sort_key_from_dict(item, "created_at"), role_order, index)


@handle_errors("counting stored conversation pairs", default_return={})
def _pair_counts(turns: list[dict]) -> dict[tuple[str, str], int]:
    """Count website user-then-MHM pairs already stored as chat turns."""
    counts: dict[tuple[str, str], int] = {}
    index = 0
    while index < len(turns) - 1:
        current = turns[index]
        following = turns[index + 1]
        if current.get("role") == "you" and following.get("role") == "mhm":
            key = (current.get("text", ""), following.get("text", ""))
            counts[key] = counts.get(key, 0) + 1
            index += 2
            continue
        index += 1
    return counts


@handle_errors("loading cross-channel chat", default_return=[])
def _chat_interaction_turns(user_id: str, existing: list[dict]) -> list[dict]:
    """Add Discord and email exchanges that are not already website turns."""
    from core.response_tracking import get_recent_chat_interactions

    remaining = _pair_counts(existing)
    added = []
    interactions = get_recent_chat_interactions(user_id, limit=MAX_CHAT_TURNS)
    for item in reversed(interactions):
        if not isinstance(item, dict):
            continue
        user_text = item.get("user_message")
        reply_text = item.get("ai_response")
        if not isinstance(user_text, str) or not user_text.strip():
            continue
        if not isinstance(reply_text, str) or not reply_text.strip():
            continue
        pair = (user_text.strip(), reply_text.strip())
        if remaining.get(pair, 0) > 0:
            remaining[pair] -= 1
            continue
        created_at = item.get("timestamp") if isinstance(item.get("timestamp"), str) else ""
        added.append(
            {
                "id": f"chat-you-{len(added)}",
                "role": "you",
                "text": pair[0],
                "created_at": created_at,
            }
        )
        added.append(
            {
                "id": f"chat-mhm-{len(added)}",
                "role": "mhm",
                "text": pair[1],
                "created_at": created_at,
            }
        )
    return added


@handle_errors("finding scheduled messages that can be reacted to", default_return={})
def _reactable_by_delivery_id(recent: list[dict]) -> dict[str, dict]:
    """Map delivery IDs to scheduled messages that website reactions can change."""
    found: dict[str, dict] = {}
    for item in recent:
        delivery_id = str(item.get("id") or "")
        if not delivery_id or str(item.get("category") or "") == "checkin":
            continue
        raw_metadata = item.get("metadata")
        metadata = raw_metadata if isinstance(raw_metadata, dict) else {}
        reaction = str(metadata.get("reaction") or "")
        found[delivery_id] = {
            "reaction": reaction if reaction in {"up", "down"} else "",
        }
    return found


@handle_errors("marking one conversation turn as reactable", default_return=None)
def _with_reaction(turn: dict, reactable: dict[str, dict]) -> dict:
    """Attach the scheduled delivery when this MHM message can take a reaction."""
    delivery_id = str(turn.get("delivery_id") or "")
    match = reactable.get(delivery_id)
    if not match:
        turn.pop("delivery_id", None)
        return turn
    turn["reaction"] = match["reaction"]
    return turn


@handle_errors("loading outbound conversation copies", default_return=[])
def _outbound_turns(user_id: str, existing: list[dict]) -> list[dict]:
    """Add MHM messages sent on any channel that are not already in the transcript."""
    from messages.message_data_manager import get_recent_messages

    recent = get_recent_messages(user_id, limit=MAX_INBOX_MESSAGES)
    reactable = _reactable_by_delivery_id(recent)
    seen = {
        (item.get("text", ""), item.get("created_at", ""))
        for item in existing
        if item.get("role") == "mhm"
    }
    added = []
    copied_delivery_ids = set()
    copied_legacy_text = set()
    for item in list_website_messages(user_id):
        text = item.get("text", "")
        created_at = item.get("created_at") or ""
        if (text, created_at) in seen:
            continue
        seen.add((text, created_at))
        delivery_id = str(item.get("delivery_id") or "")
        if delivery_id:
            copied_delivery_ids.add(delivery_id)
        else:
            copied_legacy_text.add(text)
        added.append(
            _with_reaction(
                {
                    "id": item.get("id") or "",
                    "role": "mhm",
                    "text": text,
                    "created_at": created_at,
                    "delivery_id": delivery_id,
                },
                reactable,
            )
        )
    for item in recent:
        text = item.get("sent_text")
        created_at = str(item.get("sent_at") or "")
        if not isinstance(text, str) or not text.strip():
            continue
        text = text.strip()
        delivery_id = str(item.get("id") or "")
        if delivery_id in copied_delivery_ids or text in copied_legacy_text or (text, created_at) in seen:
            continue
        seen.add((text, created_at))
        added.append(
            _with_reaction(
                {
                    "id": str(item.get("id") or ""),
                    "role": "mhm",
                    "text": text,
                    "created_at": created_at,
                    "delivery_id": delivery_id,
                },
                reactable,
            )
        )
    return added


@handle_errors("loading home conversation", default_return=[])
def list_home_conversation(user_id: str) -> list[dict]:
    """Return one timeline of website, Discord, and email messages, oldest first."""
    if not isinstance(user_id, str) or not user_id.strip():
        return []
    turns = list_website_chat_turns(user_id)
    turns.extend(_chat_interaction_turns(user_id, turns))
    turns.extend(_outbound_turns(user_id, turns))
    ordered = sorted(
        enumerate(turns),
        key=lambda pair: _turn_sort_key(pair[1], pair[0]),
    )
    return [item for _index, item in ordered][-MAX_CHAT_TURNS:]


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
    created_at = now_timestamp_full()
    new_turns = [
        {
            "id": secrets.token_urlsafe(9),
            "role": "you",
            "text": user_message.strip(),
            "created_at": created_at,
        },
        {
            "id": secrets.token_urlsafe(9),
            "role": "mhm",
            "text": reply.strip(),
            "created_at": created_at,
        },
    ]

    @handle_errors("building website chat update", user_friendly=False, default_return=None)
    def add_exchange(current):
        """Append the exchange to the latest inbox document under one lock."""
        loaded = current if isinstance(current, dict) else _EMPTY_WEBSITE_INBOX
        existing_messages = loaded.get("messages")
        messages = list(existing_messages) if isinstance(existing_messages, list) else []
        turns = list(_chat_turns(loaded))
        turns.extend(new_turns)
        return {"messages": messages, "turns": turns[-MAX_CHAT_TURNS:]}

    saved = update_json_data(path, add_exchange, default={"messages": [], "turns": []})
    if not saved:
        logger.error(f"Could not store website chat for user {user_id}")
    return bool(saved)
