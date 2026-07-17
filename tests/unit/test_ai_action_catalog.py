"""Tests for the product-AI action catalog."""

from __future__ import annotations

import pytest

from ai.prompts.action_catalog import (
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

    append_note = catalog.get("append_note_to_task")
    assert append_note is not None
    assert append_note.required_fields == ["task_identifier", "note_text"]


@pytest.mark.parametrize(
    ("action_name", "domain", "handler_name", "features", "required_fields"),
    [
        ("start_checkin", "checkins", "CheckinHandler", ["checkins"], []),
        (
            "checkin_history",
            "checkins",
            "AnalyticsHandler",
            ["checkins"],
            [],
        ),
        (
            "update_schedule",
            "schedules",
            "ScheduleManagementHandler",
            ["automated_messages"],
            ["action", "category"],
        ),
        ("show_profile", "profile", "ProfileHandler", [], []),
        (
            "create_note",
            "notebooks",
            "NotebookHandler",
            ["notebook"],
            [],
        ),
        (
            "search_entries",
            "notebooks",
            "NotebookHandler",
            ["notebook"],
            ["query"],
        ),
        (
            "remove_list_item",
            "notebooks",
            "NotebookHandler",
            ["notebook"],
            ["entry_ref", "item_index"],
        ),
        ("help", "help", "HelpHandler", [], []),
        (
            "messages",
            "help",
            "HelpHandler",
            ["automated_messages"],
            [],
        ),
        (
            "mood_trends",
            "analytics",
            "AnalyticsHandler",
            ["checkins"],
            [],
        ),
        (
            "connect_google_health",
            "health",
            "HealthHandler",
            ["google_health"],
            [],
        ),
        (
            "update_natural_language_defaults",
            "preferences",
            "NaturalLanguageHandler",
            [],
            ["nl_field", "nl_value"],
        ),
        ("show_create_hub", "tasks", "CreateMenuHandler", ["task_management"], []),
    ],
)
def test_action_catalog_non_task_domain_metadata(
    action_name,
    domain,
    handler_name,
    features,
    required_fields,
):
    catalog = build_action_catalog()
    action = catalog.get(action_name)
    assert action is not None, f"missing catalog entry for {action_name}"
    assert action.domain == domain
    assert action.handler_name == handler_name
    assert action.feature_requirements == features
    assert action.required_fields == required_fields


def test_action_catalog_delete_actions_require_confirmation():
    catalog = build_action_catalog()

    for action_name in ("delete_task", "remove_list_item", "delete_google_health_data"):
        action = catalog.get(action_name)
        assert action is not None
        assert action.requires_confirmation is True


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


def test_action_catalog_planning_prompt_summary_is_compact():
    catalog = build_action_catalog()
    summary = catalog.to_planning_prompt_summary()
    verbose = catalog.to_prompt_summary()

    assert "create_task" in summary
    assert "list_tasks" in summary
    assert "(tasks; required:" not in summary
    assert "create_task:title" not in summary
    assert summary.index("create_task") < summary.index("add_list_item")
    assert len(summary) < len(verbose)
    assert len(summary) < 2000
