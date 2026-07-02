"""Product-AI action catalog metadata backed by parser intent names."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

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


_TASK_FIELDS: dict[str, list[AIActionField]] = {
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
        AIActionField("note", True, "Text to append to task notes."),
    ],
    "task_stats": [],
}

_DOMAIN_FEATURES = {
    "tasks": ["task_management"],
    "checkins": ["checkins"],
    "messages": ["automated_messages"],
    "schedules": ["automated_messages"],
    "notebooks": ["notebook"],
    "health": ["google_health"],
}

_DELETE_ACTIONS = {"delete_task", "remove_list_item", "delete_message"}


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
            handler_name=_handler_name_for_domain(domain),
            fields=_fields_for_intent(intent),
            feature_requirements=_DOMAIN_FEATURES.get(domain, []),
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
    return list(_TASK_FIELDS.get(intent, []))


@handle_errors("inferring action domain", default_return="general")
def _infer_domain(intent: str) -> str:
    """Infer product domain from canonical parser intent name."""
    if intent in _TASK_FIELDS:
        return "tasks"
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


@handle_errors("mapping action domain to handler name", default_return=None)
def _handler_name_for_domain(domain: str) -> str | None:
    """Return the existing communication handler class name for a domain."""
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
    }.get(domain)
