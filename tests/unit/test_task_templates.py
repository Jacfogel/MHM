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
def test_template_form_defaults_prefills_medication_fields():
    from tasks.task_templates import template_form_defaults

    defaults = template_form_defaults("meds")
    assert defaults is not None
    assert defaults["template_id"] == "medication"
    assert defaults["title"] == "Take medication"
    assert defaults["due"] == "today"
    assert "medication" in defaults["tags"]
    assert defaults["modal_title"].startswith("Create:")
    assert template_form_defaults("unknown-thing") is None


@pytest.mark.unit
@pytest.mark.tasks
def test_template_form_defaults_prefills_call_and_clean_fields():
    from tasks.task_templates import template_form_defaults

    call_defaults = template_form_defaults("call")
    assert call_defaults is not None
    assert call_defaults["template_id"] == "phone_call"
    assert call_defaults["title"] == "Call"
    assert call_defaults["due"] == "this week"
    assert "phone" in call_defaults["tags"]

    clean_defaults = template_form_defaults("clean")
    assert clean_defaults is not None
    assert clean_defaults["template_id"] == "cleaning"
    assert clean_defaults["title"] == "Clean"
    assert clean_defaults["due"] == "this week"
    assert "chores" in clean_defaults["tags"]


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
def test_build_task_data_from_template_parses_due_phrase_override():
    from tasks import task_service

    fixed_now = datetime(2026, 5, 27, 10, 0)
    with patch("tasks.task_service.now_datetime_full", return_value=fixed_now):
        data = task_service.build_task_data_from_template(
            "user-1",
            "phone_call",
            title="Call dentist",
            due_date="tomorrow at 2pm",
        )

    assert data is not None
    assert data["due_date"] == "2026-05-28"
    assert data["due_time"] == "14:00"


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
def test_custom_task_templates_are_normalized_and_found_by_readable_reference():
    from tasks.task_templates import (
        get_custom_template,
        normalize_custom_task_templates,
    )

    saved = {
        "custom_abc123": {
            "display_name": "Morning routine",
            "title": "Start morning routine",
            "description": "Begin with water.",
            "priority": "high",
            "tags": ["Routine", "morning", "ROUTINE"],
            "default_due_time": "08:30",
            "recurrence_pattern": "daily",
            "recurrence_interval": 1,
        }
    }

    normalized = normalize_custom_task_templates(saved, strict=True)
    assert normalized["custom_abc123"]["tags"] == ["routine", "morning"]
    template = get_custom_template(normalized, "morning_routine")
    assert template is not None
    assert template.template_id == "custom_abc123"
    assert template.default_due_time == "08:30"


@pytest.mark.unit
@pytest.mark.tasks
@pytest.mark.parametrize(
    "field,bad",
    [
        ("display_name", "Medication"),
        ("priority", "eventually"),
        ("default_due_time", "25:00"),
        ("recurrence_interval", 0),
    ],
)
def test_custom_task_template_validation_rejects_unsafe_values(field, bad):
    from core.error_handling import ValidationError
    from tasks.task_templates import normalize_custom_task_templates

    record = {
        "display_name": "Morning routine",
        "title": "Start morning routine",
        "description": "",
        "priority": "medium",
        "tags": [],
        "default_due_time": None,
        "recurrence_pattern": None,
        "recurrence_interval": 1,
    }
    record[field] = bad
    with pytest.raises(ValidationError):
        normalize_custom_task_templates({"custom_abc123": record}, strict=True)


@pytest.mark.unit
@pytest.mark.tasks
def test_task_service_uses_account_owned_custom_template():
    from tasks import task_service

    saved = {
        "custom_abc123": {
            "display_name": "Morning routine",
            "title": "Start morning routine",
            "description": "Begin with water.",
            "priority": "high",
            "tags": ["routine"],
            "default_due_time": "08:30",
            "recurrence_pattern": "daily",
            "recurrence_interval": 1,
        }
    }
    preferences = {
        "preferences": {"task_settings": {"custom_templates": saved}}
    }
    fixed_now = datetime(2026, 5, 27, 7, 0)
    with (
        patch("tasks.task_service.get_user_data", return_value=preferences),
        patch("tasks.task_service.now_datetime_full", return_value=fixed_now),
    ):
        templates = task_service.list_task_templates("user-1")
        data = task_service.build_task_data_from_template(
            "user-1", "morning_routine"
        )
        help_text = task_service.get_task_templates_help_text("user-1")

    assert templates[-1].display_name == "Morning routine"
    assert data is not None
    assert data["title"] == "Start morning routine"
    assert data["due_time"] == "08:30"
    assert data["recurrence_pattern"] == "daily"
    assert "`morning_routine` — Morning routine" in help_text


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
