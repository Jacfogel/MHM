# ai/command_interpreter.py

"""Command interpretation: mode detection, parsing prompts, and structured extraction."""

import json

from ai.prompts.manager import get_prompt_manager
from core.error_handling import handle_errors

_CLARIFICATION_PROMPT_SUFFIX = (
    "\n\nCLARIFICATION MODE: If the user's request is ambiguous or missing required "
    "fields (for example task title or time), ask ONE short clarification question in "
    "plain language. Do not return ACTION: lines unless you can identify a specific action."
)

# Mode-detection vocabulary aligned with rule-based intents in command_parser (not exhaustive).
_COMMAND_KEYWORDS = (
    "remind",
    "todo",
    "schedule",
    "add",
    "append",
    "remove",
    "delete",
    "call",
    "message",
    "cancel",
    "stop",
    "task",
    "tasks",
    "note",
    "notes",
    "journal",
    "notebook",
    "entry",
    "entries",
    "checkin",
    "check-in",
    "check in",
    "analytics",
    "mood",
    "profile",
    "pin",
    "unpin",
    "archive",
    "tag",
    "tags",
    "list",
    "complete",
    "done",
    "help",
    "commands",
    "examples",
    "inbox",
    "group",
    "template",
    "templates",
    "overdue",
    "toggle",
    "replace",
    "search",
)

# Multi-word hints for intents where a bare keyword would false-positive on chat (e.g. "update my feelings").
_COMMAND_PHRASE_HINTS = (
    "show tasks",
    "show task",
    "show my tasks",
    "show inbox",
    "show group",
    "show entry",
    "show note",
    "show notes",
    "show schedule",
    "show profile",
    "show analytics",
    "show archived",
    "show checkin",
    "show check-in",
    "list inbox",
    "list group",
    "list tasks",
    "list task",
    "list pinned",
    "list archived",
    "search for",
    "search entries",
    "search notes",
    "append note to task",
    "add note to task",
    "update task",
    "update profile",
    "update schedule",
    "tasks in group",
    "task group:",
    "group:",
    "in group",
    "from template",
    "help notebook",
    "examples notebook",
)

_TASK_INTENT_PHRASES = (
    "i need to",
    "i should",
    "i want to",
    "i have to",
    "remind me to",
    "don't forget to",
    "do not forget to",
    "remember to",
    "i need",
    "i'd like to",
    "i want",
    "got to",
    "gotta",
)

_TASK_VERBS = (
    "buy",
    "get",
    "do",
    "call",
    "schedule",
    "complete",
    "finish",
    "pick up",
    "go to",
    "make",
    "send",
    "email",
    "pay",
    "book",
    "order",
)

_EXPLICIT_COMMAND_WORDS = ("add", "create", "new")


