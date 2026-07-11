"""Lightweight follow-up alignment using recent conversation history."""

from __future__ import annotations

import re
from typing import Any

from core.error_handling import handle_errors

_FOLLOW_UP_INTEREST_PATTERN = re.compile(
    r"(?i)\b(?:"
    r"what (?:genres?|kinds?|types?).*(?:like|enjoy|prefer)|"
    r"what would i like|what do you think i(?:'d| would) like|"
    r"any recommendations?|recommend something"
    r")\b"
)

_TOPIC_MARKERS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("books", ("book", "books", "reading", "read", "novel", "genre")),
)


@handle_errors("extracting recent conversation topics", default_return=set())
def extract_recent_user_topics(
    conversation_history: list[dict[str, Any]],
    *,
    lookback: int = 5,
) -> set[str]:
    """Infer coarse topics from recent user messages."""
    topics: set[str] = set()
    if not conversation_history:
        return topics

    for chat in list(conversation_history)[-lookback:]:
        user_msg = str(chat.get("user_message") or "").lower()
        if not user_msg:
            continue
        for topic, markers in _TOPIC_MARKERS:
            if any(marker in user_msg for marker in markers):
                topics.add(topic)
    return topics


@handle_errors("aligning response to conversation topic", default_return="")
def align_response_to_conversation_topic(
    user_prompt: str,
    response: str,
    conversation_history: list[dict[str, Any]],
) -> str:
    """Tie follow-up answers back to a topic the user raised in recent turns."""
    if not user_prompt or not response:
        return response
    if not _FOLLOW_UP_INTEREST_PATTERN.search(user_prompt):
        return response

    topics = extract_recent_user_topics(conversation_history)
    if "books" not in topics:
        return response

    lowered = response.lower()
    if any(word in lowered for word in ("book", "read", "reading", "genre")):
        return response

    stripped = response.strip()
    if not stripped:
        return (
            "You mentioned loving books - what kinds do you usually enjoy, "
            "like fiction, mystery, or nonfiction?"
        )
    return f"You mentioned loving books. {stripped}"
