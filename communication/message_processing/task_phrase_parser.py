"""Pull due dates, times, priority, tags, links, and recurrence out of a task phrase."""

from __future__ import annotations

import re
from typing import Any

from core.error_handling import handle_errors
from core.logger import get_component_logger

logger = get_component_logger("ai")


@handle_errors("extracting task entities", default_return={})
def extract_task_entities(
    title: str, *, user_id: str | None = None, original_message: str = ""
) -> dict[str, Any]:
    """Extract task-related entities from a task title."""
    try:
        from core.natural_language_defaults import get_natural_language_defaults

        nl_defaults = get_natural_language_defaults(user_id)
        time_defaults = nl_defaults.time_of_day_defaults
        entities: dict[str, Any] = {}
        urls, clean_title = extract_task_urls(title, original_message=original_message)
        if urls:
            entities["links"] = [{"url": url} for url in urls]

        # Extract due date - order matters! More specific patterns first
        due_patterns = [
            r"in\s+(\d+)\s+hours?",  # "in 48 hours", "in 1 hour" - check before days
            r"in\s+(\d+)\s+days?",  # "in 11 days", "in 1 day", "in 6 days"
            r"in\s+(\d+)\s+weeks?",  # "in 2 weeks", "in 1 week"
            r"tomorrow\s+(?:morning|afternoon|evening|night)",
            r"tomorrow\s+at\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?|noon|midnight)",
            r"today\s+at\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?|noon|midnight)",
            r"next\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+at\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?|noon|midnight)",
            r"next\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
            r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+at\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?|noon|midnight)",
            r"before\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
            r"by\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)(?!\s+\d)",
            r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
            r"after\s+(?:work|school)",
            r"this\s+week",
            r"tonight",
            r"tomorrow",
            r"next\s+week",
            r"next\s+month",
            r"on\s+(\w+\s+\d+)",
            r"by\s+(\w+\s+\d+)",
        ]

        best_match = None
        best_pattern_index = -1

        for i, pattern in enumerate(due_patterns):
            match = re.search(pattern, clean_title, re.IGNORECASE)
            if match and (
                best_match is None
                or len(match.group(0)) > len(best_match.group(0))
                or i < best_pattern_index
            ):
                best_match = match
                best_pattern_index = i

        if best_match:
            matched_phrase = best_match.group(0)
            entities["due_date"] = matched_phrase
            clean_title = remove_task_phrase(clean_title, matched_phrase)

            tomorrow_tod = re.search(
                r"tomorrow\s+(morning|afternoon|evening|night)",
                matched_phrase,
                re.IGNORECASE,
            )
            if tomorrow_tod:
                entities["due_date"] = "tomorrow"
                entities["due_time"] = time_defaults.get(tomorrow_tod.group(1).lower())
            elif len(best_match.groups()) >= 2 and best_match.group(2):
                time_str = best_match.group(2).strip()
                entities["due_time"] = time_str
            elif len(best_match.groups()) >= 1 and best_match.group(1):
                time_only_match = re.match(
                    r"(\d{1,2}(?::\d{2})?\s*(?:am|pm)?|noon|midnight)",
                    best_match.group(1).strip(),
                    re.IGNORECASE,
                )
                if time_only_match and re.search(r"\bat\s+", matched_phrase, re.IGNORECASE):
                    entities["due_time"] = time_only_match.group(1)
            elif matched_phrase.lower() == "tonight":
                entities["due_time"] = nl_defaults.tonight_start_time
            elif re.match(r"after\s+(?:work|school)", matched_phrase, re.IGNORECASE):
                entities["due_time"] = nl_defaults.after_work_school_time

        recurrence = extract_recurrence_entities(title)
        if recurrence:
            entities.update(
                {
                    key: value
                    for key, value in recurrence.items()
                    if key != "matched_text"
                }
            )
            matched_text = recurrence.get("matched_text")
            if isinstance(matched_text, str) and matched_text:
                clean_title = remove_task_phrase(clean_title, matched_text)
            if "due_time" in recurrence:
                clean_title = remove_task_phrase(
                    clean_title, f"at {recurrence['due_time']}"
                )

        priority_patterns = {
            "low": [
                r"\bnot\s+urgent\b",
                r"\blow\s+priority\b",
                r"\bwhen\s+convenient\b",
                r"\bno\s+rush\b",
            ],
            "critical": [r"\bcritical\b"],
            "urgent": [r"(?<!not\s)\burgent\b", r"\basap\b"],
            "high": [r"\bimportant\b", r"\bhigh\s+priority\b"],
            "medium": [r"\bmedium\s+priority\b"],
        }

        for priority, patterns in priority_patterns.items():
            for pattern in patterns:
                if re.search(pattern, clean_title, re.IGNORECASE):
                    entities["priority"] = priority
                    clean_title = re.sub(pattern, "", clean_title, flags=re.IGNORECASE)
                    break
            if "priority" in entities:
                break

        from core.tags import parse_tags_from_text

        clean_title, tags = parse_tags_from_text(clean_title)
        if tags:
            entities["tags"] = tags

        if "due_time" not in entities:
            time_match = re.search(
                r"\bat\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?|noon|midnight)\b",
                clean_title,
                re.IGNORECASE,
            )
            if time_match:
                entities["due_time"] = time_match.group(1)
                clean_title = remove_task_phrase(clean_title, time_match.group(0))

        clean_title = normalize_task_title(clean_title)
        if clean_title:
            entities["clean_title"] = clean_title
        return entities
    except Exception as e:
        logger.error(f"Error extracting task entities: {e}")
        return {}


