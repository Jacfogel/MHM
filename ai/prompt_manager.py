# prompt_manager.py

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from core.logger import get_component_logger
from core.error_handling import handle_errors
from core.config import AI_SYSTEM_PROMPT_PATH, AI_USE_CUSTOM_PROMPT

# Route prompt manager logs to AI component
prompt_logger = get_component_logger("ai_prompt")
logger = prompt_logger

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "resources" / "prompts"
_ASSISTANT_PROMPT_FILENAME = "assistant_system_prompt.txt"
_COMMAND_PROMPT_FILENAME = "command.txt"

# Short templates for legacy prompt_manager helpers (create_task_prompt / create_checkin_prompt).
_INLINE_PROMPT_BODIES: dict[str, str] = {
    "checkin": (
        "You are a supportive check-in assistant. Help users reflect on their day "
        "and track their wellness. Be encouraging and non-judgmental. "
        "Keep responses concise and supportive."
    ),
    "task_assistant": (
        "You are a helpful task management assistant. Help users organize, "
        "prioritize, and complete their tasks. Be practical and encouraging. "
        "Keep responses focused and actionable."
    ),
}

_MINIMAL_WELLNESS_FALLBACK = (
    "You are a supportive wellness assistant. Keep responses helpful, "
    "encouraging, and conversational."
)


@handle_errors("loading prompt text file", default_return="")
def _read_prompt_file(path: Path) -> str:
    """Read UTF-8 prompt text from a file path."""
    if not path.is_file():
        logger.warning(f"Prompt file not found: {path}")
        return ""
    return path.read_text(encoding="utf-8").strip()


@handle_errors("loading command prompt file", default_return="")
def _load_command_prompt_text() -> str:
    """Load the command-parser system prompt from resources/prompts/command.txt."""
    return _read_prompt_file(_PROMPTS_DIR / _COMMAND_PROMPT_FILENAME)


@handle_errors("loading assistant system prompt file", default_return="")
def _load_assistant_system_prompt_text() -> str:
    """Load the main companion prompt from resources/prompts/assistant_system_prompt.txt."""
    path = Path(AI_SYSTEM_PROMPT_PATH)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent.parent / AI_SYSTEM_PROMPT_PATH
    if not path.is_file():
        logger.warning(f"Assistant system prompt file not found: {path}")
        return ""
    with open(path, encoding="utf-8") as f:
        return f.read().strip()


@dataclass
class PromptTemplate:
    """Template for AI prompts"""

    name: str
    content: str
    description: str
    max_tokens: int | None = None
    temperature: float = 0.7


