"""Unit tests for per-user task natural-language defaults."""

from datetime import datetime
from unittest.mock import patch

import pytest

from tasks.task_natural_language_defaults import (
    TaskNaturalLanguageDefaults,
    get_task_natural_language_defaults,
    is_past_time_of_day,
)
from tasks import task_service


@pytest.mark.unit
@pytest.mark.tasks
def test_builtin_defaults_match_shipped_behavior():
    defaults = TaskNaturalLanguageDefaults.builtin()
    assert defaults.tonight_start_time == "18:00"
    assert defaults.after_work_school_time == "17:00"
    assert defaults.time_of_day_defaults["morning"] == "9:00"
    assert defaults.weekend_this_week_means_coming_week is True


@pytest.mark.unit
@pytest.mark.tasks
def test_from_preferences_merges_overrides():
    defaults = TaskNaturalLanguageDefaults.from_preferences(
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
@pytest.mark.tasks
def test_get_task_natural_language_defaults_reads_preferences():
    prefs = {
        "preferences": {
            "task_settings": {
                "natural_language_defaults": {
                    "tonight_start_time": "21:00",
                    "after_work_school_time": "18:30",
                }
            }
        }
    }
    with patch("tasks.task_natural_language_defaults.get_user_data", return_value=prefs):
        defaults = get_task_natural_language_defaults("user-1")

    assert defaults.tonight_start_time == "21:00"
    assert defaults.after_work_school_time == "18:30"


@pytest.mark.unit
@pytest.mark.tasks
def test_parse_relative_date_uses_custom_after_work_cutoff():
    custom = TaskNaturalLanguageDefaults.from_preferences(
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
    custom = TaskNaturalLanguageDefaults.from_preferences(
        {"weekend_this_week_means_coming_week": False}
    )
    saturday = datetime(2026, 5, 16, 10, 0)
    with patch("tasks.task_service.now_datetime_full", return_value=saturday):
        assert (
            task_service.parse_relative_date("this week", nl_defaults=custom)
            == "2026-05-17"
        )


@pytest.mark.unit
@pytest.mark.tasks
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
            "task_settings": {
                "natural_language_defaults": {
                    "tonight_start_time": "20:00",
                    "after_work_school_time": "16:30",
                    "time_of_day_defaults": {"morning": "8:00"},
                }
            }
        }
    }
    with patch(
        "tasks.task_natural_language_defaults.get_user_data", return_value=prefs
    ):
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
