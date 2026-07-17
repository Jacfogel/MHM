"""Product-AI action catalog metadata backed by parser intent names."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from core.error_handling import handle_errors


@dataclass(frozen=True)
class AIActionField:
    """One action entity field expected by an existing handler."""

    name: str
    required: bool = False
    description: str = ""


@dataclass(frozen=True)
class AIActionDefinition:
    """Catalog entry for one product action routed through existing command handlers."""

    action_name: str
    intent: str
    domain: str
    handler_name: str | None
    fields: list[AIActionField] = field(default_factory=list)
    feature_requirements: list[str] = field(default_factory=list)
    requires_confirmation: bool = False
    result_shape: dict[str, str] = field(default_factory=dict)
    source: str = "structured_command_dispatcher"

    @property
    @handle_errors("getting required action fields", default_return=[])
    def required_fields(self) -> list[str]:
        """Return entity field names required before this action can execute."""
        return [field.name for field in self.fields if field.required]

    # not_duplicate: action_catalog_serialization
    @handle_errors("serializing AI action definition", default_return={})
    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation for context envelopes."""
        return {
            "action_name": self.action_name,
            "intent": self.intent,
            "domain": self.domain,
            "handler_name": self.handler_name,
            "fields": [
                {
                    "name": field.name,
                    "required": field.required,
                    "description": field.description,
                }
                for field in self.fields
            ],
            "required_fields": self.required_fields,
            "feature_requirements": list(self.feature_requirements),
            "requires_confirmation": self.requires_confirmation,
            "result_shape": dict(self.result_shape),
            "source": self.source,
        }


@dataclass(frozen=True)
class AIActionRequest:
    """Model-planned action request before communication-layer dispatch."""

    action_name: str
    entities: dict[str, Any]
    confidence: float
    source_message: str
    requires_confirmation: bool = False


ResponseIntent = Literal["answer_only", "execute_action", "clarify"]


@dataclass(frozen=True)
class AIActionPlan:
    """Product-AI planning output before execution or conversational reply."""

    response_intent: ResponseIntent
    actions: tuple[AIActionRequest, ...] = ()
    clarification_question: str | None = None
    response_notes: str | None = None
    source_message: str = ""
    planning_method: str = "unknown"


