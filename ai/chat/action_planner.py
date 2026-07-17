"""AI action planning: decide answer, clarify, or execute app actions."""

from __future__ import annotations

import re
from typing import Any

from ai.prompts.action_catalog import (
    AIActionCatalog,
    AIActionPlan,
    AIActionRequest,
    ResponseIntent,
    get_action_catalog,
)
from ai.client.lm_studio_client import call_lm_studio_api
from ai.prompts.command_interpreter import get_command_interpreter
from core.config import (
    AI_ACTION_PLAN_MIN_CONFIDENCE,
    AI_COMMAND_PARSING_TIMEOUT,
    AI_COMMAND_TEMPERATURE,
)
from core.error_handling import handle_errors
from core.logger import get_component_logger

logger = get_component_logger("ai")

# Keep this short: local models often have 2k context. Do not stack chat
# category files, command.txt, or full AIContextEnvelope into planning.
# ACTION-first matches the existing command parser format that local models
# already follow more reliably than INTENT-first prose.
_PLANNING_SYSTEM_TEMPLATE = """Extract one MHM action as key-value lines only. No prose, JSON, or code.

Example:
ACTION: create_task
TITLE: pack hiking bag
CONFIDENCE: 0.9

Chat/venting/no action:
ACTION: unknown

Missing required detail:
INTENT: clarify
QUESTION: What should the task be called?

Rules: ACTION must be unknown or one of: {actions}
Copy field values from the user message only. Do not invent dates, locations, or titles.
"""

_PLANNING_MAX_TOKENS = 60
_PLANNING_STOP_SEQUENCES = [
    '"""',
    "```",
    "\ndef ",
    "\nUser:",
    "\n###",
    "\nStart with",
    "\nExamples:",
    "\n[",
]

_SHARED_PLAN_KEYS = frozenset(
    {"INTENT", "QUESTION", "CLARIFICATION_QUESTION", "NOTES"}
)

_INTENT_ALIASES = {
    "answer": "answer_only",
    "chat": "answer_only",
    "conversation": "answer_only",
    "execute": "execute_action",
    "action": "execute_action",
    "command": "execute_action",
    "clarification": "clarify",
    "ask": "clarify",
}

_ACTION_NAME_ALIASES = {
    "create task": "create_task",
    "list tasks": "list_tasks",
    "complete task": "complete_task",
    "delete task": "delete_task",
    "update task": "update_task",
    "unknown": "unknown",
}

_ENTITY_KEY_ALIASES = {
    "TITLE": "title",
    "TASK_ID": "task_identifier",
    "TASKID": "task_identifier",
    "TASK_IDENTIFIER": "task_identifier",
    "PRIORITY": "priority",
    "DUE_DATE": "due_date",
    "DUEDATE": "due_date",
    "DUE_TIME": "due_time",
    "DETAILS": "description",
    "DESCRIPTION": "description",
    "NOTE": "note",
    "NOTE_TEXT": "note_text",
    "TAGS": "tags",
    "GROUP": "group",
    "TEMPLATE_REF": "template_ref",
    "FILTER": "filter",
    "TAG": "tag",
    "QUERY": "query",
    "ITEM_TEXT": "item_text",
    "TEXT": "text",
}

# Free-text fields that must be grounded in the user message (blocks example leakage).
_GROUNDED_ENTITY_KEYS = frozenset(
    {
        "title",
        "description",
        "note",
        "note_text",
        "query",
        "item_text",
        "text",
    }
)


