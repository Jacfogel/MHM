"""Tests for product-AI prompt-flow categorization."""

from __future__ import annotations

import pytest

from ai.prompts.flows import (
    PRODUCT_AI_PROMPT_FLOWS,
    RUNTIME_PROMPT_CATEGORIES,
    get_product_ai_prompt_flow,
)
from ai.prompts.manager import _PRODUCT_AI_CATEGORY_FILENAMES


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


def test_product_ai_flow_categories_align_with_filename_map():
    """File-backed flow categories must match _PRODUCT_AI_CATEGORY_FILENAMES."""
    flow_categories = {
        category
        for flow in PRODUCT_AI_PROMPT_FLOWS.values()
        for category in flow.categories
    }
    file_backed_flow_categories = flow_categories - RUNTIME_PROMPT_CATEGORIES
    filename_categories = set(_PRODUCT_AI_CATEGORY_FILENAMES)

    assert file_backed_flow_categories <= filename_categories
    assert filename_categories <= flow_categories
    assert flow_categories >= RUNTIME_PROMPT_CATEGORIES
