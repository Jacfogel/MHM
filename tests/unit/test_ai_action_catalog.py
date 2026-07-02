"""Tests for the product-AI action catalog."""

from __future__ import annotations

import pytest

from ai.action_catalog import (
    AIActionRequest,
    build_action_catalog,
)


pytestmark = [pytest.mark.unit, pytest.mark.ai]


def test_action_catalog_contains_handler_backed_task_actions():
    catalog = build_action_catalog()

    for action_name in (
        "create_task",
        "list_tasks",
        "complete_task",
        "delete_task",
        "update_task",
        "append_note_to_task",
    ):
        action = catalog.get(action_name)
        assert action is not None
        assert action.domain == "tasks"
        assert action.handler_name == "TaskManagementHandler"
        assert action.source == "structured_command_dispatcher"
        assert "task_management" in action.feature_requirements

    create_task = catalog.get("create_task")
    assert create_task is not None
    assert create_task.required_fields == ["title"]
    assert "message" in create_task.result_shape

    delete_task = catalog.get("delete_task")
    assert delete_task is not None
    assert delete_task.requires_confirmation is True


def test_action_request_is_ai_layer_planning_data_only():
    request = AIActionRequest(
        action_name="create_task",
        entities={"title": "Call pharmacy", "priority": "high"},
        confidence=0.92,
        source_message="Remind me to call the pharmacy.",
    )

    assert request.action_name == "create_task"
    assert request.entities["title"] == "Call pharmacy"
    assert request.confidence == 0.92
    assert request.requires_confirmation is False