class ActionPlanner:
    """Plan product-AI responses and optional app actions from user messages."""

    @handle_errors("building action planning prompt", default_return=[])
    def build_planning_messages(
        self, user_id: str | None, user_message: str
    ) -> list[dict[str, str]]:
        """Build compact LM Studio messages for action planning.

        ``user_id`` is accepted by callers but unused today. Full context envelopes
        are intentionally omitted so local models with ~2k context can run planning.
        """
        _ = user_id
        catalog = get_action_catalog()
        system_content = _PLANNING_SYSTEM_TEMPLATE.format(
            actions=catalog.to_planning_prompt_summary()
        ).strip()
        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": (user_message or "").strip()},
        ]

    @handle_errors("planning action from message", default_return=None)
    def plan_from_message(
        self,
        user_message: str,
        *,
        user_id: str | None = None,
        ai_chatbot=None,
    ) -> AIActionPlan | None:
        """Call the model (when available) and parse an action plan."""
        if not user_message or not user_message.strip():
            return answer_only_plan("", planning_method="empty_input")

        if ai_chatbot is None:
            from ai.chat.chatbot import get_ai_chatbot

            ai_chatbot = get_ai_chatbot()

        if not ai_chatbot.is_ai_available():
            logger.debug("AI unavailable for action planning; defaulting to answer_only")
            return answer_only_plan(user_message, planning_method="ai_unavailable")

        messages = self.build_planning_messages(user_id, user_message)
        if not messages:
            return answer_only_plan(user_message, planning_method="prompt_build_failed")

        # Call LM Studio with the compact planning messages directly. Do not route
        # through generate_response(mode="command"), which rebuilds a different prompt.
        raw_response = call_lm_studio_api(
            messages=messages,
            max_tokens=_PLANNING_MAX_TOKENS,
            temperature=AI_COMMAND_TEMPERATURE,
            timeout=AI_COMMAND_PARSING_TIMEOUT,
            stop=_PLANNING_STOP_SEQUENCES,
        )
        if not raw_response or not str(raw_response).strip():
            logger.warning(
                "Action planner received empty LM Studio response; using answer_only"
            )
            return answer_only_plan(user_message, planning_method="ai_empty_response")

        return parse_action_plan_from_text(
            _trim_planner_output(raw_response),
            source_message=user_message,
            catalog=get_action_catalog(),
            planning_method="ai_planner",
        )

    @handle_errors("planning action from text", default_return=None)
    def plan_from_text(
        self,
        planner_output: str,
        *,
        source_message: str,
        catalog: AIActionCatalog | None = None,
        planning_method: str = "text",
    ) -> AIActionPlan | None:
        """Parse planner output text into an action plan (test and replay helper)."""
        return parse_action_plan_from_text(
            planner_output,
            source_message=source_message,
            catalog=catalog or get_action_catalog(),
            planning_method=planning_method,
        )


@handle_errors("creating answer-only action plan", default_return=None)
def answer_only_plan(
    source_message: str, *, planning_method: str = "default"
) -> AIActionPlan | None:
    """Return a safe answer-only plan."""
    return AIActionPlan(
        response_intent="answer_only",
        source_message=source_message,
        planning_method=planning_method,
    )


@handle_errors("creating clarify action plan", default_return=None)
def clarify_plan(
    source_message: str,
    question: str,
    *,
    planning_method: str = "default",
) -> AIActionPlan | None:
    """Return a clarification plan with one user-facing question."""
    return AIActionPlan(
        response_intent="clarify",
        clarification_question=question.strip() or "Could you share a bit more detail?",
        source_message=source_message,
        planning_method=planning_method,
    )


@handle_errors("parsing action plan from text", default_return=None)
def parse_action_plan_from_text(
    planner_output: str,
    *,
    source_message: str,
    catalog: AIActionCatalog | None = None,
    planning_method: str = "text",
) -> AIActionPlan | None:
    """Parse model planner output into a validated AIActionPlan."""
    catalog = catalog or get_action_catalog()
    shared, action_blocks = _parse_plan_structure(planner_output or "")
    fields = dict(shared)
    if action_blocks:
        fields.update(action_blocks[0])
    if not fields.get("INTENT") and not fields.get("ACTION"):
        cleaned = get_command_interpreter().extract_command_from_response(
            planner_output or ""
        )
        shared, action_blocks = _parse_plan_structure(cleaned or planner_output or "")
        fields = dict(shared)
        if action_blocks:
            fields.update(action_blocks[0])
    intent = _normalize_intent(fields.get("INTENT", ""))

    if not intent:
        if fields.get("ACTION") and fields.get("ACTION") != "unknown":
            intent = "execute_action"
        elif fields.get("QUESTION"):
            intent = "clarify"
        else:
            return answer_only_plan(
                source_message, planning_method=f"{planning_method}_malformed"
            )

    if intent == "answer_only":
        return AIActionPlan(
            response_intent="answer_only",
            response_notes=fields.get("NOTES"),
            source_message=source_message,
            planning_method=planning_method,
        )

    if intent == "clarify":
        question = fields.get("QUESTION") or fields.get("CLARIFICATION_QUESTION")
        if not question:
            return clarify_plan(
                source_message,
                "Could you share a bit more detail about what you'd like me to do?",
                planning_method=f"{planning_method}_missing_question",
            )
        return AIActionPlan(
            response_intent="clarify",
            clarification_question=question.strip(),
            response_notes=fields.get("NOTES"),
            source_message=source_message,
            planning_method=planning_method,
        )

    if intent == "execute_action":
        return _build_execute_plan(
            planner_output or "",
            source_message=source_message,
            catalog=catalog,
            planning_method=planning_method,
        )

    return answer_only_plan(
        source_message, planning_method=f"{planning_method}_unknown_intent"
    )