@dataclass(frozen=True)
class AIActionCatalog:
    """Collection of product-AI actions indexed by canonical action name."""

    actions: dict[str, AIActionDefinition]

    @handle_errors("getting AI action definition", default_return=None)
    def get(self, action_name: str) -> AIActionDefinition | None:
        """Return a catalog action by canonical action name."""
        return self.actions.get(action_name)

    @handle_errors("building AI action prompt summary", default_return="Actions: none available.")
    def to_prompt_summary(self) -> str:
        """Return compact action metadata for model prompts."""
        if not self.actions:
            return "Actions: none available."
        parts = []
        for action in self.actions.values():
            required = ", ".join(action.required_fields) or "none"
            parts.append(f"{action.action_name} ({action.domain}; required: {required})")
        return "Actions: " + "; ".join(parts)

    @handle_errors(
        "building AI action planning prompt summary",
        default_return="none",
    )
    def to_planning_prompt_summary(self) -> str:
        """Return a short action-name list for local-model planning prompts.

        Names only (comma-separated). Common task/check-in/profile actions are
        listed first so small models are less biased by alphabetical order.
        Required-field checks happen in the planner parser.
        """
        if not self.actions:
            return "none"
        priority = [
            name for name in _PRIORITY_PLANNING_ACTIONS if name in self.actions
        ]
        rest = sorted(
            name for name in self.actions if name not in _PRIORITY_PLANNING_ACTIONS
        )
        return ", ".join(priority + rest)

    # not_duplicate: action_catalog_serialization
    @handle_errors("serializing AI action catalog", default_return={})
    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable catalog representation."""
        return {
            "available": sorted(self.actions),
            "actions": {
                name: action.to_dict() for name, action in sorted(self.actions.items())
            },
        }


_TASK_ACTION_FIELDS: dict[str, list[AIActionField]] = {
    "create_task": [
        AIActionField("title", True, "Task title or reminder text."),
        AIActionField("description", False, "Optional task notes."),
        AIActionField("due_date", False, "Optional due date or date phrase."),
        AIActionField("due_time", False, "Optional due time."),
        AIActionField("priority", False, "low, medium, or high."),
        AIActionField("tags", False, "Optional task tags."),
        AIActionField("group", False, "Optional task group."),
    ],
    "create_task_from_template": [
        AIActionField("template_ref", True, "Built-in task template id or name."),
        AIActionField("title", False, "Optional title override."),
    ],
    "list_task_templates": [],
    "list_tasks": [
        AIActionField("filter", False, "Optional list filter."),
        AIActionField("priority", False, "Optional priority filter."),
        AIActionField("tag", False, "Optional tag filter."),
        AIActionField("group", False, "Optional group filter."),
    ],
    "complete_task": [
        AIActionField("task_identifier", False, "Task number, id, short id, or title.")
    ],
    "uncomplete_task": [
        AIActionField("task_identifier", True, "Completed task id, short id, or title.")
    ],
    "delete_task": [
        AIActionField("task_identifier", True, "Task number, id, short id, or title.")
    ],
    "update_task": [
        AIActionField("task_identifier", True, "Task number, id, short id, or title."),
        AIActionField("title", False, "New task title."),
        AIActionField("description", False, "Replacement task notes."),
        AIActionField("due_date", False, "New due date."),
        AIActionField("due_time", False, "New due time."),
        AIActionField("priority", False, "New priority."),
    ],
    "append_note_to_task": [
        AIActionField("task_identifier", True, "Task number, id, short id, or title."),
        AIActionField("note_text", True, "Text to append to task notes."),
    ],
    "task_stats": [
        AIActionField("days", False, "Lookback window in days."),
        AIActionField("period_name", False, "Named period such as this week."),
    ],
    "task_analytics": [
        AIActionField("days", False, "Lookback window in days."),
    ],
    "show_create_hub": [],
}

_CHECKIN_ACTION_FIELDS: dict[str, list[AIActionField]] = {
    "start_checkin": [],
    "checkin_status": [],
    "checkin_history": [
        AIActionField("limit", False, "Maximum number of recent check-ins to show."),
        AIActionField("days", False, "Lookback window in days."),
    ],
    "checkin_analysis": [
        AIActionField("days", False, "Lookback window in days."),
    ],
    "completion_rate": [
        AIActionField("days", False, "Lookback window in days."),
    ],
    "quant_summary": [
        AIActionField("days", False, "Lookback window in days."),
    ],
}

_PROFILE_ACTION_FIELDS: dict[str, list[AIActionField]] = {
    "show_profile": [],
    "update_profile": [
        AIActionField("name", False, "Preferred name."),
        AIActionField("gender_identity", False, "Gender identity value."),
        AIActionField("email", False, "Account email address."),
    ],
    "profile_stats": [],
}

_SCHEDULE_ACTION_FIELDS: dict[str, list[AIActionField]] = {
    "show_schedule": [
        AIActionField("category", False, "tasks, checkins, messages, or all."),
    ],
    "update_schedule": [
        AIActionField("action", True, "enable or disable."),
        AIActionField("category", True, "tasks, checkins, or messages."),
    ],
    "schedule_status": [],
    "add_schedule_period": [
        AIActionField("period_name", True, "Name for the new schedule period."),
        AIActionField("category", True, "tasks, checkins, or messages."),
        AIActionField("start_time", True, "Period start time."),
        AIActionField("end_time", True, "Period end time."),
        AIActionField("days", False, "Optional weekday list."),
        AIActionField("active", False, "Whether the period starts active."),
    ],
    "edit_schedule_period": [
        AIActionField("period_name", True, "Existing period name."),
        AIActionField("category", True, "tasks, checkins, or messages."),
        AIActionField("new_start_time", False, "Updated start time."),
        AIActionField("new_end_time", False, "Updated end time."),
    ],
}

_ANALYTICS_ACTION_FIELDS: dict[str, list[AIActionField]] = {
    "show_analytics": [
        AIActionField("days", False, "Lookback window in days."),
    ],
    "mood_trends": [
        AIActionField("days", False, "Lookback window in days."),
    ],
    "energy_trends": [
        AIActionField("days", False, "Lookback window in days."),
    ],
    "habit_analysis": [
        AIActionField("days", False, "Lookback window in days."),
    ],
    "sleep_analysis": [
        AIActionField("days", False, "Lookback window in days."),
    ],
    "wellness_score": [
        AIActionField("days", False, "Lookback window in days."),
    ],
}

_NOTEBOOK_ACTION_FIELDS: dict[str, list[AIActionField]] = {
    "create_note": [
        AIActionField("title", False, "Note title."),
        AIActionField("description", False, "Note body text."),
        AIActionField("tags", False, "Optional tags."),
        AIActionField("group", False, "Optional notebook group."),
    ],
    "create_quick_note": [
        AIActionField("title", False, "Quick note title."),
        AIActionField("tags", False, "Optional tags."),
        AIActionField("group", False, "Optional notebook group."),
    ],
    "create_journal": [
        AIActionField("title", False, "Journal entry title."),
        AIActionField("description", False, "Journal entry body."),
        AIActionField("tags", False, "Optional tags."),
        AIActionField("group", False, "Optional notebook group."),
    ],
    "create_list": [
        AIActionField("title", True, "List title."),
        AIActionField("items", False, "Initial list items."),
        AIActionField("tags", False, "Optional tags."),
    ],
    "list_recent_entries": [
        AIActionField("limit", False, "Maximum entries to return."),
        AIActionField("offset", False, "Pagination offset."),
    ],
    "list_recent_notes": [
        AIActionField("limit", False, "Maximum notes to return."),
        AIActionField("offset", False, "Pagination offset."),
    ],
    "show_entry": [
        AIActionField("entry_ref", True, "Entry id, short id, title, or list name."),
    ],
    "append_to_entry": [
        AIActionField("entry_ref", True, "Entry id, short id, title, or list name."),
        AIActionField("text", True, "Text to append."),
    ],
    "set_entry_body": [
        AIActionField("entry_ref", True, "Entry id, short id, title, or list name."),
        AIActionField("text", True, "Replacement body text."),
    ],
    "add_tags_to_entry": [
        AIActionField("entry_ref", True, "Entry id, short id, title, or list name."),
        AIActionField("tags", True, "Tags to add."),
    ],
    "remove_tags_from_entry": [
        AIActionField("entry_ref", True, "Entry id, short id, title, or list name."),
        AIActionField("tags", True, "Tags to remove."),
    ],
    "search_entries": [
        AIActionField("query", True, "Search text."),
    ],
    "pin_entry": [
        AIActionField("entry_ref", True, "Entry id, short id, title, or list name."),
    ],
    "unpin_entry": [
        AIActionField("entry_ref", True, "Entry id, short id, title, or list name."),
    ],
    "archive_entry": [
        AIActionField("entry_ref", True, "Entry id, short id, title, or list name."),
    ],
    "unarchive_entry": [
        AIActionField("entry_ref", True, "Entry id, short id, title, or list name."),
    ],
    "add_list_item": [
        AIActionField("entry_ref", True, "List id, short id, title, or name."),
        AIActionField("item_text", True, "List item text."),
    ],
    "toggle_list_item_done": [
        AIActionField("entry_ref", True, "List id, short id, title, or name."),
        AIActionField("item_index", True, "One-based list item index."),
    ],
    "toggle_list_item_undone": [
        AIActionField("entry_ref", True, "List id, short id, title, or name."),
        AIActionField("item_index", True, "One-based list item index."),
    ],
    "remove_list_item": [
        AIActionField("entry_ref", True, "List id, short id, title, or name."),
        AIActionField("item_index", True, "One-based list item index."),
    ],
    "set_entry_group": [
        AIActionField("entry_ref", True, "Entry id, short id, title, or list name."),
        AIActionField("group", True, "Target notebook group."),
    ],
    "list_entries_by_group": [
        AIActionField("group", True, "Notebook group name."),
    ],
    "list_entries_by_tag": [
        AIActionField("tag", True, "Tag name."),
    ],
    "list_pinned_entries": [],
    "list_inbox_entries": [],
    "list_archived_entries": [],
}

_HELP_ACTION_FIELDS: dict[str, list[AIActionField]] = {
    "help": [
        AIActionField("topic", False, "Optional help topic such as tasks or checkin."),
    ],
    "commands": [],
    "examples": [
        AIActionField("category", False, "Optional examples category."),
    ],
    "status": [],
    "messages": [],
}

_HEALTH_ACTION_FIELDS: dict[str, list[AIActionField]] = {
    "connect_google_health": [],
    "google_health_status": [],
    "pause_google_health": [],
    "enable_google_health": [],
    "delete_google_health_data": [],
    "sync_google_health": [],
}

_PREFERENCES_ACTION_FIELDS: dict[str, list[AIActionField]] = {
    "show_natural_language_defaults": [],
    "update_natural_language_defaults": [
        AIActionField("nl_field", True, "Phrase field such as tonight or after_work."),
        AIActionField("nl_value", True, "Replacement time or value."),
    ],
}

_ACTION_FIELDS: dict[str, list[AIActionField]] = {
    **_TASK_ACTION_FIELDS,
    **_CHECKIN_ACTION_FIELDS,
    **_PROFILE_ACTION_FIELDS,
    **_SCHEDULE_ACTION_FIELDS,
    **_ANALYTICS_ACTION_FIELDS,
    **_NOTEBOOK_ACTION_FIELDS,
    **_HELP_ACTION_FIELDS,
    **_HEALTH_ACTION_FIELDS,
    **_PREFERENCES_ACTION_FIELDS,
}

_INTENT_DOMAIN: dict[str, str] = {
    intent: domain
    for domain, fields in (
        ("tasks", _TASK_ACTION_FIELDS),
        ("checkins", _CHECKIN_ACTION_FIELDS),
        ("profile", _PROFILE_ACTION_FIELDS),
        ("schedules", _SCHEDULE_ACTION_FIELDS),
        ("analytics", _ANALYTICS_ACTION_FIELDS),
        ("notebooks", _NOTEBOOK_ACTION_FIELDS),
        ("help", _HELP_ACTION_FIELDS),
        ("health", _HEALTH_ACTION_FIELDS),
        ("preferences", _PREFERENCES_ACTION_FIELDS),
    )
    for intent in fields
}

_INTENT_HANDLER: dict[str, str] = {
    "show_create_hub": "CreateMenuHandler",
    "task_stats": "AnalyticsHandler",
    "task_analytics": "AnalyticsHandler",
    "checkin_history": "AnalyticsHandler",
    "checkin_analysis": "AnalyticsHandler",
    "completion_rate": "AnalyticsHandler",
    "quant_summary": "AnalyticsHandler",
    "show_analytics": "AnalyticsHandler",
    "mood_trends": "AnalyticsHandler",
    "energy_trends": "AnalyticsHandler",
    "habit_analysis": "AnalyticsHandler",
    "sleep_analysis": "AnalyticsHandler",
    "wellness_score": "AnalyticsHandler",
    "show_natural_language_defaults": "NaturalLanguageHandler",
    "update_natural_language_defaults": "NaturalLanguageHandler",
}

_INTENT_FEATURES: dict[str, list[str]] = {
    "messages": ["automated_messages"],
    "show_schedule": ["automated_messages"],
    "update_schedule": ["automated_messages"],
    "schedule_status": ["automated_messages"],
    "add_schedule_period": ["automated_messages"],
    "edit_schedule_period": ["automated_messages"],
    "start_checkin": ["checkins"],
    "checkin_status": ["checkins"],
    "checkin_history": ["checkins"],
    "checkin_analysis": ["checkins"],
    "completion_rate": ["checkins"],
    "quant_summary": ["checkins"],
    "show_analytics": ["checkins"],
    "mood_trends": ["checkins"],
    "energy_trends": ["checkins"],
    "habit_analysis": ["checkins"],
    "sleep_analysis": ["checkins"],
    "wellness_score": ["checkins"],
    "task_analytics": ["task_management"],
    "task_stats": ["task_management"],
    "connect_google_health": ["google_health"],
    "google_health_status": ["google_health"],
    "pause_google_health": ["google_health"],
    "enable_google_health": ["google_health"],
    "delete_google_health_data": ["google_health"],
    "sync_google_health": ["google_health"],
}

_DOMAIN_FEATURES = {
    "tasks": ["task_management"],
    "checkins": ["checkins"],
    "schedules": ["automated_messages"],
    "notebooks": ["notebook"],
    "health": ["google_health"],
}

_DELETE_ACTIONS = {
    "delete_task",
    "remove_list_item",
    "delete_google_health_data",
}

# Shown first in planning prompts so small models bias toward common intents.
_PRIORITY_PLANNING_ACTIONS = (
    "create_task",
    "list_tasks",
    "complete_task",
    "update_task",
    "delete_task",
    "append_note_to_task",
    "uncomplete_task",
    "task_stats",
    "start_checkin",
    "checkin_status",
    "checkin_history",
    "show_profile",
    "update_profile",
    "profile_stats",
    "show_schedule",
    "schedule_status",
    "help",
    "status",
    "messages",
)


@handle_errors("building AI action catalog", default_return=AIActionCatalog({}))
def build_action_catalog() -> AIActionCatalog:
    """Build action metadata from live parser intents without importing handlers."""
    intents = _get_live_intents()
    actions: dict[str, AIActionDefinition] = {}
    for intent in intents:
        domain = _infer_domain(intent)
        actions[intent] = AIActionDefinition(
            action_name=intent,
            intent=intent,
            domain=domain,
            handler_name=_handler_name_for_intent(intent, domain),
            fields=_fields_for_intent(intent),
            feature_requirements=_feature_requirements_for_intent(intent, domain),
            requires_confirmation=intent in _DELETE_ACTIONS,
            result_shape={
                "message": "user-visible handler response",
                "completed": "whether the handler completed the command",
                "rich_data": "optional structured metadata from handler",
                "suggestions": "optional follow-up suggestions",
                "error": "optional handler error string",
            },
        )
    return AIActionCatalog(actions=actions)


@handle_errors("getting AI action catalog", default_return=AIActionCatalog({}))
def get_action_catalog() -> AIActionCatalog:
    """Return a freshly built action catalog from live command infrastructure."""
    return build_action_catalog()


@handle_errors("getting live command intents", default_return=[])
def _get_live_intents() -> list[str]:
    """Return initialized parser intent names through the AI command registry."""
    from ai.prompts.command_registry import get_initialized_command_intent_names

    return get_initialized_command_intent_names()


@handle_errors("getting fields for action intent", default_return=[])
def _fields_for_intent(intent: str) -> list[AIActionField]:
    """Return declared entity fields for an action intent."""
    return list(_ACTION_FIELDS.get(intent, []))


@handle_errors("inferring action domain", default_return="general")
def _infer_domain(intent: str) -> str:
    """Infer product domain from canonical parser intent name."""
    if intent in _INTENT_DOMAIN:
        return _INTENT_DOMAIN[intent]
    if "checkin" in intent:
        return "checkins"
    if "profile" in intent:
        return "profile"
    if "schedule" in intent:
        return "schedules"
    if any(
        marker in intent for marker in ("analytics", "trends", "analysis", "score", "rate")
    ):
        return "analytics"
    if any(
        marker in intent
        for marker in ("note", "entry", "entries", "journal", "inbox", "pinned", "archive", "tag")
    ):
        return "notebooks"
    if "account" in intent:
        return "account"
    if "health" in intent or "google" in intent:
        return "health"
    if intent in {"help", "commands", "examples", "status", "messages"}:
        return "help"
    return "general"


@handle_errors("getting feature requirements for action intent", default_return=[])
def _feature_requirements_for_intent(intent: str, domain: str) -> list[str]:
    """Return feature gates for an action intent."""
    if intent in _INTENT_FEATURES:
        return list(_INTENT_FEATURES[intent])
    return list(_DOMAIN_FEATURES.get(domain, []))


@handle_errors("mapping action intent to handler name", default_return=None)
def _handler_name_for_intent(intent: str, domain: str) -> str | None:
    """Return the communication handler class name for an action intent."""
    if intent in _INTENT_HANDLER:
        return _INTENT_HANDLER[intent]
    return _handler_name_for_domain(domain)


@handle_errors("mapping action domain to handler name", default_return=None)
def _handler_name_for_domain(domain: str) -> str | None:
    """Return the default communication handler class name for a domain."""
    return {
        "tasks": "TaskManagementHandler",
        "checkins": "CheckinHandler",
        "profile": "ProfileHandler",
        "schedules": "ScheduleManagementHandler",
        "analytics": "AnalyticsHandler",
        "notebooks": "NotebookHandler",
        "account": "AccountManagementHandler",
        "help": "HelpHandler",
        "health": "HealthHandler",
        "preferences": "NaturalLanguageHandler",
    }.get(domain)
