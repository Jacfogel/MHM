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

# Explicit personal facts stated by the user in recent turns.
_STATED_FACT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "favorite_color",
        re.compile(
            r"(?i)\bmy favorite color(?:'?s)?\s+(?:is|was|=)\s+([a-z][a-z\s-]{1,30})\b"
        ),
    ),
    (
        "name",
        re.compile(r"(?i)\bmy name(?:'?s)?\s+(?:is|=)\s+([A-Za-z][A-Za-z\s'-]{1,40})\b"),
    ),
    (
        "favorite_food",
        re.compile(
            r"(?i)\bmy favorite (?:food|meal|dish)(?:'?s)?\s+(?:is|was|=)\s+"
            r"([a-z][a-z\s'-]{1,40})\b"
        ),
    ),
)

_FACT_FOLLOW_UP_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "favorite_color",
        re.compile(
            r"(?i)\b(?:what(?:'?s| is)|do you (?:know|remember))\s+"
            r"(?:my favorite color|the color i (?:like|love|prefer))\b"
        ),
    ),
    (
        "name",
        re.compile(r"(?i)\b(?:what(?:'?s| is)|do you (?:know|remember))\s+my name\b"),
    ),
    (
        "favorite_food",
        re.compile(
            r"(?i)\b(?:what(?:'?s| is)|do you (?:know|remember))\s+"
            r"my favorite (?:food|meal|dish)\b"
        ),
    ),
)

_FACT_LABELS = {
    "favorite_color": "favorite color",
    "name": "name",
    "favorite_food": "favorite food",
}


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


@handle_errors("extracting stated conversation facts", default_return={})
def extract_stated_conversation_facts(
    conversation_history: list[dict[str, Any]],
    *,
    lookback: int = 5,
) -> dict[str, str]:
    """Extract explicit personal facts the user stated in recent turns."""
    facts: dict[str, str] = {}
    if not conversation_history:
        return facts

    for chat in list(conversation_history)[-lookback:]:
        user_msg = str(chat.get("user_message") or "").strip()
        if not user_msg:
            continue
        for key, pattern in _STATED_FACT_PATTERNS:
            match = pattern.search(user_msg)
            if not match:
                continue
            value = re.sub(r"\s+", " ", match.group(1).strip(" .,!?;:'\"")).strip()
            if value:
                facts[key] = value
    return facts


@handle_errors("detecting fact follow-up keys", default_return=set())
def detect_fact_follow_up_keys(user_prompt: str) -> set[str]:
    """Return fact keys the current user prompt is asking about."""
    if not user_prompt:
        return set()
    keys: set[str] = set()
    for key, pattern in _FACT_FOLLOW_UP_PATTERNS:
        if pattern.search(user_prompt):
            keys.add(key)
    return keys


@handle_errors("reinforcing stated conversation facts", default_return="")
def reinforce_stated_facts_if_needed(
    user_prompt: str,
    response: str,
    conversation_history: list[dict[str, Any]],
) -> str:
    """
    If the user asks about a fact they already stated and the reply omits it,
    answer with the stated fact instead of a vague or forgetful reply.
    """
    if not user_prompt:
        return response

    asked_keys = detect_fact_follow_up_keys(user_prompt)
    if not asked_keys:
        return response

    facts = extract_stated_conversation_facts(conversation_history)
    missing: list[tuple[str, str]] = []
    lowered = (response or "").lower()
    for key in asked_keys:
        value = facts.get(key)
        if not value:
            continue
        if value.lower() in lowered:
            continue
        missing.append((key, value))

    if not missing:
        return response

    # Prefer a direct factual answer when the model forgot the stated value.
    if len(missing) == 1:
        key, value = missing[0]
        label = _FACT_LABELS.get(key, key.replace("_", " "))
        return f"Your {label} is {value}."

    parts = [
        f"your {_FACT_LABELS.get(key, key.replace('_', ' '))} is {value}"
        for key, value in missing
    ]
    if len(parts) == 2:
        return f"{parts[0].capitalize()}, and {parts[1]}."
    return f"{', '.join(parts[:-1])}, and {parts[-1]}.".capitalize()


@handle_errors("aligning response to conversation topic", default_return="")
def align_response_to_conversation_topic(
    user_prompt: str,
    response: str,
    conversation_history: list[dict[str, Any]],
) -> str:
    """Tie follow-up answers back to a topic or fact the user raised recently."""
    if not user_prompt:
        return response

    response = reinforce_stated_facts_if_needed(
        user_prompt, response, conversation_history
    )
    if not response:
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
