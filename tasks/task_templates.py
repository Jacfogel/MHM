"""
Built-in task templates for quick task creation.

Templates prefill common fields; callers may override title, due, priority, tags, etc.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.error_handling import handle_errors


@dataclass(frozen=True)
class TaskTemplate:
    """Static defaults for a repeatable task type."""

    template_id: str
    display_name: str
    title: str
    description: str = ""
    priority: str = "medium"
    category: str = ""
    group: str = ""
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
            "group": self.group,
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
        group="health",
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
        group="appointments",
        tags=("appointment", "health"),
        default_due_phrase="this week",
        aliases=("appt", "doctor", "dentist"),
    ),
    "phone_call": TaskTemplate(
        template_id="phone_call",
        display_name="Phone call",
        title="Phone call",
        description="Call someone back or make a scheduled call.",
        priority="medium",
        category="communication",
        group="calls",
        tags=("phone", "call"),
        aliases=("call", "phone"),
    ),
    "cleaning": TaskTemplate(
        template_id="cleaning",
        display_name="Cleaning / chores",
        title="Cleaning / chore",
        description="Household cleaning or chore task.",
        priority="medium",
        category="home",
        group="chores",
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
        group="paperwork",
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
