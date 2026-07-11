# ai/conversational_context/action_boundaries.py

"""Detect conversational text that falsely claims completed CRUD or data actions."""

from __future__ import annotations

import re
from re import Pattern

from core.error_handling import handle_errors

# Reply when the user message has no interpretable intent (e.g. digits only).
UNCLEAR_USER_INPUT_REPLY = (
    "I'm not sure what you mean by that. "
    "Could you rephrase, or tell me what you'd like help with?"
)

_UNINTERPRETABLE_PROMPT_PATTERN = re.compile(r"^\d+$")

# Regex patterns for completed-action claims (conversational / fallback review).
# Offering help ("I can help you create...") must not match these.
_FALSE_CRUD_CLAIM_PATTERNS: tuple[tuple[str, Pattern[str]], ...] = (
    (
        "claims task/item was created",
        re.compile(
            r"\bi(?:'ve| have)? created\b|\b(?:successfully|done!)\s+.{0,25}created\b"
            r"|\b(?:task|reminder).{0,40}(?:has been|was) (?:created|added)\b"
            r"|\btask has been added\b",
            re.IGNORECASE,
        ),
    ),
    (
        "claims item was updated or deleted",
        re.compile(
            r"\bi(?:'ve| have)? (?:updated|deleted|removed|saved|completed|scheduled)\b"
            r"|\b(?:has been|was) (?:updated|deleted|removed|saved|completed|scheduled)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "claims action was completed on user's behalf",
        re.compile(
            r"\bi(?:'ve| have)? (?:set up|configured) (?:your |the )?"
            r"(?:task|schedule|reminder|check-?in)\b"
            r"|\bi(?:'ve| have)? completed that for you\b"
            r"|\bdone!\s+i(?:'ve| have)?\b",
            re.IGNORECASE,
        ),
    ),
    (
        "claims data access or analysis not shown in context",
        re.compile(
            r"\bbased on your recent data\b|\bi noticed a pattern\b"
            r"|\bi(?:'ve| have)? accessed your\b",
            re.IGNORECASE,
        ),
    ),
)

# Simple substrings used by fallback response tests (subset of regex coverage).
FALSE_CRUD_SUCCESS_SUBSTRINGS: tuple[str, ...] = (
    "i created",
    "i've created",
    "i have created",
    "task has been added",
    "has been created",
    "successfully created",
    "i deleted",
    "i've deleted",
    "i updated",
    "i've updated",
    "i completed",
    "i've completed",
    "i saved",
    "i've saved",
    "based on your recent data",
    "i noticed a pattern",
)


@handle_errors("checking for uninterpretable user prompt", default_return=False)
def is_uninterpretable_user_prompt(text: str) -> bool:
    """True when the message has no letters and is not a usable command or question."""
    stripped = (text or "").strip()
    if not stripped:
        return True
    if _UNINTERPRETABLE_PROMPT_PATTERN.fullmatch(stripped):
        return True
    if not re.search(r"[a-zA-Z]", stripped):
        return True
    return False


@handle_errors("detecting false CRUD claims in text", default_return=[])
def find_false_crud_claims(text: str) -> list[str]:
    """Return human-readable labels for false completed-action claims in *text*."""
    if not text or not isinstance(text, str):
        return []
    matches: list[str] = []
    for label, pattern in _FALSE_CRUD_CLAIM_PATTERNS:
        if pattern.search(text):
            matches.append(label)
    return matches


@handle_errors("checking for false CRUD claims in text", default_return=False)
def response_has_false_crud_claim(text: str) -> bool:
    """True when *text* appears to claim a CRUD action completed without evidence."""
    return bool(find_false_crud_claims(text))
