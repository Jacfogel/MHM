# ai/chat/response_generator.py

"""Conversational response generation: context prompt assembly for chat."""

from ai.context.assembly import assemble_comprehensive_messages
from ai.prompts.manager import MINIMAL_CHAT_SYSTEM_PROMPT, get_prompt_manager
from core.error_handling import handle_errors
from core.logger import get_component_logger

logger = get_component_logger("ai")


class ResponseGenerator:
    """Build conversational prompts for LM Studio chat calls."""

    # devtools: intentional[duplicate-functions]: thin_prompt_component_constructors
    @handle_errors("initializing response generator", default_return=None)
    def __init__(self) -> None:
        self._prompt_manager = get_prompt_manager()

    @handle_errors(
        "creating comprehensive context prompt",
        default_return=[
            {
                "role": "system",
                "content": MINIMAL_CHAT_SYSTEM_PROMPT,
            },
            {"role": "user", "content": "Hello"},
        ],
    )
    def create_comprehensive_context_prompt(
        self, user_id: str, user_prompt: str
    ) -> list:
        """Create a comprehensive context prompt with all user data for LM Studio."""
        return assemble_comprehensive_messages(user_id, user_prompt)


_response_generator: ResponseGenerator | None = None


@handle_errors("getting response generator")
def get_response_generator() -> ResponseGenerator:
    """Return the shared response generator."""
    global _response_generator
    if _response_generator is None:
        _response_generator = ResponseGenerator()
    return _response_generator