class PromptManager:
    """Manages AI prompts and templates"""

    @handle_errors("initializing prompt manager", default_return=None)
    def __init__(self):
        """Initialize the prompt manager"""
        self._custom_prompt = None
        self._prompt_templates: dict[str, PromptTemplate] = {}
        self._assistant_prompt = _load_assistant_system_prompt_text()
        wellness_body = self._assistant_prompt or _MINIMAL_WELLNESS_FALLBACK
        command_body = _load_command_prompt_text()
        if not command_body:
            logger.error(
                f"Command prompt is empty; check resources/prompts/{_COMMAND_PROMPT_FILENAME}"
            )

        self._fallback_prompts = {
            "wellness": PromptTemplate(
                name="wellness",
                content=wellness_body,
                description="Companion wellness prompt (resources/prompts/assistant_system_prompt.txt)",
                max_tokens=250,
                temperature=0.7,
            ),
            "neurodivergent_support": PromptTemplate(
                name="neurodivergent_support",
                content=wellness_body,
                description="Same companion prompt as wellness",
                max_tokens=200,
                temperature=0.7,
            ),
            "command": PromptTemplate(
                name="command",
                content=command_body,
                description="Command parsing prompt (resources/prompts/command.txt)",
                max_tokens=120,
                temperature=0.1,
            ),
            "checkin": PromptTemplate(
                name="checkin",
                content=_INLINE_PROMPT_BODIES["checkin"],
                description="Check-in assistant prompt (inline)",
                max_tokens=150,
                temperature=0.6,
            ),
            "task_assistant": PromptTemplate(
                name="task_assistant",
                content=_INLINE_PROMPT_BODIES["task_assistant"],
                description="Task management prompt (inline)",
                max_tokens=150,
                temperature=0.5,
            ),
        }

        self._load_custom_prompt()

    @handle_errors("loading custom prompt", default_return=None)
    def _load_custom_prompt(self):
        """Load the custom system prompt from file when AI_USE_CUSTOM_PROMPT is enabled."""
        if not AI_USE_CUSTOM_PROMPT:
            logger.info("Custom system prompt disabled via configuration")
            self._custom_prompt = None
            return

        try:
            if os.path.exists(AI_SYSTEM_PROMPT_PATH):
                with open(AI_SYSTEM_PROMPT_PATH, encoding="utf-8") as f:
                    self._custom_prompt = f.read().strip()
                _is_tool = "development_tools" in " ".join(
                    getattr(sys, "argv", [])
                ) or "run_dev_tools" in " ".join(getattr(sys, "argv", []))
                (logger.debug if _is_tool else logger.info)(
                    f"Loaded custom system prompt from {AI_SYSTEM_PROMPT_PATH}"
                )
            else:
                self._custom_prompt = None
                logger.warning(
                    f"Custom system prompt file not found: {AI_SYSTEM_PROMPT_PATH}"
                )
        except Exception as e:
            self._custom_prompt = None
            logger.error(f"Error loading custom system prompt: {e}")

    @handle_errors(
        "getting prompt",
        default_return="You are a supportive wellness assistant. Keep responses helpful, encouraging, and conversational.",
    )
    def get_prompt(self, prompt_type: str = "wellness") -> str:
        """
        Get the appropriate prompt for the given type

        Args:
            prompt_type: Type of prompt ('wellness', 'command', 'neurodivergent_support', etc.)

        Returns:
            The prompt string
        """
        logger.debug(f"Getting prompt for type: {prompt_type}")

        if self._custom_prompt and prompt_type in [
            "wellness",
            "neurodivergent_support",
        ]:
            logger.debug(f"Using custom prompt for type: {prompt_type}")
            return self._custom_prompt

        template = self._fallback_prompts.get(prompt_type)
        if template:
            logger.debug(f"Using fallback prompt for type: {prompt_type}")
            content = template.content
            if prompt_type == "command":
                from ai.command_registry import inject_command_actions_into_prompt

                content = inject_command_actions_into_prompt(content)
            return content

        logger.debug(
            f"Prompt type '{prompt_type}' not found, using default wellness prompt"
        )
        return self._fallback_prompts["wellness"].content

    # not_duplicate: prompt_template_lookup_mutation
    @handle_errors("getting prompt template", default_return=None)
    def get_prompt_template(self, prompt_type: str) -> PromptTemplate | None:
        """
        Get the full prompt template for the given type

        Args:
            prompt_type: Type of prompt

        Returns:
            PromptTemplate object or None if not found
        """
        if prompt_type in self._prompt_templates:
            return self._prompt_templates[prompt_type]

        return self._fallback_prompts.get(prompt_type)

    @handle_errors("adding prompt template", default_return=False)
    def add_prompt_template(self, template: PromptTemplate):
        """
        Add a custom prompt template

        Args:
            template: PromptTemplate to add
        """
        self._prompt_templates[template.name] = template
        logger.info(
            f"Added custom prompt template: {template.name} (content_length={len(template.content)}, max_tokens={template.max_tokens})"
        )

    # not_duplicate: prompt_template_lookup_mutation
    @handle_errors("removing prompt template", default_return=False)
    def remove_prompt_template(self, prompt_type: str) -> bool:
        """
        Remove a custom prompt template

        Args:
            prompt_type: Name of the template to remove

        Returns:
            True if template was removed, False if not found
        """
        if prompt_type in self._prompt_templates:
            del self._prompt_templates[prompt_type]
            logger.info(f"Removed custom prompt template: {prompt_type}")
            return True
        return False

    @handle_errors("reloading custom prompt", default_return=False)
    def reload_custom_prompt(self):
        """Reload the custom prompt from file (useful for development)"""
        self._assistant_prompt = _load_assistant_system_prompt_text()
        wellness_body = self._assistant_prompt or _MINIMAL_WELLNESS_FALLBACK
        self._fallback_prompts["wellness"].content = wellness_body
        self._fallback_prompts["neurodivergent_support"].content = wellness_body
        self._load_custom_prompt()
        logger.info("Custom system prompt reloaded")

    # not_duplicate: custom_prompt_metadata
    @handle_errors("checking if custom prompt exists", default_return=False)
    def has_custom_prompt(self) -> bool:
        """Check if a custom prompt is loaded."""
        return self._custom_prompt is not None

    # not_duplicate: custom_prompt_metadata
    @handle_errors("getting custom prompt length", default_return=0)
    def custom_prompt_length(self) -> int:
        """Get the length of the custom prompt."""
        return len(self._custom_prompt or "")

    @handle_errors("getting fallback prompt keys", default_return=[])
    def fallback_prompt_keys(self) -> list[str]:
        """Get the keys of available fallback prompts."""
        return (
            list(self._fallback_prompts.keys())
            if isinstance(self._fallback_prompts, dict)
            else []
        )

    @handle_errors("getting available prompts", default_return={})
    def get_available_prompts(self) -> dict[str, str]:
        """
        Get all available prompt types and their descriptions

        Returns:
            Dictionary mapping prompt types to descriptions
        """
        prompts = {}

        for name, template in self._prompt_templates.items():
            prompts[name] = template.description

        for name, template in self._fallback_prompts.items():
            prompts[name] = template.description

        return prompts

    @handle_errors("creating contextual prompt", default_return="")
    def create_contextual_prompt(
        self, base_prompt: str, context: str, user_input: str
    ) -> str:
        """
        Create a contextual prompt by combining base prompt, context, and user input

        Args:
            base_prompt: Base system prompt
            context: Contextual information
            user_input: User's input

        Returns:
            Combined contextual prompt
        """
        contextual_prompt = (
            f"{base_prompt}\n\nContext: {context}\n\nUser: {user_input}\n\nAssistant:"
        )
        logger.debug(
            f"Created contextual prompt: base_length={len(base_prompt)}, context_length={len(context)}, input_length={len(user_input)}, total_length={len(contextual_prompt)}"
        )
        return contextual_prompt

    # not_duplicate: domain_prompt_builders
    @handle_errors("creating task prompt", default_return="")
    def create_task_prompt(self, task_description: str, user_context: str = "") -> str:
        """
        Create a task-specific prompt

        Args:
            task_description: Description of the task
            user_context: User context information

        Returns:
            Task-specific prompt
        """
        logger.debug(f"Creating task prompt for: {task_description[:50]}...")
        base_prompt = self.get_prompt("task_assistant")
        context = f"Task: {task_description}"
        if user_context:
            context += f"\nUser Context: {user_context}"
            logger.debug(
                f"Added user context to task prompt: {len(user_context)} characters"
            )

        return self.create_contextual_prompt(
            base_prompt, context, "Help me with this task"
        )

    # not_duplicate: domain_prompt_builders
    @handle_errors("creating checkin prompt", default_return="")
    def create_checkin_prompt(
        self, checkin_type: str = "daily", user_context: str = ""
    ) -> str:
        """
        Create a check-in specific prompt

        Args:
            checkin_type: Type of check-in (daily, weekly, etc.)
            user_context: User context information

        Returns:
            Check-in specific prompt
        """
        logger.debug(f"Creating checkin prompt for type: {checkin_type}")
        base_prompt = self.get_prompt("checkin")
        context = f"Check-in Type: {checkin_type}"
        if user_context:
            context += f"\nUser Context: {user_context}"
            logger.debug(
                f"Added user context to checkin prompt: {len(user_context)} characters"
            )

        return self.create_contextual_prompt(
            base_prompt, context, "Let's do a check-in"
        )


# Global prompt manager instance
_prompt_manager = None


@handle_errors("getting prompt manager instance", default_return=None)
def get_prompt_manager() -> PromptManager:
    """Get the global prompt manager instance"""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager
