"""Execute AI action plans through existing command handlers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai.chat.action_planner import get_action_planner
from ai.context.assembly import assemble_action_result_messages
from ai.prompts.action_catalog import AIActionPlan, AIActionRequest
from communication.command_handlers.shared_types import InteractionResponse
from communication.message_processing.structured_command_dispatcher import (
    dispatch_structured_command,
)
from core.error_handling import handle_errors
from core.logger import get_component_logger

logger = get_component_logger("communication_manager")


@handle_errors("loading action request helper module", default_return=None)
def _load_action_request_helpers():
    """Load action request conversion helpers for plan execution."""
    from importlib import import_module

    return import_module("communication.message_processing.action_request_adapter")


@dataclass(frozen=True)
class ActionExecutionResult:
    """Product-AI execution outcome for one planned interaction."""

    plan: AIActionPlan
    response: InteractionResponse
    metadata: Any | None = None


class ActionPlanExecutor:
    """Route AIActionPlan outcomes through chat or structured command dispatch."""

    @handle_errors("executing action plan", default_return=None)
    def execute_plan(
        self,
        plan: AIActionPlan,
        user_id: str,
        channel_type: str,
        *,
        command_parser,
        ai_chatbot,
        enable_ai_enhancement: bool,
        command_definitions,
    ) -> ActionExecutionResult | None:
        """Execute a plan and return the user-visible response plus metadata."""
        if plan is None:
            return None

        if plan.response_intent == "clarify":
            question = (
                plan.clarification_question
                or "Could you share a bit more detail about what you'd like?"
            )
            return ActionExecutionResult(
                plan=plan,
                response=InteractionResponse(question, True),
            )

        if plan.response_intent == "answer_only":
            response_text = ai_chatbot.generate_response(
                plan.source_message,
                user_id=user_id,
                mode="chat",
            )
            return ActionExecutionResult(
                plan=plan,
                response=InteractionResponse(response_text, True),
            )

        if plan.response_intent == "execute_action":
            return self._execute_planned_actions(
                plan,
                user_id,
                channel_type,
                command_parser=command_parser,
                ai_chatbot=ai_chatbot,
                enable_ai_enhancement=enable_ai_enhancement,
                command_definitions=command_definitions,
            )

        logger.warning(f"Unknown action plan intent: {plan.response_intent}")
        response_text = ai_chatbot.generate_response(
            plan.source_message,
            user_id=user_id,
            mode="chat",
        )
        return ActionExecutionResult(
            plan=plan,
            response=InteractionResponse(response_text, True),
        )

    @handle_errors("executing planned actions", default_return=None)
    def _execute_planned_actions(
        self,
        plan: AIActionPlan,
        user_id: str,
        channel_type: str,
        *,
        command_parser,
        ai_chatbot,
        enable_ai_enhancement: bool,
        command_definitions,
    ) -> ActionExecutionResult | None:
        """Dispatch the first planned action and optionally summarize the result."""
        if not plan.actions:
            return ActionExecutionResult(
                plan=plan,
                response=InteractionResponse(
                    "I understood you want an action, but I couldn't identify which one. "
                    "Could you try rephrasing?",
                    True,
                ),
            )

        action = plan.actions[0]
        adapter = _load_action_request_helpers()
        if adapter is None:
            return ActionExecutionResult(
                plan=plan,
                response=InteractionResponse(
                    "I had trouble preparing that action. Please try again.",
                    True,
                ),
            )
        parsing_result = adapter.build_parsing_result_from_action_request(action)
        if parsing_result is None:
            return ActionExecutionResult(
                plan=plan,
                response=InteractionResponse(
                    "I had trouble preparing that action. Please try again.",
                    True,
                ),
            )

        handler_response = dispatch_structured_command(
            user_id,
            parsing_result,
            channel_type,
            command_parser=command_parser,
            ai_chatbot=ai_chatbot,
            enable_ai_enhancement=False,
            command_definitions=command_definitions,
        )
        metadata = adapter.build_action_execution_metadata(action, handler_response)

        if handler_response.message and handler_response.message.strip():
            if enable_ai_enhancement and ai_chatbot.is_ai_available() and metadata is not None:
                enhanced = self._generate_result_aware_response(
                    user_id,
                    action,
                    handler_response,
                    metadata,
                    ai_chatbot=ai_chatbot,
                )
                if enhanced is not None:
                    handler_response = enhanced
        elif metadata is not None and metadata.error:
            handler_response = InteractionResponse(metadata.error, handler_response.completed)

        return ActionExecutionResult(
            plan=plan,
            response=handler_response,
            metadata=metadata,
        )

    @handle_errors("generating result-aware response", default_return=None)
    def _generate_result_aware_response(
        self,
        user_id: str,
        action: AIActionRequest,
        handler_response: InteractionResponse,
        metadata: Any,
        *,
        ai_chatbot,
    ) -> InteractionResponse:
        """Rewrite handler output using the action_result_response prompt flow."""
        result_metadata = metadata.to_dict()
        messages = assemble_action_result_messages(
            user_id,
            action.source_message,
            result_metadata,
        )
        if not messages or len(messages) < 2:
            return handler_response

        system_content = messages[0].get("content", "")
        user_content = messages[1].get("content", action.source_message)
        context_prompt = (
            f"{system_content}\n\n"
            f"User: {user_content}\n\n"
            "Write one warm, concise user-visible reply that reflects the handler result. "
            "Return ONLY the reply text."
        )
        enhanced_text = ai_chatbot.generate_response(
            context_prompt,
            user_id=user_id,
            timeout=3,
        )
        if enhanced_text and len(enhanced_text.strip()) > 10:
            handler_response.message = enhanced_text.strip()
        return handler_response


_action_plan_executor: ActionPlanExecutor | None = None


@handle_errors("getting action plan executor")
def get_action_plan_executor() -> ActionPlanExecutor:
    """Return the shared action plan executor."""
    global _action_plan_executor
    if _action_plan_executor is None:
        _action_plan_executor = ActionPlanExecutor()
    return _action_plan_executor


@handle_errors("handling message with action planner", default_return=None)
def handle_message_with_action_planner(
    user_id: str,
    message: str,
    channel_type: str,
    *,
    command_parser,
    ai_chatbot,
    enable_ai_enhancement: bool,
    command_definitions,
) -> InteractionResponse | None:
    """Plan and execute one product-AI interaction."""
    planner = get_action_planner()
    executor = get_action_plan_executor()
    plan = planner.plan_from_message(message, user_id=user_id, ai_chatbot=ai_chatbot)
    if plan is None:
        return None
    result = executor.execute_plan(
        plan,
        user_id,
        channel_type,
        command_parser=command_parser,
        ai_chatbot=ai_chatbot,
        enable_ai_enhancement=enable_ai_enhancement,
        command_definitions=command_definitions,
    )
    return result.response if result else None
