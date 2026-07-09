# communication/message_processing/interaction_manager.py

"""
Interaction Manager - Main integration layer for user interactions.

Thin orchestrator composing command registry, prefix routing, flow dispatch,
parsing shortcuts, structured command dispatch, and response helpers.
"""

from typing import Any

from ai.chat.chatbot import get_ai_chatbot
from core.error_handling import handle_errors
from core.logger import get_component_logger
from communication.command_handlers.interaction_handlers import get_all_handlers
from communication.command_handlers.shared_types import InteractionResponse
from communication.message_processing.command_parser import get_enhanced_command_parser
from communication.message_processing.command_registry import (
    CommandDefinition,
    build_command_definitions,
    build_slash_command_map,
    command_definitions_as_dicts,
)
from communication.message_processing.conversation_flow_manager import conversation_manager
from communication.message_processing.flow_message_dispatcher import dispatch_flow_message
from communication.message_processing.help_responses import get_help_response
from communication.message_processing.intent_validation import is_valid_intent
from communication.message_processing.parsing_shortcuts import (
    coerce_unknown_update_task,
    reinforce_update_task_parsing,
    try_parsing_shortcuts,
)
from communication.message_processing.prefix_command_processor import process_prefix_command
from communication.message_processing.structured_command_dispatcher import (
    dispatch_structured_command,
)
from communication.message_processing.user_suggestions import (
    augment_suggestions,
    get_user_suggestions,
)

logger = get_component_logger("communication_manager")
interaction_logger = logger

# Public API facade re-exports
__all__ = [
    "CommandDefinition",
    "InteractionManager",
    "get_interaction_manager",
    "handle_user_message",
]


