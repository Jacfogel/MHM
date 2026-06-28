"""Unit tests for per-user natural-language phrase defaults."""

from datetime import datetime
from unittest.mock import patch

import pytest

from core.natural_language_defaults import (
    NaturalLanguageDefaults,
    apply_natural_language_defaults_update,
    format_natural_language_defaults_message,
    get_natural_language_defaults,
    is_past_time_of_day,
)
from tasks import task_service


@pytest.mark.unit
@pytest.mark.user
def test_builtin_defaults_load_from_resources_json():
    from pathlib import Path

    import json

    from core.natural_language_defaults import (
        _load_builtin_defaults_dict,
        build_builtin_natural_language_defaults,
    )

    resource_path = (
        Path(__file__).resolve().parents[2]
        / "resources"
        / "default_natural_language_defaults.json"
    )
    assert resource_path.is_file()
    with open(resource_path, encoding="utf-8") as handle:
        shipped = json.load(handle)

    loaded = _load_builtin_defaults_dict()
    defaults = build_builtin_natural_language_defaults()

    assert loaded["tonight_start_time"] == shipped["tonight_start_time"]
    assert defaults.tonight_start_time == shipped["tonight_start_time"]
    assert defaults.after_work_school_time == shipped["after_work_school_time"]
    assert defaults.time_of_day_defaults["morning"] == shipped["time_of_day_defaults"]["morning"]


@pytest.mark.unit
@pytest.mark.user
def test_builtin_defaults_match_shipped_behavior():
    defaults = NaturalLanguageDefaults.builtin()
    assert defaults.tonight_start_time == "18:00"
    assert defaults.after_work_school_time == "17:00"
    assert defaults.time_of_day_defaults["morning"] == "9:00"
    assert defaults.weekend_this_week_means_coming_week is True


@pytest.mark.unit
@pytest.mark.user
def test_from_preferences_merges_overrides():
    defaults = NaturalLanguageDefaults.from_preferences(
        {
            "tonight_start_time": "8:30pm",
            "after_work_school_time": "6pm",
            "time_of_day_defaults": {"evening": "7:00pm"},
            "weekend_this_week_means_coming_week": False,
        }
    )
    assert defaults.tonight_start_time == "20:30"
    assert defaults.after_work_school_time == "18:00"
    assert defaults.time_of_day_defaults["evening"] == "19:00"
    assert defaults.weekend_this_week_means_coming_week is False


@pytest.mark.unit
@pytest.mark.user
def test_get_natural_language_defaults_reads_canonical_preferences():
    prefs = {
        "preferences": {
            "natural_language_defaults": {
                "tonight_start_time": "21:00",
                "after_work_school_time": "18:30",
            }
        }
    }
    with patch("core.natural_language_defaults.get_user_data", return_value=prefs):
        defaults = get_natural_language_defaults("user-1")

    assert defaults.tonight_start_time == "21:00"
    assert defaults.after_work_school_time == "18:30"


@pytest.mark.unit
@pytest.mark.tasks
def test_parse_relative_date_uses_custom_after_work_cutoff():
    custom = NaturalLanguageDefaults.from_preferences(
        {"after_work_school_time": "19:00"}
    )
    before_cutoff = datetime(2026, 5, 11, 18, 0)
    after_cutoff = datetime(2026, 5, 11, 19, 30)

    with patch("tasks.task_service.now_datetime_full", return_value=before_cutoff):
        assert (
            task_service.parse_relative_date("after work", nl_defaults=custom)
            == "2026-05-11"
        )
    with patch("tasks.task_service.now_datetime_full", return_value=after_cutoff):
        assert (
            task_service.parse_relative_date("after school", nl_defaults=custom)
            == "2026-05-12"
        )


@pytest.mark.unit
@pytest.mark.tasks
def test_parse_relative_date_weekend_this_week_flag():
    custom = NaturalLanguageDefaults.from_preferences(
        {"weekend_this_week_means_coming_week": False}
    )
    saturday = datetime(2026, 5, 16, 10, 0)
    with patch("tasks.task_service.now_datetime_full", return_value=saturday):
        assert (
            task_service.parse_relative_date("this week", nl_defaults=custom)
            == "2026-05-17"
        )


