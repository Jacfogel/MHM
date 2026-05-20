# ai/response_generator.py

"""Conversational response generation: context prompts and engagement helpers."""

from ai.conversational_context import assemble_comprehensive_messages
from ai.prompt_manager import get_prompt_manager
from core.config import AI_MIN_RESPONSE_LENGTH
from core.error_handling import handle_errors
from core.logger import get_component_logger

logger = get_component_logger("ai")


class ResponseGenerator:
    """Build conversational prompts and post-process chat responses."""

    @handle_errors("initializing response generator", default_return=None)
    def __init__(self) -> None:
        self._prompt_manager = get_prompt_manager()

    @handle_errors(
        "creating comprehensive context prompt",
        default_return=[
            {
                "role": "system",
                "content": "You are a supportive wellness assistant. Keep responses helpful, encouraging, and conversational.",
            },
            {"role": "user", "content": "Hello"},
        ],
    )
    def create_comprehensive_context_prompt(
        self, user_id: str, user_prompt: str
    ) -> list:
        """Create a comprehensive context prompt with all user data for LM Studio."""
        base_prompt = self._prompt_manager.get_prompt("wellness")
        return assemble_comprehensive_messages(user_id, user_prompt, base_prompt)

    @handle_errors("enhancing conversational engagement", default_return="")
    def enhance_conversational_engagement(self, response: str) -> str:
        """
        Enhance response to ensure good conversational engagement.
        Adds engagement prompts if the response doesn't already have them.
        """
        if not response or len(response.strip()) < AI_MIN_RESPONSE_LENGTH:
            return response

        # Check if response already ends with engagement indicators
        response_lower = response.lower().strip()
        engagement_indicators = [
            "?",
            "how are you",
            "what do you think",
            "would you like",
            "tell me more",
            "i'm here",
            "feel free",
            "let me know",
            "what's on your mind",
            "how can i help",
            "anything else",
        ]

        # If response already has engagement, return as-is
        for indicator in engagement_indicators:
            if response_lower.endswith(indicator) or indicator in response_lower[-50:]:
                return response

        # Add gentle engagement prompt if response seems complete but lacks engagement
        if response.endswith((".", "!", "...")):
            engagement_options = [
                " How are you feeling about that?",
                " I'm here if you want to talk more about this.",
                " What would help you feel better right now?",
                " Would you like to tell me more about what's on your mind?",
                " How can I support you with this?",
                " What else is on your mind today?",
            ]

            # Choose engagement based on response content
            if any(
                word in response_lower
                for word in ["difficult", "hard", "struggle", "tough", "challenge"]
            ):
                return response + engagement_options[0]
            if any(
                word in response_lower
                for word in ["good", "great", "better", "improve", "progress"]
            ):
                return response + engagement_options[3]
            if any(
                word in response_lower for word in ["help", "support", "need", "want"]
            ):
                return response + engagement_options[4]
            return response + engagement_options[5]

        return response


_response_generator: ResponseGenerator | None = None


@handle_errors("getting response generator")
def get_response_generator() -> ResponseGenerator:
    """Return the shared response generator."""
    global _response_generator
    if _response_generator is None:
        _response_generator = ResponseGenerator()
    return _response_generator
