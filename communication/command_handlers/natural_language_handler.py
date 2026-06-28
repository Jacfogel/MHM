# communication/command_handlers/natural_language_handler.py

"""Handler for per-user natural-language phrase settings."""

from typing import Any

from core.logger import get_component_logger
from core.error_handling import handle_errors
from core.natural_language_defaults import (
    apply_natural_language_defaults_update,
    format_natural_language_defaults_message,
    get_natural_language_defaults,
)

from communication.command_handlers.base_handler import InteractionHandler
from communication.command_handlers.shared_types import InteractionResponse, ParsedCommand

logger = get_component_logger("communication_manager")

PHRASE_HELP_TEXT = """**Natural-Language Phrase Settings**
Tune how the assistant interprets time phrases in messages and commands.

**View:** `show phrase settings` / `show language settings`
**Update:**
• `set tonight to 8pm`
• `set after work to 6pm`
• `set morning to 8:30am`
• `set weekend this week to coming` or `off`

These apply to task due dates and other phrase parsing that uses your schedule."""


class NaturalLanguageHandler(InteractionHandler):
    """Handler for natural-language phrase preference commands."""

    @handle_errors("checking if natural language handler can handle intent")
    def can_handle(self, intent: str) -> bool:
        return intent in (
            "show_natural_language_defaults",
            "update_natural_language_defaults",
        )

    @handle_errors(
        "handling natural language interaction",
        default_return=InteractionResponse(
            "I'm having trouble with phrase settings right now. Please try again.", True
        ),
    )
    def handle(
        self, user_id: str, parsed_command: ParsedCommand
    ) -> InteractionResponse:
        intent = parsed_command.intent
        entities = parsed_command.entities

        if intent == "show_natural_language_defaults":
            return self._handle_show(user_id)
        if intent == "update_natural_language_defaults":
            return self._handle_update(user_id, entities)

        return InteractionResponse(
            f"I don't understand that phrase-settings command. Try: {', '.join(self.get_examples())}",
            True,
        )

    @handle_errors(
        "showing phrase settings",
        default_return=InteractionResponse(
            "I'm having trouble loading phrase settings. Please try again.", True
        ),
    )
    def _handle_show(self, user_id: str) -> InteractionResponse:
        defaults = get_natural_language_defaults(user_id)
        return InteractionResponse(
            format_natural_language_defaults_message(defaults),
            completed=True,
            suggestions=[
                "set tonight to 8pm",
                "set after work to 6pm",
                "set morning to 8:30am",
            ],
        )

    @handle_errors(
        "updating phrase settings",
        default_return=InteractionResponse(
            "I'm having trouble updating phrase settings. Please try again.", True
        ),
    )
    def _handle_update(self, user_id: str, entities: dict[str, Any]) -> InteractionResponse:
        nl_field = entities.get("nl_field")
        nl_value = entities.get("nl_value")
        if not nl_field or not nl_value:
            return InteractionResponse(
                "What should I change? Examples:\n"
                "- `set tonight to 8pm`\n"
                "- `set after work to 6pm`\n"
                "- `set morning to 8:30am`\n"
                "- `set weekend this week to coming`",
                completed=False,
                suggestions=[
                    "set tonight to 8pm",
                    "set after work to 6pm",
                    "show phrase settings",
                ],
            )

        result = apply_natural_language_defaults_update(
            user_id, str(nl_field), str(nl_value)
        )
        if not result.success:
            return InteractionResponse(
                result.error_message or "Could not update phrase settings.",
                completed=True,
            )

        updated = ", ".join(result.updated_labels)
        defaults = get_natural_language_defaults(user_id)
        summary = format_natural_language_defaults_message(defaults)
        return InteractionResponse(
            f"Updated **{updated}**.\n\n{summary}",
            completed=True,
            suggestions=["show phrase settings"],
        )

    @handle_errors("getting phrase settings help", default_return=PHRASE_HELP_TEXT)
    def get_help(self) -> str:
        return PHRASE_HELP_TEXT

    @handle_errors("getting phrase settings examples", default_return=[])
    def get_examples(self) -> list[str]:
        return [
            "show phrase settings",
            "set tonight to 8pm",
            "set after work to 6pm",
            "set morning to 8:30am",
            "set weekend this week to off",
        ]
