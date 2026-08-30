# communication/command_handlers/create_menu_handler.py

"""Handler for the unified create menu (tasks + notes)."""

from core.error_handling import handle_errors
from communication.command_handlers.base_handler import InteractionHandler
from communication.command_handlers.shared_types import InteractionResponse, ParsedCommand


class CreateMenuHandler(InteractionHandler):
    """Show the Discord create hub (template and note buttons)."""

    @handle_errors("checking create menu intent", default_return=False)
    def can_handle(self, intent: str) -> bool:
        return intent == "show_create_hub"

    @handle_errors(
        "handling create menu",
        default_return=InteractionResponse(
            "I could not open the create menu. Try again or use text commands.", True
        ),
    )
    def handle(
        self, user_id: str, parsed_command: ParsedCommand
    ) -> InteractionResponse:
        message = (
            "**Create something**\n"
            "First row starts a **task**. Green buttons start a **note**."
        )
        return InteractionResponse(
            message,
            completed=True,
            rich_data={"interaction_view": "create_hub", "user_id": user_id},
        )

    @handle_errors("getting create menu help", default_return="")
    def get_help(self) -> str:
        return (
            "**Create menu** — `create`, `new`, or `add`\n"
            "Opens buttons for task templates (prefilled form), custom task, quick note, and new note (Discord)."
        )

    @handle_errors("getting create menu examples", default_return=[])
    def get_examples(self) -> list[str]:
        return [
            "create menu",
            "task template medication",
            "list task templates",
            "open create hub",
        ]
