"""Canonical product-AI context envelope construction."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core import get_user_data
from core.error_handling import handle_errors
from core.health_context_builder import build_safe_health_guidance_summary
from core.response_tracking import get_recent_chat_interactions
from core.schedule_utilities import get_active_schedules
from core.time_utilities import now_timestamp_full


@dataclass(frozen=True)
class AIContextSection:
    """One normalized context section and its AI-facing prompt text."""

    name: str
    data: Any
    prompt_text: str = ""
    included: bool = True
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AIContextEnvelope:
    """Structured product-AI context for a single user request."""

    metadata: dict[str, Any]
    sections: dict[str, AIContextSection]

    @property
    @handle_errors("getting structured AI context", default_return={})
    def structured(self) -> dict[str, Any]:
        """Return structured data keyed by section name."""
        return {name: section.data for name, section in self.sections.items()}

    @property
    @handle_errors("getting AI prompt sections", default_return={})
    def prompt_sections(self) -> dict[str, str]:
        """Return compact prompt text for included sections."""
        return {
            name: section.prompt_text
            for name, section in self.sections.items()
            if section.included and section.prompt_text
        }

    @property
    @handle_errors("getting included AI context sections", default_return=[])
    def included_sections(self) -> list[str]:
        """Return included section names in insertion order."""
        return [
            name
            for name, section in self.sections.items()
            if section.included and section.prompt_text
        ]

    @handle_errors("joining AI prompt text", default_return="")
    def to_prompt_text(self) -> str:
        """Join included prompt sections into a compact context block."""
        return "\n".join(self.prompt_sections.values())


@handle_errors("building AI context envelope", default_return=None)
def build_ai_context_envelope(
    user_id: str,
    *,
    active_channel: str | None = None,
    requested_intent: str | None = None,
    include_conversation_history: bool = True,
    prompt_request: str | None = None,
) -> AIContextEnvelope | None:
    """Build the canonical structured context envelope for product AI."""

    user_data = get_user_data(user_id, "all", normalize_on_read=True) or {}
    account = _unwrap_section(user_data, "account")
    preferences = _unwrap_section(user_data, "preferences")
    personal_context = _unwrap_section(user_data, "context")
    schedules = _unwrap_section(user_data, "schedules")

    sections: dict[str, AIContextSection] = {}
    sections["account"] = _section(
        "account",
        account,
        _format_account(account),
        source='get_user_data("all").account',
    )
    sections["preferences"] = _section(
        "preferences",
        preferences,
        _format_preferences(preferences),
        source='get_user_data("all").preferences',
    )
    sections["personal_context"] = _section(
        "personal_context",
        personal_context,
        _format_personal_context(personal_context),
        source='get_user_data("all").context',
    )
    sections["schedules"] = _section(
        "schedules",
        _build_schedule_context(schedules),
        source='get_user_data("all").schedules',
    )
    sections["tasks"] = _section("tasks", _build_task_context(user_id), source="tasks.task_service")
    sections["checkins"] = _section(
        "checkins", _build_checkin_context(user_id), source="checkins.checkin_service"
    )
    sections["messages"] = _section(
        "messages",
        _build_message_context(user_id, preferences),
        source="messages.message_data_manager",
    )
    sections["notebooks"] = _section(
        "notebooks", _build_notebook_context(user_id), source="notebook.notebook_service"
    )
    sections["health"] = _section(
        "health", _build_health_context(user_id), source="core.health_context_builder"
    )
    sections["analytics"] = _section("analytics", _build_analytics_context(sections))
    sections["conversation"] = _section(
        "conversation",
        _build_conversation_context(user_id, include_conversation_history),
        source="core.response_tracking",
    )
    sections["action_catalog"] = _section(
        "action_catalog",
        _build_action_catalog_context(),
        source="ai.action_catalog",
    )

    selected_sections = _select_prompt_sections(prompt_request, sections)
    if selected_sections is not None:
        sections = {
            name: _replace_included(section, name in selected_sections)
            for name, section in sections.items()
        }

    metadata = {
        "user_id": user_id,
        "current_timestamp": now_timestamp_full(),
        "timezone": account.get("timezone") or preferences.get("timezone"),
        "active_channel": active_channel,
        "requested_intent": requested_intent,
        "context_version": 1,
        "included_sections": [
            name for name, section in sections.items() if section.included
        ],
    }
    return AIContextEnvelope(metadata=metadata, sections=sections)


@handle_errors(
    "creating AI context section",
    default_return=AIContextSection(name="", data={}, included=False),
)
def _section(
    name: str,
    data: Any,
    prompt_text: str | None = None,
    *,
    included: bool = True,
    source: str = "",
    metadata: dict[str, Any] | None = None,
) -> AIContextSection:
    """Create a normalized context section with optional prompt text."""
    if prompt_text is None:
        prompt_text = _default_prompt_text(name, data)
    prompt_text = str(prompt_text or "")
    return AIContextSection(
        name=name,
        data=data,
        prompt_text=prompt_text,
        included=included,
        source=source,
        metadata=metadata or {},
    )


@handle_errors("updating AI context section inclusion", default_return=None)
def _replace_included(section: AIContextSection, included: bool) -> AIContextSection:
    """Return a copy of a context section with a new inclusion flag."""
    return AIContextSection(
        name=section.name,
        data=section.data,
        prompt_text=section.prompt_text,
        included=included,
        source=section.source,
        metadata=section.metadata,
    )


@handle_errors("unwrapping user data section", default_return={})
def _unwrap_section(user_data: dict[str, Any], section_name: str) -> dict[str, Any]:
    """Return a normalized section payload from get_user_data output."""
    section = user_data.get(section_name)
    if isinstance(section, dict) and isinstance(section.get(section_name), dict):
        return section[section_name]
    return section if isinstance(section, dict) else {}


@handle_errors("formatting account context", default_return="")
def _format_account(account: dict[str, Any]) -> str:
    """Format account fields into compact prompt text."""
    bits = []
    if account.get("preferred_name"):
        bits.append(f"preferred name {account['preferred_name']}")
    if account.get("internal_username"):
        bits.append(f"username {account['internal_username']}")
    features = account.get("features") or {}
    enabled = sorted(k for k, v in features.items() if v == "enabled")
    if enabled:
        bits.append("enabled features " + ", ".join(enabled))
    return "Account: " + "; ".join(bits) if bits else "Account: no account details."


@handle_errors("formatting preferences context", default_return="")
def _format_preferences(preferences: dict[str, Any]) -> str:
    """Format preference fields into compact prompt text."""
    categories = preferences.get("categories") or []
    channel = (preferences.get("channel") or {}).get("type")
    bits = []
    if categories:
        bits.append("categories " + ", ".join(str(c) for c in categories))
    if channel:
        bits.append(f"channel {channel}")
    if preferences.get("task_settings"):
        bits.append("task settings available")
    return "Preferences: " + "; ".join(bits) if bits else "Preferences: none loaded."


@handle_errors("formatting personal context", default_return="")
def _format_personal_context(personal_context: dict[str, Any]) -> str:
    """Format personal context fields into compact prompt text."""
    bits = []
    for key, label in (
        ("goals", "goals"),
        ("notes_for_ai", "AI notes"),
        ("activities_for_encouragement", "encouraging activities"),
        ("interests", "interests"),
    ):
        values = personal_context.get(key) or []
        if values:
            bits.append(f"{label}: {', '.join(str(v) for v in values[:5])}")
    custom_fields = personal_context.get("custom_fields") or {}
    if custom_fields:
        bits.append("custom context fields available")
    return "Personal context: " + "; ".join(bits) if bits else "Personal context: none loaded."


@handle_errors("building schedule context", default_return={})
def _build_schedule_context(schedules: dict[str, Any]) -> dict[str, Any]:
    """Build structured schedule context and active schedule summary."""
    return {
        "raw": schedules,
        "active_schedules": get_active_schedules(schedules) if schedules else [],
    }


@handle_errors("building task context", default_return={})
def _build_task_context(user_id: str) -> dict[str, Any]:
    """Build structured task context through task service APIs."""
    from tasks import are_tasks_enabled
    from tasks import task_service

    active = task_service.load_active_tasks(user_id) or []
    completed = task_service.load_completed_tasks(user_id) or []
    due_soon = task_service.get_tasks_due_soon(user_id, days_ahead=7) or []
    stats = task_service.get_user_task_stats(user_id) or {}
    return {
        "enabled": are_tasks_enabled(user_id),
        "active": active,
        "completed_summary": completed[:10],
        "due_soon": due_soon,
        "stats": stats,
        "recurring_defaults": task_service.get_recurring_task_defaults(user_id),
    }


@handle_errors("building check-in context", default_return={})
def _build_checkin_context(user_id: str) -> dict[str, Any]:
    """Build structured check-in context through check-in service APIs."""
    from checkins.checkin_service import get_checkin_start_status, get_recent_checkin_summary

    summary = get_recent_checkin_summary(user_id, limit=10)
    start_status = get_checkin_start_status(user_id)
    return {
        "enabled": summary.enabled,
        "recent": summary.entries,
        "latest": summary.entries[0] if summary.entries else None,
        "daily_status": {
            "already_completed_today": start_status.already_completed_today,
            "last_checkin_timestamp": start_status.last_checkin_timestamp,
        },
    }


@handle_errors("building message context", default_return={})
def _build_message_context(user_id: str, preferences: dict[str, Any]) -> dict[str, Any]:
    """Build structured message context through message data APIs."""
    from messages.message_data_manager import (
        get_recent_messages,
        is_automated_messages_enabled,
        load_user_messages,
    )

    categories = list(preferences.get("categories") or [])
    templates_by_category = {
        category: load_user_messages(user_id, category)[:5] for category in categories
    }
    return {
        "enabled": is_automated_messages_enabled(user_id),
        "categories": categories,
        "recent_sent": get_recent_messages(user_id, limit=10),
        "templates_by_category": templates_by_category,
    }


@handle_errors("building notebook context", default_return={})
def _build_notebook_context(user_id: str) -> dict[str, Any]:
    """Build structured notebook context through notebook service APIs."""
    from notebook import notebook_service

    recent = notebook_service.list_recent_entries(user_id, limit=10)
    return {
        "recent": [_entry_to_dict(entry) for entry in recent.entries],
        "total_recent": recent.total,
    }


@handle_errors("building health context", default_return={})
def _build_health_context(user_id: str) -> dict[str, Any]:
    """Build safe AI-facing health guidance context."""
    summary = build_safe_health_guidance_summary(user_id)
    return {"guidance_summary": summary, "available": bool(summary)}


@handle_errors("building analytics context", default_return={})
def _build_analytics_context(sections: dict[str, AIContextSection]) -> dict[str, Any]:
    """Build compact analytics summaries from already-loaded context sections."""
    task_data = sections["tasks"].data if "tasks" in sections else {}
    checkin_data = sections["checkins"].data if "checkins" in sections else {}
    message_data = sections["messages"].data if "messages" in sections else {}
    return {
        "task_counts": (task_data or {}).get("stats", {}),
        "recent_checkin_count": len((checkin_data or {}).get("recent") or []),
        "recent_message_count": len((message_data or {}).get("recent_sent") or []),
    }


@handle_errors("building conversation context", default_return={})
def _build_conversation_context(
    user_id: str, include_conversation_history: bool
) -> dict[str, Any]:
    """Build recent conversation context when enabled."""
    if not include_conversation_history:
        return {"recent_chat_interactions": []}
    return {"recent_chat_interactions": get_recent_chat_interactions(user_id, limit=5)}


@handle_errors("building action catalog context", default_return={})
def _build_action_catalog_context() -> dict[str, Any]:
    """Build action catalog context for prompt/action planning."""
    from ai.action_catalog import get_action_catalog

    catalog = get_action_catalog()
    return {**catalog.to_dict(), "summary": catalog.to_prompt_summary()}


@handle_errors("converting notebook entry to dict", default_return={})
def _entry_to_dict(entry: Any) -> dict[str, Any]:
    """Convert notebook entries or dict-like values to plain dictionaries."""
    if hasattr(entry, "model_dump"):
        return entry.model_dump(mode="json")
    return dict(entry) if isinstance(entry, dict) else {"value": str(entry)}


@handle_errors("building default prompt section text", default_return="")
def _default_prompt_text(name: str, data: Any) -> str:
    """Build compact prompt text for a context section."""
    if name == "schedules":
        active = (data or {}).get("active_schedules") or []
        return f"Schedules: {len(active)} active schedule periods."
    if name == "tasks":
        active = (data or {}).get("active") or []
        due_soon = (data or {}).get("due_soon") or []
        return f"Tasks: {len(active)} active; {len(due_soon)} due soon."
    if name == "checkins":
        recent = (data or {}).get("recent") or []
        enabled = (data or {}).get("enabled")
        return f"Check-ins: {'enabled' if enabled else 'disabled'}; {len(recent)} recent."
    if name == "messages":
        categories = (data or {}).get("categories") or []
        recent = (data or {}).get("recent_sent") or []
        return f"Messages: categories {', '.join(categories) if categories else 'none'}; {len(recent)} recent sent."
    if name == "notebooks":
        return f"Notebooks: {(data or {}).get('total_recent', 0)} recent entries."
    if name == "health":
        summary = (data or {}).get("guidance_summary") or "no health guidance summary."
        return f"Health: {summary}"
    if name == "analytics":
        return f"Analytics: {data}"
    if name == "conversation":
        recent = (data or {}).get("recent_chat_interactions") or []
        return f"Conversation: {len(recent)} recent chat interactions."
    if name == "action_catalog":
        return (data or {}).get("summary") or "Actions: none available."
    return f"{name}: {data}"


@handle_errors("selecting prompt sections", default_return=None)
def _select_prompt_sections(
    prompt_request: str | None, sections: dict[str, AIContextSection]
) -> set[str] | None:
    """Select prompt sections relevant to the current user request."""
    if not prompt_request:
        return None

    request = prompt_request.lower()
    selected = {
        "account",
        "preferences",
        "personal_context",
        "tasks",
        "conversation",
    }
    keyword_sections = {
        "checkins": ("check-in", "checkin", "mood", "energy", "wellness"),
        "schedules": ("schedule", "window", "reminder time"),
        "messages": ("message", "sent", "category"),
        "notebooks": ("note", "notebook", "journal", "list"),
        "health": ("health", "sleep", "rest", "recovery"),
        "analytics": ("trend", "summary", "analytics", "stats"),
    }
    for section_name, keywords in keyword_sections.items():
        if any(keyword in request for keyword in keywords):
            selected.add(section_name)
    return selected & set(sections)
