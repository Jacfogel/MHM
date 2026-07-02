"""Tests for category-composed product-AI prompts."""

from __future__ import annotations

import pytest

from ai.context.service import AIContextEnvelope, AIContextSection
from ai.prompts.manager import PromptManager, PromptTemplate


pytestmark = [pytest.mark.unit, pytest.mark.ai]


def _section(name: str, data, prompt_text: str = "") -> AIContextSection:
    return AIContextSection(name=name, data=data, prompt_text=prompt_text)


def _envelope() -> AIContextEnvelope:
    return AIContextEnvelope(
        metadata={"user_id": "user-1", "included_sections": ["account", "tasks"]},
        sections={
            "account": _section(
                "account",
                {"preferred_name": "Julie"},
                "Account: preferred name Julie.",
            ),
            "tasks": _section(
                "tasks",
                {"enabled": False, "active": []},
                "Tasks: disabled; 0 active.",
            ),
            "action_catalog": _section(
                "action_catalog",
                {
                    "summary": "Actions: create_task (tasks; required: title)",
                    "available": ["create_task"],
                },
                "Actions: create_task (tasks; required: title)",
            ),
        },
    )


def test_compose_chat_response_prompt_uses_flow_categories_in_order():
    manager = PromptManager()

    template = manager.compose_product_prompt(
        "chat_response",
        context_view=_envelope(),
    )

    assert isinstance(template, PromptTemplate)
    assert template.name == "product_ai_chat_response"
    content = template.content
    assert content.index("[persona]") < content.index("[reply_rules]")
    assert content.index("[reply_rules]") < content.index("[data_honesty]")
    assert content.index("[data_honesty]") < content.index("[action_boundaries]")
    assert content.index("[action_boundaries]") < content.index("[available_actions]")
    assert "MHM's in-app assistant" in content
    assert "Account: preferred name Julie." in content
    assert "Tasks: disabled; 0 active." in content


def test_compose_chat_response_prompt_includes_generated_capabilities():
    manager = PromptManager()

    template = manager.compose_product_prompt("chat_response", context_view=_envelope())

    assert template is not None
    assert "[available_actions]" in template.content
    assert "create_task (tasks; required: title)" in template.content


def test_compose_chat_response_prompt_owns_conversation_and_action_rules():
    manager = PromptManager()

    template = manager.compose_product_prompt(
        "chat_response",
        context_view={"prompt_text": "User Context:\ntask management is disabled"},
    )

    assert template is not None
    content = template.content
    assert "Answer direct questions before redirecting" in content
    assert "ACTION BOUNDARIES (no false CRUD claims)" in content
    assert "I've created that task for you" in content
    assert "task management is disabled" in content
    assert "GOOD examples" not in content
    assert content.count("Answer direct questions before redirecting") == 1
