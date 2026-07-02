"""Tests for product-AI prompt-flow categorization."""

from __future__ import annotations

import pytest

from ai.prompt_flows import PRODUCT_AI_PROMPT_FLOWS, get_product_ai_prompt_flow


pytestmark = [pytest.mark.unit, pytest.mark.ai]


def test_product_ai_prompt_flows_are_explicitly_categorized():
    assert set(PRODUCT_AI_PROMPT_FLOWS) == {
        "chat_response",
        "action_interpretation",
        "action_result_response",
        "fallback_response",
    }

    chat_flow = get_product_ai_prompt_flow("chat_response")
    assert chat_flow.context_source == "ai.context_service.AIContextEnvelope"
    assert chat_flow.prompt_owner == "ai.conversational_context"
    assert "identity_and_tone" in chat_flow.categories
    assert "context_data_access" in chat_flow.categories
    assert "conversation_behavior" in chat_flow.categories

    action_flow = get_product_ai_prompt_flow("action_interpretation")
    assert "action_interpretation" in action_flow.categories
    assert "ai.action_catalog.AIActionCatalog" in action_flow.context_source
