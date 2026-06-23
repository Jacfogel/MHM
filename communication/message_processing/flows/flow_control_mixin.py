# communication/message_processing/flows/flow_control_mixin.py

"""Shared flow control behavior mixin for multi-step conversation flows."""

from __future__ import annotations

from dataclasses import replace
from collections.abc import Callable

from core.logger import get_component_logger

from communication.message_processing.flows.flow_command_helpers import (
    FlowControlHandlers,
    is_flow_expired,
    try_flow_control_command,
)
from communication.message_processing.flows.flow_constants import (
    CONVERSATION_FLOW_TIMEOUT_MINUTES,
)
from communication.message_processing.flows.flow_state import FlowStateMixin

logger = get_component_logger("communication_manager")


class FlowControlMixin(FlowStateMixin):
    """Common timeout and control-command handling for entity creation flows."""

    # error_handling_exclude: thin delegate; flow entry points are decorated
    def _is_flow_expired(
        self,
        user_state: dict,
        *,
        timeout_minutes: int = CONVERSATION_FLOW_TIMEOUT_MINUTES,
        timestamp_key: str = "started_at",
    ) -> bool:
        """Delegate to shared idle-timeout check for this flow's timestamp key."""
        return is_flow_expired(
            user_state,
            timeout_minutes=timeout_minutes,
            timestamp_key=timestamp_key,
        )

    # error_handling_exclude: called from decorated flow handlers
    def _clear_flow_silent(self, user_id: str) -> tuple[str, bool]:
        """Clear flow without user-facing message (hand off to next handler)."""
        self._clear_flow_state(user_id, mark_completion=True)
        return ("", True)

    # error_handling_exclude: orchestrates decorated callbacks on entity flows
    def _try_flow_control_command(
        self,
        user_id: str,
        user_state: dict,
        message_lower: str,
        handlers: FlowControlHandlers,
        *,
        flow_label: str = "flow",
    ) -> tuple[str, bool] | None:
        """Run shared control-command handling with default silent clear on unrelated."""
        if handlers.is_unrelated and handlers.on_unrelated_clear is None:
            handlers = replace(
                handlers,
                on_unrelated_clear=lambda: self._clear_flow_silent(user_id),
            )
        elif handlers.on_unrelated_clear is not None:
            original_clear = handlers.on_unrelated_clear

            # error_handling_exclude: nested helper; caller is decorated
            def _logged_clear() -> tuple[str, bool]:
                """Log unrelated-message flow clear then delegate to the flow handler."""
                logger.info(
                    f"User {user_id} in {flow_label} sent unrelated message, "
                    "clearing flow"
                )
                return original_clear()

            handlers = replace(handlers, on_unrelated_clear=_logged_clear)

        return try_flow_control_command(message_lower, user_state, handlers)

    # error_handling_exclude: factory only; handlers run under decorated callers
    def _build_flow_control_handlers(
        self,
        *,
        on_skip_all: Callable[[], tuple[str, bool]] | None = None,
        on_skip_question: Callable[[], tuple[str, bool]] | None = None,
        on_undo_creation: Callable[[], tuple[str, bool]] | None = None,
        on_step_back: Callable[[], tuple[str, bool]] | None = None,
        on_finish: Callable[[], tuple[str, bool]] | None = None,
        is_unrelated: Callable[[str], bool] | None = None,
        on_timeout_unrelated: Callable[[], tuple[str, bool]] | None = None,
        **kwargs,
    ) -> FlowControlHandlers:
        """Factory for ``FlowControlHandlers`` used by entity-specific flows."""
        return FlowControlHandlers(
            on_skip_all=on_skip_all,
            on_skip_question=on_skip_question,
            on_undo_creation=on_undo_creation,
            on_step_back=on_step_back,
            on_finish=on_finish,
            is_unrelated=is_unrelated,
            on_timeout_unrelated=on_timeout_unrelated,
            **kwargs,
        )