@handle_errors("extracting URLs from task title", default_return=([], ""))
def extract_task_urls(
    title: str, *, original_message: str = ""
) -> tuple[list[str], str]:
    """Strip web links from a create-task title and return them separately."""
    from tasks.task_link_helpers import extract_urls_from_text, restore_url_case

    urls, remainder = extract_urls_from_text(title)
    if original_message:
        urls = [restore_url_case(url, original_message) or url for url in urls]
    return urls, remainder


@handle_errors("extracting recurrence entities", default_return={})
def extract_recurrence_entities(title: str) -> dict[str, Any]:
    """Extract recurrence fields from natural task text."""
    title_lower = title.lower()
    result: dict[str, Any] = {}

    interval_match = re.search(
        r"\bevery\s+(\d+)\s+(days?|weeks?|months?|years?)\b", title_lower
    )
    if interval_match:
        unit = interval_match.group(2)
        result["recurrence_pattern"] = recurrence_unit_to_pattern(unit)
        result["recurrence_interval"] = int(interval_match.group(1))
        result["matched_text"] = interval_match.group(0)
    else:
        simple_patterns = [
            (r"\bevery\s+(?:day|morning|afternoon|evening|night)\b", "daily"),
            (r"\bdaily\b", "daily"),
            (r"\bevery\s+week\b", "weekly"),
            (r"\bweekly\b", "weekly"),
            (r"\bevery\s+month\b", "monthly"),
            (r"\bmonthly\b", "monthly"),
            (r"\bevery\s+year\b", "yearly"),
            (r"\byearly\b", "yearly"),
            (
                r"\bevery\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
                "weekly",
            ),
        ]
        for pattern, recurrence_pattern in simple_patterns:
            match = re.search(pattern, title_lower)
            if match:
                result["recurrence_pattern"] = recurrence_pattern
                result["recurrence_interval"] = 1
                result["matched_text"] = match.group(0)
                if match.groups():
                    result["due_date"] = match.group(1)
                break

    time_match = re.search(
        r"\bat\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?|noon|midnight)\b",
        title_lower,
    )
    if result and time_match:
        result["due_time"] = time_match.group(1)

    return result


@handle_errors("mapping recurrence unit to pattern", default_return=None)
def recurrence_unit_to_pattern(unit: str) -> str | None:
    """Map a plural natural-language recurrence unit to a task recurrence pattern."""
    unit = unit.lower().rstrip("s")
    return {
        "day": "daily",
        "week": "weekly",
        "month": "monthly",
        "year": "yearly",
    }.get(unit)


@handle_errors("removing task phrase", default_return="")
def remove_task_phrase(title: str, phrase: str) -> str:
    """Remove a parsed metadata phrase from a task title."""
    if not phrase:
        return title
    return re.sub(re.escape(phrase), "", title, flags=re.IGNORECASE).strip()


@handle_errors("normalizing task title", default_return="")
def normalize_task_title(title: str) -> str:
    """Normalize whitespace and dangling connectors after entity extraction."""
    title = re.sub(r"\s+", " ", title).strip()
    title = re.sub(r"^\s*[:\-]\s*", "", title)
    title = re.sub(
        r"\s+(?:by|on|at|every|repeat(?:s|ing)?|due)$",
        "",
        title,
        flags=re.IGNORECASE,
    )
    title = re.sub(r"\s+,$", "", title).strip()
    return title
