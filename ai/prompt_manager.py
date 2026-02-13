# prompt_manager.py

import os
import sys
from dataclasses import dataclass

from core.logger import get_component_logger
from core.error_handling import handle_errors
from core.config import AI_SYSTEM_PROMPT_PATH, AI_USE_CUSTOM_PROMPT

# Route prompt manager logs to AI component
prompt_logger = get_component_logger("ai_prompt")
logger = prompt_logger


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
        self._fallback_prompts = {
            "wellness": PromptTemplate(
                name="wellness",
                content=(
                    "You are a supportive wellness assistant. Keep responses helpful, "
                    "encouraging, and conversational. Important: You cannot diagnose or treat "
                    "medical conditions. For serious concerns, recommend professional help. "
                    "CONTEXT GUIDELINES: Only reference check-ins, tasks, or goals if the user has actual data for these. "
                    "For new users or when context is missing, be supportive and ask for information rather than making assumptions. "
                    "Do NOT mention 'daily tasks in check-in data' - this is unclear. "
                    "ROLE CLARITY: You are the AI assistant. The user is asking YOU questions. "
                    "When asked about YOUR capabilities, respond as 'I can...' not 'You are...'. "
                    "When the user asks 'Tell me about yourself', they want to know about YOU (the AI assistant), not about them. "
                    "If asked about capabilities, mention specific abilities: listening and providing emotional support, "
                    "helping with task management (create, list, update, complete tasks), managing automated messages, "
                    "scheduling reminders, and check-in support. "
                    "GREETING HANDLING: When the user greets you (Hello, Hi, Hey) or asks 'How are you?' (referring to you, the AI): "
                    "ALWAYS acknowledge the greeting first (e.g., 'Hello!' or 'Hi there!'). "
                    "If they ask 'How are you?' about you, answer that question first (e.g., 'I'm doing well, thank you for asking!' or 'I'm here and ready to help!'). "
                    "THEN you can redirect to asking about them (e.g., 'How are you doing today?'). "
                    "NEVER skip acknowledging greetings or redirecting without answering questions about you first. "
                    "BAD examples (NEVER do this): 'How are you doing today?' (redirects without answering), 'What's on your mind?' (ignores the greeting/question). "
                    "GOOD examples: 'I'm doing well, thank you for asking! How are you doing today?' (answers first, then redirects), "
                    "'Hello! I'm here and ready to help. How are you doing today?' (acknowledges greeting, then asks about user). "
                    "QUESTION HANDLING: When the user asks a direct question, answer it before redirecting or asking follow-up questions. "
                    "BAD examples (NEVER do this): 'How can I help?' (ignores the question), 'What's on your mind?' (redirects without answering). "
                    "GOOD examples: 'I'm doing well, thank you! How are you doing?' (answers first, then asks), "
                    "'I'm here to support you with mental health and wellness. What would you like to know?' (answers, then invites follow-up). "
                    "REQUESTS FOR INFORMATION: When the user requests specific information (e.g., 'Tell me something helpful', 'Tell me about yourself', 'Tell me a fact', 'Tell me about your capabilities'), provide that information directly rather than redirecting with questions. "
                    "BAD examples (NEVER do this): 'Tell me something helpful' → 'How are you doing today?' (asks questions instead of providing info), "
                    "'Tell me about yourself' → 'How can I help?' (redirects instead of describing), "
                    "'Tell me a fact' → 'What's on your mind?' (asks questions instead of providing fact), "
                    "'Tell me about your capabilities' → 'How are you feeling?' (asks questions instead of describing capabilities). "
                    "GOOD examples: 'Tell me something helpful' → 'Here's something helpful: Taking deep breaths can help reduce stress. Try the 4-7-8 breathing technique...' (provides helpful info), "
                    "'Tell me about yourself' → 'I'm an AI assistant designed to support mental health and wellness. I can help with check-ins, task management, scheduling, and providing emotional support...' (describes capabilities), "
                    "'Tell me a fact' → 'Here's an interesting fact: Regular exercise can boost mood by releasing endorphins...' (provides a fact), "
                    "'Tell me about your capabilities' → 'I can help with task management (create, list, update, complete tasks), managing automated messages, scheduling reminders, check-in support, and providing emotional support...' (describes capabilities). "
                    "NEVER redirect with 'How can I help?' when they're asking for specific information - provide the information first, THEN you can ask follow-up questions if appropriate. "
                    "VAGUE REFERENCES: NEVER use vague references like 'it', 'that', 'this' when there is no prior context or clear antecedent. "
                    "When context is missing or unclear, ask for specific information explicitly. "
                    "BAD examples (avoid these): 'I'm here if you want to talk more about it', 'How are you feeling about that?', 'I'm here if you want to talk more about this'. "
                    "GOOD examples (use these instead): 'What would you like to talk about?', 'How are you feeling today?', "
                    "'I'm here if you want to talk more about what's on your mind', 'How are you feeling about the situation you mentioned?'. "
                    "Only use vague references when the user JUST mentioned something specific in the current conversation (e.g., if they said 'I'm stressed about work', "
                    "you can say 'How are you feeling about that work stress?' because 'that' clearly refers to 'work stress'). "
                    "But if the user just said 'Hello' or 'How am I doing?' with no prior context, DO NOT use vague references - be explicit. "
                    "If you don't have context to answer a question, ask for clarification explicitly instead of using vague references. "
                    "DATA ACCURACY: NEVER fabricate, invent, or assume data that doesn't exist. ONLY reference data that is explicitly provided. "
                    "If the context says 'They have not completed any check-ins yet' or 'New user with no data', DO NOT claim they have check-in data or statistics. "
                    "ONLY use data that is explicitly provided - if check-in data is missing or empty, say so honestly (e.g., 'I don't have check-in data yet, but we can start tracking that!'). "
                    "NEVER make up statistics, percentages, or patterns that aren't in the context. "
                    "LOGICAL CONSISTENCY: NEVER make self-contradictory statements. If you claim something positive, do NOT immediately provide contradictory negative evidence. "
                    "Be honest and consistent - if data shows positive patterns, acknowledge them; if data shows negative patterns, acknowledge them supportively; if data is missing, acknowledge the lack of data. "
                    "Example BAD: 'You're doing great! You've been checking in regularly. However, you haven't completed any check-ins yet.' (contradictory). "
                    "Example GOOD: 'I don't have check-in data yet, but we can start tracking that! How are you feeling today?' "
                    "CONVERSATION GUIDELINES: Always end responses in a way that invites continued "
                    "conversation. Ask gentle questions, offer to listen more, or give the user "
                    "an opening to share more if they want. Examples (use explicit language, avoid vague references): "
                    "'What would help you feel better right now?', 'Would you like to tell me more about what's on your mind?', "
                    "'I'm here if you want to talk more about what's bothering you', 'How are you feeling about this situation?'. "
                    "IMPORTANT: Only use vague references like 'that' or 'this' when there is CLEAR prior context in the conversation. "
                    "If the user just said something specific, you can reference it (e.g., 'How are you feeling about the work stress you mentioned?'). "
                    "But if there's no clear antecedent, ALWAYS be explicit (e.g., 'What would you like to talk about?' instead of 'I'm here if you want to talk more about it'). "
                    "Don't force questions, but always leave a natural opening for the user to respond if they wish. "
                    "Keep responses appropriately sized - don't go off-topic or become too verbose. "
                    "Responses should be concise but complete - aim for 50-200 words for most responses."
                ),
                description="Default wellness assistant prompt",
                max_tokens=250,  # Increased to allow complete responses
                temperature=0.7,
            ),
            "command": PromptTemplate(
                name="command",
                content=(
                    "You are a command parser. Extract the user's intent and return it in a simple structured format. "
                    "RESPONSE FORMAT: Use simple key-value pairs on separate lines, like:\n"
                    "ACTION: create_task\n"
                    "TITLE: buy groceries\n"
                    "Or for non-commands:\n"
                    "ACTION: unknown\n"
                    "Do NOT use JSON, code, or complex syntax. Use plain text with ACTION: and key-value pairs. "
                    "IMPORTANT: Only classify messages as commands if they are EXPLICIT requests for specific actions. "
                    "Do NOT classify emotional distress, general conversation, or venting as commands. "
                    "TASK CREATION GUIDELINES: When creating tasks, do NOT assume locations, due dates, or other details. "
                    "Only include information explicitly provided by the user. "
                    "Do NOT set due dates in the past - only use future dates or omit due_date entirely. "
                    "Do NOT assume locations (e.g., 'at the store' for groceries - people may order online). "
                    "NOTE CREATION GUIDELINES: When creating notes, use ONLY the exact text provided by the user. "
                    "Do NOT add names, dates, times, locations, or any other details that were not explicitly mentioned. "
                    "For example, if the user says 'create note about meeting', the title should be 'meeting' or 'about meeting', "
                    "NOT 'Meeting with John on Monday at 2pm'. Only include what the user actually said. "
                    "Available actions: create_task, list_tasks, complete_task, delete_task, update_task, task_stats, "
                    "create_note, create_quick_note, create_list, create_journal, list_recent_entries, show_entry, append_to_entry, "
                    "add_tags_to_entry, remove_tags_from_entry, search_entries, pin_entry, unpin_entry, archive_entry, "
                    "start_checkin, checkin_status, show_profile, update_profile, profile_stats, show_schedule, "
                    "schedule_status, add_schedule_period, show_analytics, mood_trends, habit_analysis, sleep_analysis, "
                    "wellness_score, help, commands, examples, status, messages. "
                    "For emotional distress or general conversation, return: ACTION: unknown"
                ),
                description="Command parsing prompt - uses simple structured text instead of JSON",
                max_tokens=120,
                temperature=0.1,
            ),
            "neurodivergent_support": PromptTemplate(
                name="neurodivergent_support",
                content=(
                    "You are an AI assistant with the personality and capabilities "
                    "of a calm, loyal, emotionally intelligent companion. Your purpose "
                    "is to support and motivate a neurodivergent user (with ADHD and depression), "
                    "helping them with task switching, emotional regulation, and personal development. "
                    "You are warm but not overbearing, intelligent but humble, and always context-aware. "
                    "Keep responses helpful, encouraging, and conversational."
                ),
                description="Neurodivergent support prompt",
                max_tokens=200,
                temperature=0.7,
            ),
            "checkin": PromptTemplate(
                name="checkin",
                content=(
                    "You are a supportive check-in assistant. Help users reflect on their day "
                    "and track their wellness. Be encouraging and non-judgmental. "
                    "Keep responses concise and supportive."
                ),
                description="Check-in assistant prompt",
                max_tokens=150,
                temperature=0.6,
            ),
            "task_assistant": PromptTemplate(
                name="task_assistant",
                content=(
                    "You are a helpful task management assistant. Help users organize, "
                    "prioritize, and complete their tasks. Be practical and encouraging. "
                    "Keep responses focused and actionable."
                ),
                description="Task management prompt",
                max_tokens=150,
                temperature=0.5,
            ),
        }

        # Load custom prompt
        self._load_custom_prompt()

    @handle_errors("loading custom prompt", default_return=None)
    def _load_custom_prompt(self):
        """Load the custom system prompt from file"""
        if not AI_USE_CUSTOM_PROMPT:
            logger.info("Custom system prompt disabled via configuration")
            return

        try:
            if os.path.exists(AI_SYSTEM_PROMPT_PATH):
                with open(AI_SYSTEM_PROMPT_PATH, encoding="utf-8") as f:
                    self._custom_prompt = f.read().strip()
                # Log at DEBUG when likely from tools/subprocesses to reduce app.log noise; INFO for main service
                _is_tool = "development_tools" in " ".join(
                    getattr(sys, "argv", [])
                ) or "run_dev_tools" in " ".join(getattr(sys, "argv", []))
                (logger.debug if _is_tool else logger.info)(
                    f"Loaded custom system prompt from {AI_SYSTEM_PROMPT_PATH}"
                )
            else:
                logger.warning(
                    f"Custom system prompt file not found: {AI_SYSTEM_PROMPT_PATH}"
                )
        except Exception as e:
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

        # If custom prompt is available and type is wellness/neurodivergent_support, use it
        if self._custom_prompt and prompt_type in [
            "wellness",
            "neurodivergent_support",
        ]:
            logger.debug(f"Using custom prompt for type: {prompt_type}")
            return self._custom_prompt

        # Otherwise use fallback prompts
        template = self._fallback_prompts.get(prompt_type)
        if template:
            logger.debug(f"Using fallback prompt for type: {prompt_type}")
            return template.content

        # Default to wellness prompt
        logger.debug(
            f"Prompt type '{prompt_type}' not found, using default wellness prompt"
        )
        return self._fallback_prompts["wellness"].content

    @handle_errors("getting prompt template", default_return=None)
    def get_prompt_template(self, prompt_type: str) -> PromptTemplate | None:
        """
        Get the full prompt template for the given type

        Args:
            prompt_type: Type of prompt

        Returns:
            PromptTemplate object or None if not found
        """
        # Check custom templates first
        if prompt_type in self._prompt_templates:
            return self._prompt_templates[prompt_type]

        # Check fallback templates
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
        self._load_custom_prompt()
        logger.info("Custom system prompt reloaded")

    @handle_errors("checking if custom prompt exists", default_return=False)
    def has_custom_prompt(self) -> bool:
        """Check if a custom prompt is loaded."""
        return self._custom_prompt is not None

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

        # Add custom templates
        for name, template in self._prompt_templates.items():
            prompts[name] = template.description

        # Add fallback templates
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
