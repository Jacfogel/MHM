"""Unit tests for built-in task templates."""

from datetime import datetime
from unittest.mock import patch

import pytest


@pytest.mark.unit
@pytest.mark.tasks
def test_lookup_builtin_template_id_accepts_aliases():
    from tasks.task_templates import lookup_builtin_template_id

    assert lookup_builtin_template_id("medication") == "medication"
    assert lookup_builtin_template_id("meds") == "medication"
    assert lookup_builtin_template_id("phone call") == "phone_call"
    assert lookup_builtin_template_id("unknown-thing") is None


@pytest.mark.unit
@pytest.mark.tasks
def test_list_builtin_templates_returns_all_five():
    from tasks.task_templates import list_builtin_templates

    ids = [t.template_id for t in list_builtin_templates()]
    assert ids == ["medication", "appointment", "phone_call", "cleaning", "paperwork"]


@pytest.mark.unit
@pytest.mark.tasks
def test_build_task_data_from_template_merges_overrides():
    from tasks import task_service

    fixed_now = datetime(2026, 5, 27, 10, 0)
    with patch("tasks.task_service.now_datetime_full", return_value=fixed_now):
        data = task_service.build_task_data_from_template(
            "user-1",
            "phone_call",
            title="Call dentist",
            priority="urgent",
        )

    assert data is not None
    assert data["title"] == "Call dentist"
    assert data["priority"] == "urgent"
    assert "phone" in data["tags"]


@pytest.mark.unit
@pytest.mark.tasks
def test_build_task_data_from_template_applies_default_due():
    from tasks import task_service

    fixed_now = datetime(2026, 5, 27, 10, 0)  # Tuesday
    with patch("tasks.task_service.now_datetime_full", return_value=fixed_now):
        data = task_service.build_task_data_from_template("user-1", "appointment")

    assert data is not None
    assert data.get("due_date") is not None
    assert data["priority"] == "high"


@pytest.mark.unit
@pytest.mark.tasks
def test_create_task_from_template_delegates_to_create_task():
    from tasks import task_service

    with patch("tasks.task_service.create_task", return_value="tid-1") as mock_create:
        result = task_service.create_task_from_template("user-1", "cleaning")

    assert result == "tid-1"
    mock_create.assert_called_once()
    kwargs = mock_create.call_args.kwargs
    assert kwargs["user_id"] == "user-1"
    assert "chores" in kwargs.get("tags", [])


@pytest.mark.unit
@pytest.mark.tasks
def test_command_parser_task_template_intent():
    from communication.message_processing.command_parser import parse_command

    result = parse_command("task template medication")
    assert result is not None
    assert result.parsed_command.intent == "create_task_from_template"
    assert result.parsed_command.entities.get("template_ref") == "medication"


@pytest.mark.unit
@pytest.mark.tasks
def test_command_parser_list_task_templates_intent():
    from communication.message_processing.command_parser import parse_command

    result = parse_command("list task templates")
    assert result is not None
    assert result.parsed_command.intent == "list_task_templates"
