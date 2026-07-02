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
            "identity_and_tone",
            "product_capabilities",
            "context_data_access",
            "context_selection_and_memory",
            "conversation_behavior",
            "fallback_behavior",
        ),
        context_source="ai.context_service.AIContextEnvelope",
        prompt_owner="ai.conversational_context",
    ),
    "action_interpretation": ProductAIPromptFlow(
        name="action_interpretation",
        purpose="Interpret whether a request should answer, clarify, or execute app actions.",
        categories=(
            "product_capabilities",
            "context_selection_and_memory",
            "action_interpretation",
            "fallback_behavior",
        ),
        context_source="ai.context_service.AIContextEnvelope + ai.action_catalog.AIActionCatalog",
        prompt_owner="ai.command_interpreter",
    ),
    "action_result_response": ProductAIPromptFlow(
        name="action_result_response",
        purpose="Summarize actual handler execution results to the user.",
        categories=(
            "identity_and_tone",
            "conversation_behavior",
            "action_execution",
            "fallback_behavior",
        ),
        context_source="handler result metadata + refreshed AIContextEnvelope",
        prompt_owner="future ai.action_executor/response flow",
    ),
    "fallback_response": ProductAIPromptFlow(
        name="fallback_response",
        purpose="Produce deterministic responses when model planning or generation is unavailable.",
        categories=(
            "identity_and_tone",
            "product_capabilities",
            "context_data_access",
            "fallback_behavior",
        ),
        context_source="AIContextEnvelope or compact fallback context",
        prompt_owner="ai.fallback_responses",
    ),
}


@handle_errors("getting product AI prompt flow")
def get_product_ai_prompt_flow(name: PromptFlowName) -> ProductAIPromptFlow:
    """Return the prompt-flow contract for a named product-AI flow."""
    return PRODUCT_AI_PROMPT_FLOWS[name]
