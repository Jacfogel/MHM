"""Tests for product-AI prompt-flow categorization."""

from __future__ import annotations

import pytest

from ai.prompts.flows import PRODUCT_AI_PROMPT_FLOWS, get_product_ai_prompt_flow


pytestmark = [pytest.mark.unit, pytest.mark.ai]


def test_product_ai_prompt_flows_are_explicitly_categorized():
    assert set(PRODUCT_AI_PROMPT_FLOWS) == {
        "chat_response",
        "action_interpretation",
        "action_result_response",
        "fallback_response",
    }

    chat_flow = get_product_ai_prompt_flow("chat_response")
    assert chat_flow.context_source == "ai.context.service.AIContextEnvelope"
    assert chat_flow.prompt_owner == "ai.context"
    assert "persona" in chat_flow.categories
    assert "data_honesty" in chat_flow.categories
    assert "reply_rules" in chat_flow.categories
    assert "available_actions" in chat_flow.categories

    action_flow = get_product_ai_prompt_flow("action_interpretation")
    assert "action_boundaries" in action_flow.categories
    assert "available_actions" in action_flow.categories
    assert "ai.prompts.action_catalog.AIActionCatalog" in action_flow.context_source