class CommandInterpreter:
    """Detect command-oriented prompts and extract structured command candidates."""

    # devtools: intentional[duplicate-functions]: thin_prompt_component_constructors
    @handle_errors("initializing command interpreter", default_return=None)
    def __init__(self) -> None:
        self._prompt_manager = get_prompt_manager()

    @handle_errors("detecting prompt mode", default_return="chat")
    def detect_mode(self, user_prompt: str) -> str:
        """Detect whether the prompt is a command or a chat query."""
        prompt_lower = user_prompt.lower().strip()
        if not prompt_lower:
            return "chat"

        if self.is_natural_language_task_request(prompt_lower):
            return "command_with_clarification"

        if not self.has_command_keyword(prompt_lower):
            return "chat"

        words = prompt_lower.split()
        stripped_prompt = prompt_lower.strip("?.! ")
        if self.needs_command_clarification(prompt_lower, words, stripped_prompt):
            return "command_with_clarification"
        return "command"

    @handle_errors("detecting natural language task request", default_return=False)
    def is_natural_language_task_request(self, prompt_lower: str) -> bool:
        """Detect natural-language task intents that likely need clarification."""
        has_task_intent = any(phrase in prompt_lower for phrase in _TASK_INTENT_PHRASES)
        has_task_verb = any(verb in prompt_lower for verb in _TASK_VERBS)
        has_explicit_command_word = any(
            word in prompt_lower for word in _EXPLICIT_COMMAND_WORDS
        )
        return has_task_intent and has_task_verb and not has_explicit_command_word

    @handle_errors("detecting command keyword", default_return=False)
    def has_command_keyword(self, prompt_lower: str) -> bool:
        """Return True when prompt appears command-oriented."""
        if any(keyword in prompt_lower for keyword in _COMMAND_KEYWORDS):
            return True
        return any(phrase in prompt_lower for phrase in _COMMAND_PHRASE_HINTS)

    @handle_errors("detecting clarification need for command", default_return=True)
    def needs_command_clarification(
        self, prompt_lower: str, words: list[str], stripped_prompt: str
    ) -> bool:
        """Determine whether a command-like prompt is too ambiguous."""
        clarification_phrases = [
            "not sure",
            "don't know",
            "should i",
            "should we",
            "could you help",
            "can you help",
            "help me decide",
            "need help",
            "figure out",
            "what should i",
            "what should we",
            "which task should",
            "which reminder should",
            "any suggestions",
            "what do you recommend",
            "i'm unsure",
        ]

        minimal_command_prompts = {
            "remind me",
            "add task",
            "add a task",
            "create task",
            "create a task",
            "delete task",
            "delete a task",
            "complete task",
            "complete a task",
            "schedule",
            "schedule something",
            "start checkin",
            "start a checkin",
            "start check-in",
            "stop checkin",
            "stop a checkin",
            "create note",
            "create a note",
            "new note",
            "list tasks",
            "show tasks",
            "show profile",
            "show inbox",
            "help notebook",
            "append note to task",
            "add note to task",
            "list inbox",
            "search for",
        }

        request_question_patterns = [
            "can you",
            "could you",
            "would you",
            "will you",
        ]

        detail_markers = [
            " to ",
            " for ",
            " with ",
            " about ",
            " regarding ",
            " on ",
            " at ",
            " by ",
            " before ",
            " after ",
        ]

        if (
            len(words) <= 3
            or stripped_prompt in minimal_command_prompts
            or any(phrase in prompt_lower for phrase in clarification_phrases)
        ):
            return True

        has_question_request = "?" in prompt_lower and any(
            pattern in prompt_lower for pattern in request_question_patterns
        )
        return bool(has_question_request and not any(marker in prompt_lower for marker in detail_markers))

    @handle_errors(
        "creating command parsing prompt",
        default_return=[
            {"role": "system", "content": "You are a command parser."},
            {"role": "user", "content": ""},
        ],
    )
    def create_command_parsing_prompt(
        self,
        user_prompt: str,
        *,
        clarification: bool = False,
        user_id: str | None = None,
    ) -> list:
        """Create a prompt instructing the model to return structured command output."""
        from ai.context.service import build_ai_context_envelope
        from ai.prompts.action_catalog import get_action_catalog

        catalog = get_action_catalog()
        context_view = None
        if user_id:
            context_view = build_ai_context_envelope(
                user_id,
                requested_intent="action_interpretation",
                prompt_request=user_prompt,
                include_conversation_history=False,
            )

        composed = self._prompt_manager.compose_product_prompt(
            "action_interpretation",
            context_view=context_view,
            action_catalog=catalog,
        )
        format_instructions = self._prompt_manager.get_command_format_instructions()
        system_sections = []
        if composed and composed.content:
            system_sections.append(composed.content)
        if format_instructions:
            system_sections.append(format_instructions)
        system_content = "\n\n".join(system_sections)
        if not system_content:
            system_content = self._prompt_manager.get_prompt("command")
        if clarification:
            system_content = system_content + _CLARIFICATION_PROMPT_SUFFIX

        system_message = {"role": "system", "content": system_content}
        user_message = {"role": "user", "content": user_prompt}
        return [system_message, user_message]

    @handle_errors("extracting command from response", default_return="")
    def extract_command_from_response(self, response: str) -> str:
        """
        Extract command structure from command mode responses.
        Handles JSON, key-value pairs (ACTION: ...), or natural language.
        """
        if not response:
            return response

        try:
            parsed = json.loads(response.strip())
            return json.dumps(parsed)
        except (json.JSONDecodeError, ValueError):
            pass

        if "ACTION:" in response or "action:" in response:
            lines = response.split("\n")
            command_lines = []
            for line in lines:
                line_stripped = line.strip()
                if (
                    line_stripped.startswith("import ")
                    or line_stripped.startswith("from ")
                    or line_stripped.startswith("def ")
                    or line_stripped.startswith("class ")
                    or line_stripped.startswith('"""')
                    or line_stripped.startswith("'''")
                    or line_stripped.startswith("#")
                    or line_stripped.startswith("```python")
                    or line_stripped.startswith("```")
                    or line_stripped == "```"
                ):
                    continue
                if ":" in line_stripped and (
                    line_stripped.startswith("ACTION")
                    or line_stripped.startswith("action")
                    or any(
                        keyword in line_stripped.upper()
                        for keyword in ["TITLE", "DETAILS", "PRIORITY", "DUE_DATE"]
                    )
                ):
                    command_lines.append(line_stripped)

            if command_lines:
                return "\n".join(command_lines)

        start_idx = None
        brace_count = 0

        for i, char in enumerate(response):
            if char == "{":
                if start_idx is None:
                    start_idx = i
                brace_count += 1
            elif char == "}":
                brace_count -= 1
                if brace_count == 0 and start_idx is not None:
                    json_str = response[start_idx : i + 1]
                    try:
                        parsed = json.loads(json_str)
                        return json.dumps(parsed)
                    except (json.JSONDecodeError, ValueError):
                        start_idx = None
                        brace_count = 0
                        continue

        lines = response.split("\n")
        clean_lines = []
        for line in lines:
            line_stripped = line.strip()
            if (
                line_stripped.startswith("import ")
                or line_stripped.startswith("from ")
                or line_stripped.startswith("def ")
                or line_stripped.startswith("class ")
                or line_stripped.startswith('"""')
                or line_stripped.startswith("'''")
                or line_stripped.startswith("#")
                or line_stripped.startswith("```python")
                or line_stripped.startswith("```")
                or line_stripped == "```"
                or "This function takes" in line_stripped
                or "This function" in line_stripped
                or "takes in a message" in line_stripped.lower()
                or "returns the user" in line_stripped.lower()
                or line_stripped.endswith("_re")
                or (
                    len(line_stripped.split()) == 1
                    and "_" in line_stripped
                    and not line_stripped.startswith("ACTION")
                )
            ):
                continue
            if line_stripped:
                clean_lines.append(line_stripped)

        if clean_lines:
            return "\n".join(clean_lines)

        return response


_command_interpreter: CommandInterpreter | None = None


@handle_errors("getting command interpreter")
def get_command_interpreter() -> CommandInterpreter:
    """Return the shared command interpreter."""
    global _command_interpreter
    if _command_interpreter is None:
        _command_interpreter = CommandInterpreter()
    return _command_interpreter