class InteractionManager:
    """Main manager for handling user interactions across all channels."""

    @handle_errors("initializing interaction manager")
    def __init__(self):
        try:
            self.command_parser = get_enhanced_command_parser()
            self.ai_chatbot = get_ai_chatbot()
            self.interaction_handlers = get_all_handlers()
            self.min_command_confidence = 0.3
            self.partial_command_confidence = 0.15
            self.enable_ai_enhancement = True
            self.fallback_to_chat = True
            self._command_definitions = build_command_definitions()
        except Exception as e:
            logger.error(f"Error initializing interaction manager: {e}")
            raise

    @handle_errors(
        "handling user interaction",
        default_return=InteractionResponse(
            "I'm having trouble processing your request right now. Please try again in a moment.",
            True,
        ),
    )
    def handle_message(
        self, user_id: str, message: str, channel_type: str = "discord"
    ) -> InteractionResponse:
        """Main entry point for handling user messages."""
        if not message or not message.strip():
            return InteractionResponse(
                "I didn't receive a message. How can I help you today?", True
            )

        rule_based_override = None
        message_stripped = message.strip()
        logger.info(
            f"COMMAND_DETECTION: Processing message '{message_stripped[:50]}...' "
            f"for user {user_id}"
        )

        user_state = conversation_manager.user_states.get(
            user_id, {"flow": 0, "state": 0, "data": {}}
        )
        logger.info(
            f"FLOW_CHECK: User {user_id} flow state: {user_state.get('flow', 'None')} "
            f"(type: {type(user_state.get('flow'))})"
        )

        prefix_result = process_prefix_command(
            user_id, message_stripped, user_state, self._command_definitions
        )
        if prefix_result.response is not None:
            return prefix_result.response
        message = prefix_result.message if prefix_result.message is not None else message

        flow_result = dispatch_flow_message(user_id, message, self.command_parser)
        if flow_result.response is not None:
            return flow_result.response
        if flow_result.rule_based_override is not None:
            rule_based_override = flow_result.rule_based_override

        logger.info(
            f"User {user_id} not in active flow or command detected, "
            "proceeding with command parsing"
        )

        shortcut_response = try_parsing_shortcuts(
            user_id,
            message,
            channel_type,
            self._handle_structured_command,
            augment_suggestions,
        )
        if shortcut_response is not None:
            return shortcut_response

        if rule_based_override is not None:
            parsing_result = rule_based_override
        else:
            parsing_result = self.command_parser.parse(message, user_id)

        parsing_result = coerce_unknown_update_task(parsing_result, message)
        logger.info(
            f"INTERACTION_MANAGER: Parsed message for user {user_id}: "
            f"{parsing_result.method} method, "
            f"intent: {parsing_result.parsed_command.intent}, "
            f"confidence: {parsing_result.confidence}"
        )

        if parsing_result.confidence >= self.min_command_confidence:
            parsing_result = reinforce_update_task_parsing(parsing_result, message)
            logger.info(
                f"INTERACTION_MANAGER: Handling as structured command: "
                f"{parsing_result.parsed_command.intent}"
            )
            resp = self._handle_structured_command(user_id, parsing_result, channel_type)
            return augment_suggestions(parsing_result.parsed_command, resp)

        if self.fallback_to_chat:
            logger.info(
                f"INTERACTION_MANAGER: Handling as contextual chat: confidence "
                f"{parsing_result.confidence} < {self.min_command_confidence}"
            )
            from core.config import AI_ACTION_PLANNER_ENABLED

            if AI_ACTION_PLANNER_ENABLED:
                from communication.message_processing.action_plan_executor import (
                    handle_message_with_action_planner,
                )

                planned_response = handle_message_with_action_planner(
                    user_id,
                    message,
                    channel_type,
                    command_parser=self.command_parser,
                    ai_chatbot=self.ai_chatbot,
                    enable_ai_enhancement=self.enable_ai_enhancement,
                    command_definitions=self._command_definitions,
                )
                if planned_response is not None:
                    return planned_response
                partial_response = self._try_partial_structured_command(
                    user_id, parsing_result, channel_type
                )
                if partial_response is not None:
                    return partial_response
            return self._handle_contextual_chat(user_id, message, channel_type)

        logger.debug("No fallback to chat, returning help")
        return get_help_response(
            user_id,
            message,
            command_parser=self.command_parser,
            command_definitions=self._command_definitions,
        )

    @property
    @handle_errors("getting slash command map property", default_return={})
    def slash_command_map(self) -> dict[str, str]:
        """Backward-compatible property exposing the canonical slash command map."""
        return self.get_slash_command_map()

    @handle_errors("getting slash command map")
    def get_slash_command_map(self) -> dict[str, str]:
        return build_slash_command_map(self._command_definitions)

    @handle_errors("getting command definitions")
    def get_command_definitions(self) -> list[dict[str, str]]:
        return command_definitions_as_dicts(self._command_definitions)

    @handle_errors(
        "handling structured command",
        default_return=InteractionResponse(
            "I encountered an error while processing your request. Please try again or ask for help.",
            True,
        ),
    )
    def _handle_structured_command(self, user_id, parsing_result, channel_type):
        """Delegate structured command handling to the shared dispatcher."""
        return dispatch_structured_command(
            user_id,
            parsing_result,
            channel_type,
            command_parser=self.command_parser,
            ai_chatbot=self.ai_chatbot,
            enable_ai_enhancement=self.enable_ai_enhancement,
            command_definitions=self._command_definitions,
        )

    @handle_errors(
        "handling contextual chat",
        default_return=InteractionResponse(
            "I'm having trouble processing your message right now. Please try again.",
            True,
        ),
    )
    def _handle_contextual_chat(
        self, user_id: str, message: str, channel_type: str
    ) -> InteractionResponse:
        response = self.ai_chatbot.generate_response(
            message, user_id=user_id, mode="chat"
        )
        return InteractionResponse(response, True)

    @handle_errors("getting available commands", default_return={})
    def get_available_commands(self, user_id: str) -> dict[str, Any]:
        commands = {}
        for handler_name, handler in self.interaction_handlers.items():
            commands[handler_name] = {
                "help": handler.get_help(),
                "examples": handler.get_examples(),
                "intents": [
                    intent
                    for intent in [
                        "create_task",
                        "list_tasks",
                        "complete_task",
                        "delete_task",
                        "update_task",
                        "task_stats",
                        "start_checkin",
                        "checkin_status",
                        "show_profile",
                        "update_profile",
                        "profile_stats",
                        "help",
                        "commands",
                        "examples",
                    ]
                    if handler.can_handle(intent)
                ],
            }
        return commands

    @handle_errors("getting user suggestions", default_return=[])
    def get_user_suggestions(self, user_id: str, context: str = "") -> list:
        return get_user_suggestions(user_id, context)

    # not_duplicate: intent_validation_delegates
    @handle_errors("checking if intent is valid", default_return=False)
    def _is_valid_intent(self, intent: str) -> bool:
        return is_valid_intent(intent, self.interaction_handlers)

    @handle_errors("retrying partial structured command after planner failure", default_return=None)
    def _try_partial_structured_command(
        self,
        user_id: str,
        parsing_result,
        channel_type: str,
    ) -> InteractionResponse | None:
        """Run rule-based command dispatch when planner failed but parse had usable intent."""
        intent = parsing_result.parsed_command.intent
        confidence = parsing_result.confidence
        if not intent or intent == "unknown":
            return None
        if confidence >= self.min_command_confidence:
            return None
        if confidence < self.partial_command_confidence:
            return None
        if not self._is_valid_intent(intent):
            return None

        logger.info(
            "INTERACTION_MANAGER: Planner unavailable; retrying partial structured command "
            f"for intent {intent} at confidence {confidence:.2f}"
        )
        response = self._handle_structured_command(user_id, parsing_result, channel_type)
        return augment_suggestions(parsing_result.parsed_command, response)

    @handle_errors("augmenting suggestions")
    def _augment_suggestions(self, parsed_command, response):
        """Add context-aware follow-up suggestions to an interaction response."""
        return augment_suggestions(parsed_command, response)

    @handle_errors(
        "getting help response",
        default_return=InteractionResponse(
            "I'm here to help! Try asking about tasks, check-ins, or your profile.",
            True,
        ),
    )
    def _get_help_response(self, user_id: str, message: str) -> InteractionResponse:
        """Return contextual help text and parser suggestions."""
        return get_help_response(
            user_id,
            message,
            command_parser=self.command_parser,
            command_definitions=self._command_definitions,
        )

    @handle_errors(
        "getting commands response",
        default_return=InteractionResponse("Error getting commands", False),
    )
    def _get_commands_response(self) -> InteractionResponse:
        """Return the channel-agnostic slash-command discovery list."""
        from communication.message_processing.help_responses import get_commands_response

        return get_commands_response(self._command_definitions)


_interaction_manager_instance = None


@handle_errors("getting interaction manager")
def get_interaction_manager() -> InteractionManager:
    global _interaction_manager_instance
    if _interaction_manager_instance is None:
        _interaction_manager_instance = InteractionManager()
    return _interaction_manager_instance


@handle_errors(
    operation="handling user message",
    default_return=InteractionResponse(
        message="I'm having trouble processing your request right now. Please try again in a moment.",
        completed=True,
    ),
)
def handle_user_message(
    user_id: str, message: str, channel_type: str = "discord"
) -> InteractionResponse:
    return get_interaction_manager().handle_message(user_id, message, channel_type)