@pytest.mark.unit
@pytest.mark.user
def test_is_past_time_of_day_compares_minutes():
    now_dt = datetime(2026, 5, 11, 17, 45)
    assert is_past_time_of_day(now_dt, "17:30") is True
    assert is_past_time_of_day(now_dt, "18:00") is False


@pytest.mark.unit
@pytest.mark.tasks
@pytest.mark.communication
def test_extract_task_entities_uses_user_preferences():
    from communication.message_processing.command_parser import EnhancedCommandParser

    command_parser = EnhancedCommandParser()
    prefs = {
        "preferences": {
            "natural_language_defaults": {
                "tonight_start_time": "20:00",
                "after_work_school_time": "16:30",
                "time_of_day_defaults": {"morning": "8:00"},
            }
        }
    }
    with patch("core.natural_language_defaults.get_user_data", return_value=prefs):
        tonight = command_parser._extract_task_entities(
            "buy milk tonight", user_id="user-1"
        )
        after_work = command_parser._extract_task_entities(
            "call dentist after work", user_id="user-1"
        )
        morning = command_parser._extract_task_entities(
            "submit forms tomorrow morning", user_id="user-1"
        )

    assert tonight.get("due_time") == "20:00"
    assert after_work.get("due_time") == "16:30"
    assert morning.get("due_time") == "08:00"


@pytest.mark.unit
@pytest.mark.user
def test_format_natural_language_defaults_message_includes_values():
    defaults = NaturalLanguageDefaults.from_preferences(
        {
            "tonight_start_time": "20:00",
            "after_work_school_time": "18:00",
            "time_of_day_defaults": {"morning": "8:00"},
            "weekend_this_week_means_coming_week": False,
        }
    )
    message = format_natural_language_defaults_message(defaults)
    assert "20:00" in message
    assert "18:00" in message
    assert "current week" in message


@pytest.mark.unit
@pytest.mark.user
def test_apply_natural_language_defaults_update_saves_canonical_path():
    prefs = {
        "preferences": {
            "natural_language_defaults": {"tonight_start_time": "18:00"},
        }
    }
    saved: dict = {}

    def _fake_save(user_id: str, updates: dict) -> bool:
        saved["user_id"] = user_id
        saved["updates"] = updates
        return True

    with patch("core.natural_language_defaults.get_user_data", return_value=prefs):
        result = apply_natural_language_defaults_update(
            "user-1",
            "tonight",
            "8pm",
            save_preferences=_fake_save,
        )

    assert result.success is True
    assert saved["updates"]["natural_language_defaults"]["tonight_start_time"] == "20:00"


@pytest.mark.unit
@pytest.mark.user
def test_apply_natural_language_defaults_update_rejects_invalid_time():
    with patch("core.natural_language_defaults.get_user_data", return_value={}):
        result = apply_natural_language_defaults_update(
            "user-1", "tonight", "not-a-time"
        )

    assert result.success is False


@pytest.mark.unit
@pytest.mark.communication
@pytest.mark.user
def test_command_parser_show_phrase_settings_intent():
    from communication.message_processing.command_parser import parse_command

    result = parse_command("show phrase settings")
    assert result is not None
    assert result.parsed_command.intent == "show_natural_language_defaults"

    legacy = parse_command("show task language settings")
    assert legacy is not None
    assert legacy.parsed_command.intent == "show_natural_language_defaults"


@pytest.mark.unit
@pytest.mark.communication
@pytest.mark.user
def test_command_parser_update_phrase_settings_entities():
    from communication.message_processing.command_parser import parse_command

    result = parse_command("set tonight to 8pm")
    assert result is not None
    assert result.parsed_command.intent == "update_natural_language_defaults"
    assert result.parsed_command.entities.get("nl_field") == "tonight"
    assert result.parsed_command.entities.get("nl_value") == "8pm"

    morning = parse_command("set morning to 8:30am")
    assert morning is not None
    assert morning.parsed_command.intent == "update_natural_language_defaults"
    assert morning.parsed_command.entities.get("nl_field") == "morning"
    assert morning.parsed_command.entities.get("nl_value") == "8:30am"
