"""Remember which outbound email a reply is answering."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from core.config import get_user_data_dir
from core.error_handling import handle_errors
from core.file_operations import load_json_data, save_json_data
from core.logger import get_component_logger
from core.time_utilities import now_timestamp_full

logger = get_component_logger("email")

_MESSAGE_ID_RE = re.compile(r"<[^>]+>")
_MAX_THREADS = 100
_MAX_HANDLED = 200
_KINDS = {"checkin", "task_reminder", "message"}


@handle_errors("normalizing an email message id", default_return="")
def normalize_message_id(value: str | None) -> str:
    """Return one Message-ID in angle brackets, or an empty string."""
    if not value or not isinstance(value, str):
        return ""
    match = _MESSAGE_ID_RE.search(value.strip())
    if match:
        return match.group(0)
    token = value.strip().strip("<>").strip()
    if "@" not in token:
        return ""
    return f"<{token}>"


@handle_errors("listing email message ids in a header", default_return=[])
def message_ids_in_header(value: str | None) -> list[str]:
    """Return every Message-ID found in an In-Reply-To or References header."""
    if not value or not isinstance(value, str):
        return []
    return _MESSAGE_ID_RE.findall(value)


@handle_errors("building email reply context path", default_return="")
def _context_path(user_id: str) -> str:
    """Return the per-user email reply index path."""
    if not user_id or not isinstance(user_id, str):
        return ""
    user_dir = get_user_data_dir(user_id.strip())
    if not user_dir:
        return ""
    return str(Path(user_dir) / "email_reply_context.json")


@handle_errors("loading email reply context", default_return={"threads": [], "handled_inbound_ids": []})
def _load_context(user_id: str) -> dict[str, Any]:
    """Load the reply index, or an empty index when the file is missing."""
    path = _context_path(user_id)
    if not path:
        return {"threads": [], "handled_inbound_ids": []}
    payload = load_json_data(path)
    data = payload if isinstance(payload, dict) else {}
    threads = data.get("threads")
    handled = data.get("handled_inbound_ids")
    return {
        "threads": [item for item in threads if isinstance(item, dict)]
        if isinstance(threads, list)
        else [],
        "handled_inbound_ids": [str(item) for item in handled if str(item).strip()]
        if isinstance(handled, list)
        else [],
    }


@handle_errors("saving email reply context", default_return=False)
def _save_context(user_id: str, data: dict[str, Any]) -> bool:
    """Persist the reply index for one user."""
    path = _context_path(user_id)
    if not path:
        return False
    threads_raw = data.get("threads")
    threads = threads_raw if isinstance(threads_raw, list) else []
    handled_raw = data.get("handled_inbound_ids")
    handled = handled_raw if isinstance(handled_raw, list) else []
    save_json_data(
        {
            "threads": threads[-_MAX_THREADS:],
            "handled_inbound_ids": handled[-_MAX_HANDLED:],
        },
        path,
    )
    return True


@handle_errors("recording outbound email reply context", default_return=False)
def record_outbound_email(
    user_id: str,
    message_id: str,
    *,
    kind: str,
    task_id: str = "",
    subject: str = "",
) -> bool:
    """Store the outbound Message-ID so a later reply can find this email."""
    normalized = normalize_message_id(message_id)
    if not user_id or not normalized:
        return False
    stored_kind = kind if kind in _KINDS else "message"
    data = _load_context(user_id)
    threads = [
        item
        for item in data["threads"]
        if normalize_message_id(str(item.get("message_id") or "")) != normalized
    ]
    threads.append(
        {
            "message_id": normalized,
            "kind": stored_kind,
            "task_id": str(task_id or ""),
            "subject": str(subject or ""),
            "created_at": now_timestamp_full(),
        }
    )
    data["threads"] = threads
    return _save_context(user_id, data)


@handle_errors("finding email reply context", default_return=None)
def find_reply_context(
    user_id: str,
    in_reply_to: str | None,
    references: str | None,
) -> dict[str, str] | None:
    """Return the outbound email this reply is answering, when we sent it."""
    if not user_id:
        return None
    candidates: list[str] = []
    parent = normalize_message_id(in_reply_to)
    if parent:
        candidates.append(parent)
    for token in reversed(message_ids_in_header(references)):
        if token not in candidates:
            candidates.append(token)
    if not candidates:
        return None
    by_id = {
        normalize_message_id(str(item.get("message_id") or "")): item
        for item in _load_context(user_id)["threads"]
    }
    for candidate in candidates:
        match = by_id.get(candidate)
        if not isinstance(match, dict):
            continue
        return {
            "message_id": candidate,
            "kind": str(match.get("kind") or "message"),
            "task_id": str(match.get("task_id") or ""),
            "subject": str(match.get("subject") or ""),
        }
    return None


@handle_errors("checking handled inbound email", default_return=False)
def inbound_already_handled(user_id: str, message_id: str) -> bool:
    """Return True when this inbound Message-ID was already answered."""
    normalized = normalize_message_id(message_id)
    if not user_id or not normalized:
        return False
    return normalized in _load_context(user_id)["handled_inbound_ids"]


@handle_errors("recording handled inbound email", default_return=False)
def mark_inbound_handled(user_id: str, message_id: str) -> bool:
    """Remember an inbound Message-ID so a later poll does not answer it twice."""
    normalized = normalize_message_id(message_id)
    if not user_id or not normalized:
        return False
    data = _load_context(user_id)
    handled = [item for item in data["handled_inbound_ids"] if item != normalized]
    handled.append(normalized)
    data["handled_inbound_ids"] = handled
    return _save_context(user_id, data)
