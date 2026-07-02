# communication/message_processing/flows/flow_command_helpers.py

"""Shared keyword matching, timeout, and control-command handling for conversation flows."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import timedelta
from collections.abc import Callable

from core.time_utilities import now_datetime_full, parse_timestamp_full

from communication.message_processing.flows.flow_constants import (
    CONVERSATION_FLOW_TIMEOUT_MINUTES,
)

# ---------------------------------------------------------------------------
# Flow focus — which entity type the user is currently creating/editing
# ---------------------------------------------------------------------------
FLOW_FOCUS_TASK = "task"
FLOW_FOCUS_NOTE = "note"
FLOW_FOCUS_LIST = "list"
FLOW_FOCUS_JOURNAL = "journal"
FLOW_FOCUS_CHECKIN = "checkin"
FLOW_FOCUS_EVENT = "event"  # reserved for future calendar/event flows

# ---------------------------------------------------------------------------
# Flow step — what kind of input the current question expects
# ---------------------------------------------------------------------------
FLOW_STEP_FREE_TEXT = "free_text"  # note/journal body, list item lines
FLOW_STEP_DATE_TIME = "date_time"  # task due date and/or time
FLOW_STEP_PRIORITY = "priority"  # task priority level
FLOW_STEP_REMINDER = "reminder"  # task reminder periods

ENTITY_PREFIX_ALIASES: dict[str, list[str]] = {
    FLOW_FOCUS_NOTE: ["n", "note", "nn", "newn", "newnote"],
    FLOW_FOCUS_TASK: [
        "task",
        "t",
        "nt",
        "ntask",
        "newt",
        "newtask",
        "ct",
        "ctask",
        "createtask",
        "createt",
    ],
    FLOW_FOCUS_LIST: ["l", "list", "newl", "newlist", "cl", "createlist", "createl"],
    FLOW_FOCUS_JOURNAL: [
        "j",
        "journal",
        "njournal",
        "newjournal",
        "cjournal",
        "createjournal",
    ],
    FLOW_FOCUS_EVENT: [
        "e",
        "event",
        "nevent",
        "newevent",
        "cevent",
        "createevent",
    ],
}

GREETING_UNRELATED_PATTERN = re.compile(
    r"^(hi|hello|hey|thanks|thank you|bye|goodbye)\b"
)

# Cancel / stop synonyms (cancel = abandon creation)
_CANCEL_BASE_WORDS = ["cancel", "stop", "quit", "exit", "abort"]

# Pure keyword helpers below perform string matching only (no I/O).
# error_handling_exclude per AI_ERROR_HANDLING_GUIDE section 7.


# error_handling_exclude: pure keyword helper; no I/O
def _prefix_variants(word: str) -> list[str]:
    """Return bare, bang-prefixed, and slash-prefixed forms of a control word."""
    return [word, f"!{word}", f"/{word}"]


# error_handling_exclude: pure keyword helper; no I/O
def _expand_keyword_variants(base_words: list[str]) -> list[str]:
    """Expand each base word into all prefix variants for flow keyword lists."""
    keywords: list[str] = []
    for word in base_words:
        keywords.extend(_prefix_variants(word))
    return keywords


FLOW_CANCEL_KEYWORDS = _expand_keyword_variants(_CANCEL_BASE_WORDS)
FLOW_SKIP_ALL_KEYWORDS = _expand_keyword_variants(["skip all"])
FLOW_SKIP_QUESTION_KEYWORDS = _expand_keyword_variants(["skip question", "skip"])
FLOW_STEP_BACK_KEYWORDS = _expand_keyword_variants(["back", "undo"])
FLOW_FINISH_LIST_KEYWORDS = _expand_keyword_variants(
    ["end", "endlist", "endl", "skip all"]
)

FLOW_DISPATCH_KEYWORDS = frozenset(
    {
        *FLOW_SKIP_QUESTION_KEYWORDS,
        *FLOW_SKIP_ALL_KEYWORDS,
        *FLOW_CANCEL_KEYWORDS,
        *FLOW_STEP_BACK_KEYWORDS,
        *[kw for kw in FLOW_FINISH_LIST_KEYWORDS if kw not in FLOW_SKIP_ALL_KEYWORDS],
    }
)

# Explicit undo-creation button labels
TASK_FLOW_UNDO_CREATION_KEYWORDS = [
    "undo task creation",
    *_expand_keyword_variants(["delete task", "delete this task"]),
    *FLOW_CANCEL_KEYWORDS,
]
NOTE_FLOW_UNDO_CREATION_KEYWORDS = ["undo note creation", *FLOW_CANCEL_KEYWORDS]
JOURNAL_FLOW_UNDO_CREATION_KEYWORDS = ["undo entry creation", *FLOW_CANCEL_KEYWORDS]
LIST_FLOW_UNDO_CREATION_KEYWORDS = ["undo list creation", *FLOW_CANCEL_KEYWORDS]
TASK_FLOW_DELETE_TASK_KEYWORDS = ["delete task", "delete this task"]

# User-facing outcome messages
TASK_SAVED_MESSAGE = (
    "Task saved. You can update due date, priority, or reminders later from the task list."
)
TASK_NOT_SAVED_MESSAGE = "Task not saved. Creation cancelled."
TASK_STEP_BACK_MESSAGE = "Went back one step."
NOTE_SAVED_TITLE_ONLY_TEMPLATE = "Note saved: '{title}' ({short_id}) - body skipped."
NOTE_SAVED_WITH_BODY_TEMPLATE = "Note saved: '{title}' ({short_id})"
NOTE_NOT_SAVED_TEMPLATE = "Note not saved. '{title}' was discarded."
JOURNAL_SAVED_TITLE_ONLY_TEMPLATE = (
    "Journal entry saved: '{title}' ({short_id}) - body skipped."
)
JOURNAL_SAVED_WITH_BODY_TEMPLATE = "Journal entry saved: '{title}' ({short_id})"
JOURNAL_NOT_SAVED_TEMPLATE = "Journal entry not saved. '{title}' was discarded."
LIST_SAVED_TEMPLATE = "List saved: '{title}' ({short_id}) with {count} items."
LIST_NOT_SAVED_TEMPLATE = "List not saved. '{title}' was discarded."
LIST_STEP_BACK_REMOVED_TEMPLATE = "Removed last entry ({count} item(s)). {remaining} item(s) remaining."

# Backward compatible alias
TASK_FLOW_SKIP_ALL_MESSAGE = TASK_SAVED_MESSAGE


# error_handling_exclude: pure keyword helper; no I/O
def message_matches_keyword(
    message_lower: str,
    keywords: list[str],
    *,
    allow_prefix: bool = True,
) -> bool:
    """Return True when *message_lower* equals or starts with a keyword phrase."""
    for keyword in keywords:
        if message_lower == keyword:
            return True
        if allow_prefix and message_lower.startswith(keyword + " "):
            return True
    return False


# error_handling_exclude: pure keyword helper; no I/O
def is_skip_all_message(message_lower: str) -> bool:
    """Return True when the user wants to finish with defaults for remaining steps."""
    return message_matches_keyword(message_lower, FLOW_SKIP_ALL_KEYWORDS)


# error_handling_exclude: pure keyword helper; no I/O
def is_skip_question_message(message_lower: str) -> bool:
    """Return True when the user wants to skip only the current question."""
    return message_matches_keyword(message_lower, FLOW_SKIP_QUESTION_KEYWORDS)


# error_handling_exclude: pure keyword helper; no I/O
def is_cancel_message(message_lower: str) -> bool:
    """Return True when the user wants to abandon creation (cancel/stop/quit/etc.)."""
    return message_matches_keyword(message_lower, FLOW_CANCEL_KEYWORDS)


# error_handling_exclude: pure keyword helper; no I/O
def is_step_back_message(
    message_lower: str,
    *,
    undo_creation_phrases: list[str] | None = None,
) -> bool:
    """Step back one question; excludes explicit undo-creation phrases."""
    for phrase in undo_creation_phrases or []:
        if message_lower == phrase or message_lower.startswith(phrase + " "):
            return False
    return message_matches_keyword(message_lower, FLOW_STEP_BACK_KEYWORDS)


# error_handling_exclude: pure keyword helper; no I/O
def is_finish_list_message(message_lower: str) -> bool:
    """Return True when the user wants to end list item entry."""
    return message_matches_keyword(message_lower, FLOW_FINISH_LIST_KEYWORDS)


# error_handling_exclude: pure keyword helper; no I/O
def is_delete_in_progress_message(
    message_lower: str,
    *,
    delete_phrases: list[str] | None = None,
) -> bool:
    """Return True when the user explicitly asked to delete the in-progress entity."""
    phrases = delete_phrases or TASK_FLOW_DELETE_TASK_KEYWORDS
    for phrase in phrases:
        if message_lower == phrase:
            return True
        if message_lower.startswith(phrase + " "):
            return True
    return False


# error_handling_exclude: pure keyword helper; no I/O
def is_flow_expired(
    user_state: dict,
    *,
    timeout_minutes: int = CONVERSATION_FLOW_TIMEOUT_MINUTES,
    timestamp_key: str = "started_at",
) -> bool:
    """Return True when the flow has been idle longer than *timeout_minutes*."""
    started_at_str = user_state.get(timestamp_key)
    if not started_at_str:
        return False
    started_at = parse_timestamp_full(started_at_str)
    if started_at is None:
        return False
    return (now_datetime_full() - started_at) > timedelta(minutes=timeout_minutes)


# error_handling_exclude: pure keyword helper; no I/O
def _entity_prefix_patterns(entity: str) -> list[str]:
    """Regex patterns for slash/bang and natural entity prefixes."""
    aliases = ENTITY_PREFIX_ALIASES.get(entity, [])
    if not aliases:
        return []
    group = "|".join(re.escape(alias) for alias in aliases)
    return [rf"^[/!]({group})\b", rf"^({entity})\b"]


# error_handling_exclude: pure keyword helper; no I/O
def _natural_language_create_pattern(entities: list[str]) -> str:
    """Regex for natural-language commands that mention one of *entities*."""
    entity_group = "|".join(re.escape(entity) for entity in entities)
    return rf"^(create|add|new|show|list|complete|delete|update)\b.*\b(?:{entity_group})\b"


# error_handling_exclude: pure keyword helper; no I/O
def is_unrelated_flow_message(
    message_lower: str,
    *,
    current_focus: str,
    step: str = FLOW_STEP_DATE_TIME,
) -> bool:
    """
    Return True when *message_lower* looks like a context switch, not a step answer.

    * ``FLOW_STEP_FREE_TEXT`` — only slash/bang commands and greetings are unrelated
      (journal/note body text may contain words like "create" or "new").
    * Structured steps (date/time, priority, reminder) — also treat natural-language
      commands for other entities as unrelated; step answers stay in-flow.
    """
    if GREETING_UNRELATED_PATTERN.match(message_lower):
        return True

    other_entities = [
        entity for entity in ENTITY_PREFIX_ALIASES if entity != current_focus
    ]
    prefix_patterns: list[str] = []
    for entity in other_entities:
        prefix_patterns.extend(_entity_prefix_patterns(entity))

    if any(re.match(pattern, message_lower) for pattern in prefix_patterns):
        return True

    if step == FLOW_STEP_FREE_TEXT:
        return False

    all_entities = list(ENTITY_PREFIX_ALIASES.keys())
    nl_pattern = _natural_language_create_pattern(all_entities)
    return bool(re.match(nl_pattern, message_lower))


# error_handling_exclude: pure keyword helper; no I/O
def build_unrelated_checker(
    current_focus: str,
    step: str,
) -> Callable[[str], bool]:
    """Return a closure that checks unrelated messages for a focus + step pair."""

    # error_handling_exclude: nested closure; caller uses decorated flow handlers
    def _checker(message_lower: str) -> bool:
        return is_unrelated_flow_message(
            message_lower,
            current_focus=current_focus,
            step=step,
        )

    return _checker


# Task-flow keyword helpers (entity-specific undo/step-back phrasing)


# error_handling_exclude: pure keyword helper; no I/O
def is_task_flow_undo_creation_message(message_lower: str) -> bool:
    """Return True for undo-task-creation or cancel phrases during task flow."""
    return message_matches_keyword(message_lower, TASK_FLOW_UNDO_CREATION_KEYWORDS)


# error_handling_exclude: pure keyword helper; no I/O
def is_task_flow_delete_in_progress_message(message_lower: str) -> bool:
    """Return True when the user asked to delete the in-progress task."""
    return is_delete_in_progress_message(message_lower)


# error_handling_exclude: pure keyword helper; no I/O
# not_duplicate: flow_step_back_per_flow
def is_task_flow_step_back_message(message_lower: str) -> bool:
    """Step back one task question; excludes undo-task-creation phrases."""
    return is_step_back_message(
        message_lower,
        undo_creation_phrases=["undo task creation", "undo task"],
    )


# error_handling_exclude: pure keyword helper; no I/O
# not_duplicate: flow_step_back_per_flow
def is_note_flow_step_back_message(message_lower: str) -> bool:
    """Step back one note question; excludes undo-note-creation phrases."""
    return is_step_back_message(
        message_lower,
        undo_creation_phrases=["undo note creation"],
    )


# error_handling_exclude: pure keyword helper; no I/O
# not_duplicate: flow_step_back_per_flow
def is_journal_flow_step_back_message(message_lower: str) -> bool:
    """Step back one journal question; excludes undo-entry-creation phrases."""
    return is_step_back_message(
        message_lower,
        undo_creation_phrases=["undo entry creation", "undo journal creation"],
    )


is_unrelated_task_due_date_message = build_unrelated_checker(
    FLOW_FOCUS_TASK, FLOW_STEP_DATE_TIME
)
is_unrelated_task_priority_message = build_unrelated_checker(
    FLOW_FOCUS_TASK, FLOW_STEP_PRIORITY
)
is_unrelated_task_reminder_message = build_unrelated_checker(
    FLOW_FOCUS_TASK, FLOW_STEP_REMINDER
)
is_unrelated_note_body_message = build_unrelated_checker(
    FLOW_FOCUS_NOTE, FLOW_STEP_FREE_TEXT
)
is_unrelated_journal_body_message = build_unrelated_checker(
    FLOW_FOCUS_JOURNAL, FLOW_STEP_FREE_TEXT
)
is_unrelated_list_items_message = build_unrelated_checker(
    FLOW_FOCUS_LIST, FLOW_STEP_FREE_TEXT
)


@dataclass(frozen=True)
class FlowControlHandlers:
    """Callbacks for shared multi-step flow control commands."""

    on_skip_all: Callable[[], tuple[str, bool]] | None = None
    on_skip_question: Callable[[], tuple[str, bool]] | None = None
    on_undo_creation: Callable[[], tuple[str, bool]] | None = None
    on_step_back: Callable[[], tuple[str, bool]] | None = None
    on_finish: Callable[[], tuple[str, bool]] | None = None
    is_unrelated: Callable[[str], bool] | None = None
    on_timeout_unrelated: Callable[[], tuple[str, bool]] | None = None
    on_unrelated_clear: Callable[[], tuple[str, bool]] | None = None
    skip_all_checker: Callable[[str], bool] = is_skip_all_message
    skip_question_checker: Callable[[str], bool] = is_skip_question_message
    undo_creation_checker: Callable[[str], bool] | None = None
    delete_in_progress_checker: Callable[[str], bool] | None = None
    step_back_checker: Callable[[str], bool] | None = None
    finish_checker: Callable[[str], bool] | None = None
    is_expired: Callable[[dict], bool] | None = None


# error_handling_exclude: dispatches to decorated flow callbacks; no I/O here
def try_flow_control_command(
    message_lower: str,
    user_state: dict,
    handlers: FlowControlHandlers,
) -> tuple[str, bool] | None:
    """
    Handle universal flow control keywords before step-specific parsing.

    Returns ``(reply, completed)`` when a control command matched, else ``None``.
    """
    if handlers.skip_all_checker(message_lower) and handlers.on_skip_all:
        return handlers.on_skip_all()

    undo_checker = handlers.undo_creation_checker or is_cancel_message
    if handlers.on_undo_creation and (
        undo_checker(message_lower)
        or (
            handlers.delete_in_progress_checker
            and handlers.delete_in_progress_checker(message_lower)
        )
    ):
        return handlers.on_undo_creation()

    step_back_checker = handlers.step_back_checker or (
        lambda msg: is_step_back_message(msg)
    )
    if handlers.on_step_back and step_back_checker(message_lower):
        return handlers.on_step_back()

    finish_checker = handlers.finish_checker or is_finish_list_message
    if handlers.on_finish and finish_checker(message_lower):
        return handlers.on_finish()

    if handlers.on_skip_question and handlers.skip_question_checker(message_lower):
        return handlers.on_skip_question()

    if handlers.is_unrelated and handlers.is_unrelated(message_lower):
        is_expired = handlers.is_expired or (
            lambda state: is_flow_expired(state)
        )
        if is_expired(user_state) and handlers.on_timeout_unrelated:
            return handlers.on_timeout_unrelated()
        if handlers.on_unrelated_clear:
            return handlers.on_unrelated_clear()

    return None