@handle_errors("trimming planner model output", default_return="")
def _trim_planner_output(planner_output: str) -> str:
    """Drop common local-model trailing junk after the first plan block."""
    text = (planner_output or "").strip()
    if not text:
        return ""
    cut_markers = (
        "\nStart with",
        "\n###",
        "\nUser:",
        "\nExamples:",
        '"""',
        "```",
        "\ndef ",
    )
    cut_at = len(text)
    for marker in cut_markers:
        idx = text.find(marker)
        if idx >= 0:
            cut_at = min(cut_at, idx)
    return text[:cut_at].strip()


@handle_errors("building execute-action plan", default_return=None)
def _build_execute_plan(
    planner_output: str,
    *,
    source_message: str,
    catalog: AIActionCatalog,
    planning_method: str,
) -> AIActionPlan | None:
    """Build an execute_action plan or downgrade to clarify/answer_only."""
    shared, action_blocks = _parse_plan_structure(planner_output)
    if not action_blocks:
        return answer_only_plan(
            source_message, planning_method=f"{planning_method}_unknown_action"
        )

    default_confidence = shared.get("CONFIDENCE")
    requests: list[AIActionRequest] = []
    for block in action_blocks:
        merged_fields = dict(block)
        if "CONFIDENCE" not in merged_fields and default_confidence:
            merged_fields["CONFIDENCE"] = default_confidence

        request, downgrade = _build_action_request_from_fields(
            merged_fields,
            source_message=source_message,
            catalog=catalog,
            planning_method=planning_method,
        )
        if downgrade is not None:
            return downgrade
        if request is not None:
            requests.append(request)

    if not requests:
        return answer_only_plan(
            source_message, planning_method=f"{planning_method}_unknown_action"
        )

    return AIActionPlan(
        response_intent="execute_action",
        actions=tuple(requests),
        response_notes=shared.get("NOTES"),
        source_message=source_message,
        planning_method=planning_method,
    )


@handle_errors("building action request from planner fields", default_return=(None, None))
def _build_action_request_from_fields(
    fields: dict[str, str],
    *,
    source_message: str,
    catalog: AIActionCatalog,
    planning_method: str,
) -> tuple[AIActionRequest | None, AIActionPlan | None]:
    """Validate one action block and return a request or downgrade plan."""
    action_name = _normalize_action_name(fields.get("ACTION", ""))
    if not action_name or action_name == "unknown":
        return None, answer_only_plan(
            source_message, planning_method=f"{planning_method}_unknown_action"
        )

    action_def = catalog.get(action_name)
    if action_def is None:
        return None, clarify_plan(
            source_message,
            f"I'm not sure how to handle '{action_name}' yet. Could you rephrase?",
            planning_method=f"{planning_method}_invalid_action",
        )

    confidence = _parse_confidence(fields.get("CONFIDENCE"))
    entities = _extract_entities_from_fields(
        fields, source_message=source_message
    )
    missing_required = [
        field_name
        for field_name in action_def.required_fields
        if not entities.get(field_name)
    ]
    if missing_required:
        label = missing_required[0].replace("_", " ")
        return None, clarify_plan(
            source_message,
            fields.get("QUESTION")
            or f"What should the {label} be for this {action_name.replace('_', ' ')}?",
            planning_method=f"{planning_method}_missing_fields",
        )

    if confidence < AI_ACTION_PLAN_MIN_CONFIDENCE:
        return None, clarify_plan(
            source_message,
            fields.get("QUESTION")
            or "I want to make sure I understood - could you confirm what you'd like me to do?",
            planning_method=f"{planning_method}_low_confidence",
        )

    return (
        AIActionRequest(
            action_name=action_name,
            entities=entities,
            confidence=confidence,
            source_message=source_message,
            requires_confirmation=action_def.requires_confirmation,
        ),
        None,
    )


