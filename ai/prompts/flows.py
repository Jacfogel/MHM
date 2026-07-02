"""Named product-AI prompt flows and category ownership."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from core.error_handling import handle_errors


PromptFlowName = Literal[
    "chat_response",
    "action_interpretation",
    "action_result_response",
    "fallback_response",
]

# Runtime-only category: injects action catalog summary, not a prompt file.
RUNTIME_PROMPT_CATEGORIES = frozenset({"available_actions"})


@dataclass(frozen=True)
class ProductAIPromptFlow:
    """Declarative prompt-flow contract for product AI."""

    name: PromptFlowName
    purpose: str
    categories: tuple[str, ...]
    context_source: str
    prompt_owner: str


PRODUCT_AI_PROMPT_FLOWS: dict[PromptFlowName, ProductAIPromptFlow] = {
    "chat_response": ProductAIPromptFlow(
        name="chat_response",
        purpose="Answer conversational requests from user context without executing app actions.",
        categories=(
            "persona",
            "reply_rules",
            "data_honesty",
            "action_boundaries",
            "available_actions",
        ),
        context_source="ai.context.service.AIContextEnvelope",
        prompt_owner="ai.context",
    ),
    "action_interpretation": ProductAIPromptFlow(
        name="action_interpretation",
        purpose="Interpret whether a request should answer, clarify, or execute app actions.",
        categories=(
            "data_honesty",
            "action_boundaries",
            "available_actions",
        ),
        context_source="ai.context.service.AIContextEnvelope + ai.prompts.action_catalog.AIActionCatalog",
        prompt_owner="ai.prompts.command_interpreter",
    ),
    "action_result_response": ProductAIPromptFlow(
        name="action_result_response",
        purpose="Summarize actual handler execution results to the user.",
        categories=(
            "persona",
            "reply_rules",
            "action_boundaries",
        ),
        context_source="handler result metadata + refreshed AIContextEnvelope",
        prompt_owner="future ai.action_executor/response flow",
    ),
    "fallback_response": ProductAIPromptFlow(
        name="fallback_response",
        purpose="Produce deterministic responses when model planning or generation is unavailable.",
        categories=(
            "persona",
            "data_honesty",
            "action_boundaries",
            "available_actions",
        ),
        context_source="AIContextEnvelope or compact fallback context",
        prompt_owner="ai.fallback",
    ),
}


@handle_errors("getting product AI prompt flow")
def get_product_ai_prompt_flow(name: PromptFlowName) -> ProductAIPromptFlow:
    """Return the prompt-flow contract for a named product-AI flow."""
    return PRODUCT_AI_PROMPT_FLOWS[name]
