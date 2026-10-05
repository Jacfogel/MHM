"""
Task templates for quick task creation.

Built-in and user-defined templates prefill common fields; callers may override
title, due, priority, tags, etc.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from core.error_handling import ValidationError, handle_errors


MAX_CUSTOM_TASK_TEMPLATES = 20
CUSTOM_TASK_TEMPLATE_FIELDS = {
    "display_name",
    "title",
    "description",
    "priority",
    "tags",
    "default_due_time",
    "recurrence_pattern",
    "recurrence_interval",
}
_VALID_PRIORITIES = {"low", "medium", "high", "urgent", "critical"}
_VALID_RECURRENCE_PATTERNS = {None, "daily", "weekly", "monthly", "yearly"}
_CUSTOM_TEMPLATE_ID = re.compile(r"custom_[a-z0-9_]{1,100}")
_TIME_VALUE = re.compile(r"(?:[01]\d|2[0-3]):[0-5]\d")


@dataclass(frozen=True)
class TaskTemplate:
    """Static defaults for a repeatable task type."""

    template_id: str
    display_name: str
    title: str
    description: str = ""
    priority: str = "medium"
    category: str = ""
    tags: tuple[str, ...] = ()
    default_due_phrase: str | None = None
    default_due_time: str | None = None
    recurrence_pattern: str | None = None
    recurrence_interval: int = 1
    aliases: tuple[str, ...] = ()

    @handle_errors("building task template create kwargs", default_return={})
    def to_create_kwargs(self) -> dict[str, Any]:
        """Return non-empty template fields suitable for task creation."""
        data: dict[str, Any] = {
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "category": self.category,
            "tags": list(self.tags),
        }
        if self.recurrence_pattern:
            data["recurrence_pattern"] = self.recurrence_pattern
            data["recurrence_interval"] = self.recurrence_interval
        return data


_BUILTIN_TEMPLATES: dict[str, TaskTemplate] = {
    "medication": TaskTemplate(
        template_id="medication",
        display_name="Medication",
        title="Take medication",
        description="Remember to take prescribed medication.",
        priority="high",
        category="health",
        tags=("health", "medication"),
        default_due_phrase="today",
        default_due_time="08:00",
        recurrence_pattern="daily",
        aliases=("meds", "medicine", "pill", "pills"),
    ),
    "appointment": TaskTemplate(
        template_id="appointment",
        display_name="Appointment",
        title="Appointment",
        description="Schedule or attend an appointment.",
        priority="high",
        category="health",
        tags=("appointment", "health"),
        default_due_phrase="this week",
        aliases=("appt", "doctor", "dentist"),
    ),
    "phone_call": TaskTemplate(
        template_id="phone_call",
        display_name="Phone call",
        title="Call",
        description="Call someone back or make a scheduled call.",
        priority="medium",
        category="communication",
        tags=("phone", "call"),
        default_due_phrase="this week",
        aliases=("call", "phone"),
    ),
    "cleaning": TaskTemplate(
        template_id="cleaning",
        display_name="Cleaning / chores",
        title="Clean",
        description="Household cleaning or chore task.",
        priority="medium",
        category="home",
        tags=("chores", "home"),
        default_due_phrase="this week",
        aliases=("chore", "chores", "housework", "clean"),
    ),
    "paperwork": TaskTemplate(
        template_id="paperwork",
        display_name="Paperwork / forms",
        title="Paperwork / forms",
        description="Forms, paperwork, or administrative task.",
        priority="medium",
        category="admin",
        tags=("paperwork", "forms", "admin"),
        default_due_phrase="this week",
        aliases=("forms", "admin", "documents"),
    ),
}

# Map alias -> canonical template_id (built once at import).
_ALIAS_INDEX: dict[str, str] = {}
for _template in _BUILTIN_TEMPLATES.values():
    _ALIAS_INDEX[_template.template_id] = _template.template_id
    for _alias in _template.aliases:
        _ALIAS_INDEX[_alias.lower()] = _template.template_id


@handle_errors("listing built-in task templates", default_return=[])
def list_builtin_templates() -> list[TaskTemplate]:
    """Return built-in templates in stable display order."""
    order = ("medication", "appointment", "phone_call", "cleaning", "paperwork")
    return [_BUILTIN_TEMPLATES[tid] for tid in order if tid in _BUILTIN_TEMPLATES]


@handle_errors("normalizing task template reference", default_return="")
def _template_reference(value: str) -> str:
    """Return the command-friendly form of a template name."""
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", value.casefold())).strip(
        "_"
    )


@handle_errors("normalizing custom task templates", default_return={}, re_raise=True)
def normalize_custom_task_templates(
    value: Any, *, strict: bool = False
) -> dict[str, dict[str, Any]]:
    """Return canonical safe custom-template records.

    ``strict`` is used by settings writes so malformed input is rejected instead
    of silently dropped. Runtime reads stay tolerant of manually edited files.
    """

    if not isinstance(value, dict):
        if strict:
            raise ValidationError("Custom task templates must use an object.")
        return {}
    if len(value) > MAX_CUSTOM_TASK_TEMPLATES:
        if strict:
            raise ValidationError(
                f"Add at most {MAX_CUSTOM_TASK_TEMPLATES} custom task templates."
            )
        return {}

    normalized: dict[str, dict[str, Any]] = {}
    references: set[str] = set(_ALIAS_INDEX)
    for template_id, record in value.items():
        if (
            not isinstance(template_id, str)
            or _CUSTOM_TEMPLATE_ID.fullmatch(template_id) is None
            or not isinstance(record, dict)
            or set(record) != CUSTOM_TASK_TEMPLATE_FIELDS
        ):
            if strict:
                raise ValidationError("Check each custom task template.")
            continue

        display_name = record.get("display_name")
        title = record.get("title")
        description = record.get("description")
        priority = record.get("priority")
        tags = record.get("tags")
        due_time = record.get("default_due_time")
        recurrence = record.get("recurrence_pattern")
        interval = record.get("recurrence_interval")
        reference = _template_reference(display_name) if isinstance(display_name, str) else ""
        valid = (
            isinstance(display_name, str)
            and bool(display_name.strip())
            and len(display_name.strip()) <= 80
            and bool(reference)
            and reference not in references
            and isinstance(title, str)
            and bool(title.strip())
            and len(title.strip()) <= 500
            and isinstance(description, str)
            and len(description) <= 10000
            and priority in _VALID_PRIORITIES
            and isinstance(tags, list)
            and len(tags) <= 20
            and all(
                isinstance(tag, str) and bool(tag.strip()) and len(tag.strip()) <= 100
                for tag in tags
            )
            and (due_time in (None, "") or (
                isinstance(due_time, str) and _TIME_VALUE.fullmatch(due_time)
            ))
            and recurrence in _VALID_RECURRENCE_PATTERNS
            and type(interval) is int
            and 1 <= interval <= 365
        )
        if not valid:
            if strict:
                raise ValidationError(
                    "Check each custom task template and use unique names."
                )
            continue
        references.add(reference)
        display_name_value = display_name.strip() if isinstance(display_name, str) else ""
        title_value = title.strip() if isinstance(title, str) else ""
        description_value = description.strip() if isinstance(description, str) else ""
        priority_value = priority if isinstance(priority, str) else "medium"
        tag_values = tags if isinstance(tags, list) else []
        due_time_value = due_time if isinstance(due_time, str) and due_time else None
        recurrence_value = recurrence if isinstance(recurrence, str) else None
        interval_value = interval if type(interval) is int else 1
        normalized[template_id] = {
            "display_name": display_name_value,
            "title": title_value,
            "description": description_value,
            "priority": priority_value,
            "tags": list(
                dict.fromkeys(
                    tag.strip().casefold()
                    for tag in tag_values
                    if isinstance(tag, str)
                )
            ),
            "default_due_time": due_time_value,
            "recurrence_pattern": recurrence_value,
            "recurrence_interval": interval_value,
        }
    return normalized


@handle_errors("listing custom task templates", default_return=[])
def list_custom_templates(value: Any) -> list[TaskTemplate]:
    """Build runtime templates from saved preference records."""
    templates = []
    for template_id, record in normalize_custom_task_templates(value).items():
        templates.append(
            TaskTemplate(
                template_id=template_id,
                display_name=record["display_name"],
                title=record["title"],
                description=record["description"],
                priority=record["priority"],
                tags=tuple(record["tags"]),
                default_due_time=record["default_due_time"],
                recurrence_pattern=record["recurrence_pattern"],
                recurrence_interval=record["recurrence_interval"],
            )
        )
    return templates


@handle_errors("looking up custom task template", default_return=None)
def get_custom_template(value: Any, name_or_id: str) -> TaskTemplate | None:
    """Find a saved custom template by id, display name, or command reference."""
    if not isinstance(name_or_id, str) or not name_or_id.strip():
        return None
    wanted = _template_reference(name_or_id)
    for template in list_custom_templates(value):
        if name_or_id.strip().casefold() == template.template_id.casefold():
            return template
        if wanted == _template_reference(template.display_name):
            return template
    return None


@handle_errors("building custom task template reference", default_return="")
def custom_template_reference(template: TaskTemplate) -> str:
    """Return the readable command reference for a custom template."""
    return _template_reference(template.display_name)


@handle_errors("looking up built-in task template id", default_return=None)
def lookup_builtin_template_id(name: str) -> str | None:
    """Match a user-facing template name or synonym to a canonical built-in template_id."""
    if not name or not isinstance(name, str):
        return None
    normalized = name.strip().lower().replace("-", "_").replace(" ", "_")
    if not normalized:
        return None
    if normalized in _BUILTIN_TEMPLATES:
        return normalized
    return _ALIAS_INDEX.get(normalized)


@handle_errors("loading task template", default_return=None)
def get_template(template_id: str) -> TaskTemplate | None:
    """Return a built-in template by canonical id, or None."""
    resolved = lookup_builtin_template_id(template_id)
    if not resolved:
        return None
    return _BUILTIN_TEMPLATES.get(resolved)


@handle_errors("building task template form defaults", default_return=None)
def template_form_defaults(template_id: str) -> dict[str, str] | None:
    """Return Discord/modal field defaults for a built-in template."""
    template = get_template(template_id)
    if not template:
        return None
    modal_title = f"Create: {template.display_name}"
    return {
        "template_id": template.template_id,
        "modal_title": modal_title[:45],
        "title": template.title,
        "description": template.description,
        "due": template.default_due_phrase or "",
        "tags": ", ".join(template.tags),
    }


@handle_errors("formatting task templates for help", default_return="")
def format_templates_for_help() -> str:
    """Short bullet list for help text."""
    lines = []
    for template in list_builtin_templates():
        alias_hint = ""
        if template.aliases:
            alias_hint = f" (also: {', '.join(template.aliases[:2])})"
        lines.append(f"• `{template.template_id}` — {template.display_name}{alias_hint}")
    return "\n".join(lines)