@handle_errors("parsing planner structure", default_return=({}, []))
def _parse_plan_structure(text: str) -> tuple[dict[str, str], list[dict[str, str]]]:
    """Parse shared planner fields and ordered per-action blocks."""
    shared: dict[str, str] = {}
    action_blocks: list[dict[str, str]] = []
    current: dict[str, str] | None = None

    for line in (text or "").splitlines():
        line_stripped = line.strip()
        if not line_stripped or line_stripped.startswith("---"):
            continue
        if ":" not in line_stripped:
            continue
        key, value = line_stripped.split(":", 1)
        key = key.strip().upper()
        value = value.strip()
        if not key or not value:
            continue

        if key == "ACTION":
            if current:
                action_blocks.append(current)
            current = {"ACTION": value}
        elif key in _SHARED_PLAN_KEYS and current is None:
            shared[key] = value
        elif current is not None:
            current[key] = value
        else:
            shared[key] = value

    if current:
        action_blocks.append(current)

    if action_blocks:
        return shared, action_blocks

    flat = _parse_key_value_fields(text)
    if not flat.get("ACTION"):
        return flat, []

    action_fields = {
        key: value
        for key, value in flat.items()
        if key not in _SHARED_PLAN_KEYS
    }
    shared_fields = {
        key: value for key, value in flat.items() if key in _SHARED_PLAN_KEYS
    }
    return shared_fields, [action_fields]


@handle_errors("parsing planner key-value fields", default_return={})
def _parse_key_value_fields(text: str) -> dict[str, str]:
    """Parse INTENT/ACTION/entity key-value lines from planner output."""
    fields: dict[str, str] = {}
    for line in (text or "").splitlines():
        line_stripped = line.strip()
        if ":" not in line_stripped:
            continue
        key, value = line_stripped.split(":", 1)
        key = key.strip().upper()
        value = value.strip()
        if key and value:
            fields[key] = value
    return fields


@handle_errors("normalizing planner intent", default_return=None)
def _normalize_intent(raw_intent: str) -> ResponseIntent | None:
    """Normalize planner intent labels."""
    normalized = re.sub(r"[^a-z_]+", "_", (raw_intent or "").strip().lower())
    normalized = normalized.strip("_")
    if not normalized:
        return None
    normalized = _INTENT_ALIASES.get(normalized, normalized)
    if normalized in {"answer_only", "execute_action", "clarify"}:
        return normalized  # type: ignore[return-value]
    return None


@handle_errors("normalizing planner action name", default_return="")
def _normalize_action_name(raw_action: str) -> str:
    """Normalize canonical action names from planner output."""
    action = (raw_action or "").strip().lower()
    if not action:
        return ""
    action = _ACTION_NAME_ALIASES.get(action, action)
    return re.sub(r"[^a-z0-9_]+", "_", action).strip("_")


@handle_errors("parsing planner confidence", default_return=0.0)
def _parse_confidence(raw_confidence: str | None) -> float:
    """Parse a confidence score from planner output."""
    if not raw_confidence:
        return AI_ACTION_PLAN_MIN_CONFIDENCE
    try:
        value = float(raw_confidence.strip())
    except (TypeError, ValueError):
        return AI_ACTION_PLAN_MIN_CONFIDENCE
    return max(0.0, min(1.0, value))


@handle_errors("checking grounded planner entity value", default_return=False)
def _entity_value_grounded_in_message(value: str, source_message: str) -> bool:
    """Return True when a free-text entity value is supported by the user message."""
    src = (source_message or "").casefold()
    val = (value or "").casefold().strip()
    if not val or not src:
        return False
    if val in src:
        return True
    words = [word for word in re.findall(r"[a-z0-9]+", val) if len(word) > 2]
    if not words:
        return False
    return all(word in src for word in words)


@handle_errors("extracting planner entity fields", default_return={})
def _extract_entities_from_fields(
    fields: dict[str, str],
    *,
    source_message: str = "",
) -> dict[str, Any]:
    """Map planner entity keys to handler entity names."""
    reserved = {
        "INTENT",
        "ACTION",
        "CONFIDENCE",
        "QUESTION",
        "CLARIFICATION_QUESTION",
        "NOTES",
    }
    entities: dict[str, Any] = {}
    for key, value in fields.items():
        if key in reserved or not value:
            continue
        entity_key = _ENTITY_KEY_ALIASES.get(key, key.lower())
        if entity_key in _GROUNDED_ENTITY_KEYS and not _entity_value_grounded_in_message(
            value, source_message
        ):
            continue
        entities[entity_key] = value
    return entities


_action_planner: ActionPlanner | None = None


@handle_errors("getting action planner")
def get_action_planner() -> ActionPlanner:
    """Return the shared action planner."""
    global _action_planner
    if _action_planner is None:
        _action_planner = ActionPlanner()
    return _action_planner
