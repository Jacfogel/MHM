# communication/command_handlers/handler_registry.py

"""Lazy-loaded interaction handler registry (single import site per handler)."""

from __future__ import annotations

from dataclasses import dataclass

from core.error_handling import handle_errors
from core.logger import get_component_logger

from communication.command_handlers.base_handler import InteractionHandler

logger = get_component_logger("communication_manager")


@dataclass(frozen=True)
class _HandlerSpec:
    module_path: str
    class_name: str


_HANDLER_SPECS: dict[str, _HandlerSpec] = {
    "TaskManagementHandler": _HandlerSpec(
        "communication.command_handlers.task_handler", "TaskManagementHandler"
    ),
    "CheckinHandler": _HandlerSpec(
        "communication.command_handlers.checkin_handler", "CheckinHandler"
    ),
    "ProfileHandler": _HandlerSpec(
        "communication.command_handlers.profile_handler", "ProfileHandler"
    ),
    "ScheduleManagementHandler": _HandlerSpec(
        "communication.command_handlers.schedule_handler", "ScheduleManagementHandler"
    ),
    "AnalyticsHandler": _HandlerSpec(
        "communication.command_handlers.analytics_handler", "AnalyticsHandler"
    ),
    "NotebookHandler": _HandlerSpec(
        "communication.command_handlers.notebook_handler", "NotebookHandler"
    ),
    "AccountManagementHandler": _HandlerSpec(
        "communication.command_handlers.account_handler", "AccountManagementHandler"
    ),
    "CreateMenuHandler": _HandlerSpec(
        "communication.command_handlers.create_menu_handler", "CreateMenuHandler"
    ),
    "NaturalLanguageHandler": _HandlerSpec(
        "communication.command_handlers.natural_language_handler",
        "NaturalLanguageHandler",
    ),
}


@handle_errors("importing interaction handler class", default_return=None)
def _import_handler_class(spec: _HandlerSpec) -> type[InteractionHandler] | None:
    import importlib

    module = importlib.import_module(spec.module_path)
    return getattr(module, spec.class_name)


@handle_errors("lazy-loading interaction handler", default_return=None)
def _load_handler(
    registry_key: str,
    handlers: dict[str, InteractionHandler | None],
) -> InteractionHandler | None:
    if handlers.get(registry_key) is not None:
        return handlers[registry_key]

    spec = _HANDLER_SPECS.get(registry_key)
    if spec is None:
        return None

    handler_cls = _import_handler_class(spec)
    if handler_cls is None:
        return None

    instance = handler_cls()
    handlers[registry_key] = instance
    return instance


@handle_errors("loading interaction handlers", default_return=None)
def ensure_handlers_loaded(
    handlers: dict[str, InteractionHandler | None],
    *,
    preload_all: bool = False,
) -> None:
    """Load handler modules once."""
    keys_to_load = list(_HANDLER_SPECS.keys()) if preload_all else list(_HANDLER_SPECS.keys())
    for key in keys_to_load:
        if handlers.get(key) is None:
            _load_handler(key, handlers)


@handle_errors("getting interaction handler for intent", default_return=None)
def get_handler_for_intent(
    handlers: dict[str, InteractionHandler | None],
    intent: str,
) -> InteractionHandler | None:
    """Return the first registered handler that accepts the intent."""
    ensure_handlers_loaded(handlers, preload_all=True)
    for handler in handlers.values():
        if handler and handler.can_handle(intent):
            return handler
    return None


@handle_errors("getting loaded interaction handlers", default_return={})
def get_loaded_handlers(
    handlers: dict[str, InteractionHandler | None],
) -> dict[str, InteractionHandler]:
    """Return all non-None handler instances, loading any that are still unset."""
    ensure_handlers_loaded(handlers, preload_all=True)
    return {key: value for key, value in handlers.items() if value is not None}
