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


@handle_errors("combining handler responses", default_return=InteractionResponse("Done.", True))
def _combine_handler_responses(responses: list[InteractionResponse]) -> InteractionResponse:
    """Merge sequential handler replies into one user-visible response."""
    if not responses:
        return InteractionResponse("Done.", True)
    if len(responses) == 1:
        return responses[0]

    messages = [
        response.message.strip()
        for response in responses
        if response.message and response.message.strip()
    ]
    combined_message = "\n\n".join(messages) if messages else "Done."
    completed = all(response.completed for response in responses)
    last = responses[-1]
    return InteractionResponse(
        combined_message,
        completed,
        rich_data=last.rich_data,
        suggestions=last.suggestions,
        error=last.error,
    )


@handle_errors("normalizing execution metadata", default_return=None)
def _normalize_execution_metadata(
    metadata_list: list[Any],
    *,
    total_planned: int,
) -> Any | None:
    """Return single metadata for one-action plans, or a list for multi-action plans."""
    if not metadata_list:
        return None
    if total_planned > 1 or len(metadata_list) > 1:
        return metadata_list
    return metadata_list[0]


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
        command_definitions,
    ) -> ActionExecutionResult | None:
        """Dispatch planned actions in order and combine completed handler results.

        Result-aware rewriting runs for every completed action when AI is available,
        independent of the rule-parser ``enable_ai_enhancement`` flag.
        """
        if not plan.actions:
            return ActionExecutionResult(
                plan=plan,
                response=InteractionResponse(
                    "I understood you want an action, but I couldn't identify which one. "
                    "Could you try rephrasing?",
                    True,
                ),
            )

        adapter = _load_action_request_helpers()
        if adapter is None:
            return ActionExecutionResult(
                plan=plan,
                response=InteractionResponse(
                    "I had trouble preparing that action. Please try again.",
                    True,
                ),
            )

        completed_steps: list[tuple[AIActionRequest, InteractionResponse, Any]] = []
        metadata_list: list[Any] = []

        for index, action in enumerate(plan.actions):
            parsing_result = adapter.build_parsing_result_from_action_request(action)
            if parsing_result is None:
                return ActionExecutionResult(
                    plan=plan,
                    response=InteractionResponse(
                        "I had trouble preparing that action. Please try again.",
                        True,
                    ),
                    metadata=_normalize_execution_metadata(
                        metadata_list, total_planned=len(plan.actions)
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
            if metadata is not None:
                metadata_list.append(metadata)

            if metadata is not None and metadata.error:
                handler_response = InteractionResponse(
                    metadata.error,
                    handler_response.completed,
                )
                return ActionExecutionResult(
                    plan=plan,
                    response=handler_response,
                    metadata=_normalize_execution_metadata(
                        metadata_list, total_planned=len(plan.actions)
                    ),
                )

            if not handler_response.completed:
                logger.info(
                    f"Stopping multi-action plan after action {index + 1} "
                    f"({action.action_name}): follow-up required"
                )
                return ActionExecutionResult(
                    plan=plan,
                    response=handler_response,
                    metadata=_normalize_execution_metadata(
                        metadata_list, total_planned=len(plan.actions)
                    ),
                )

            if handler_response.message and handler_response.message.strip():
                completed_steps.append((action, handler_response, metadata))

        enhanced_responses = self._apply_result_aware_responses(
            user_id,
            completed_steps,
            ai_chatbot=ai_chatbot,
        )
        handler_response = _combine_handler_responses(enhanced_responses)
        metadata = _normalize_execution_metadata(
            metadata_list, total_planned=len(plan.actions)
        )

        return ActionExecutionResult(
            plan=plan,
            response=handler_response,
            metadata=metadata,
        )

    @handle_errors("applying result-aware responses", default_return=[])
    def _apply_result_aware_responses(
        self,
        user_id: str,
        completed_steps: list[tuple[AIActionRequest, InteractionResponse, Any]],
        *,
        ai_chatbot,
    ) -> list[InteractionResponse]:
        """Rewrite each completed handler output using the action_result_response flow."""
        if not completed_steps or not ai_chatbot.is_ai_available():
            return [response for _, response, _ in completed_steps]

        enhanced_responses: list[InteractionResponse] = []
        for action, handler_response, step_metadata in completed_steps:
            if step_metadata is None:
                enhanced_responses.append(handler_response)
                continue
            enhanced = self._generate_result_aware_response(
                user_id,
                action,
                handler_response,
                step_metadata,
                ai_chatbot=ai_chatbot,
            )
            enhanced_responses.append(enhanced or handler_response)
        return enhanced_responses

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
