import copy

import pytest

from core.schemas import (
    validate_account_dict,
    validate_preferences_dict,
    validate_schedules_dict,
    validate_messages_file_dict,
)


@pytest.fixture()
def base_account_data():
    return {
        "user_id": "user-123",
        "internal_username": "tester",
        "email": "not-an-email",
        "features": {
            "automated_messages": True,
            "checkins": "yes",
            "task_management": "no",
        },
    }


@pytest.mark.unit
def test_validate_account_dict_coerces_features_and_normalizes_email(base_account_data):
    normalized, errors = validate_account_dict(base_account_data)

    assert errors == []
    assert normalized["email"] == ""
    assert normalized["features"] == {
        "automated_messages": "enabled",
        "checkins": "enabled",
        "task_management": "disabled",
    }


@pytest.mark.unit
def test_validate_account_dict_reports_errors_when_required_fields_missing(base_account_data):
    incomplete = copy.deepcopy(base_account_data)
    incomplete.pop("user_id")

    normalized, errors = validate_account_dict(incomplete)

    assert errors, "Expected validation errors for missing required fields"
    assert normalized["features"]["automated_messages"] == "enabled"
    assert normalized["features"]["checkins"] == "enabled"
    assert normalized["features"]["task_management"] == "disabled"


@pytest.mark.unit
def test_validate_preferences_dict_retains_original_on_error():
    # Invalid category should trigger a validation error and return original payload
    prefs = {
        "categories": ["unknown_category"],
        "channel": {"type": "email", "contact": "user@example.com"},
        "checkin_settings": None,
    }

    normalized, errors = validate_preferences_dict(prefs)

    assert errors
    assert normalized == prefs


@pytest.mark.unit
def test_validate_schedules_dict_normalizes_days_and_times():
    schedules = {
        "motivational": {
            "periods": {
                "morning": {
                    "active": True,
                    "days": ["Monday", "Funday"],
                    "start_time": "25:00",  # invalid
                    "end_time": "06:30",
                },
                "evening": {
                    "active": False,
                    "days": [],
                    "start_time": "18:30",
                    "end_time": "not-a-time",
                },
            }
        }
    }

    normalized, errors = validate_schedules_dict(schedules)

    assert errors == []
    periods = normalized["motivational"]["periods"]
    assert periods["morning"]["days"] == ["Monday"]
    assert periods["morning"]["start_time"] == "00:00"
    assert periods["evening"]["days"] == ["ALL"]
    assert periods["evening"]["end_time"] == "00:00"


@pytest.mark.unit
def test_validate_messages_file_dict_filters_invalid_entries():
    data = {
        "messages": [
            {"message_id": "1", "message": "Hello!", "days": [], "time_periods": []},
            {"message": "Missing id"},
            "not-a-dict",
        ]
    }

    normalized, errors = validate_messages_file_dict(data)

    assert errors
    assert normalized["messages"] == [
        {"message_id": "1", "message": "Hello!", "days": ["ALL"], "time_periods": ["ALL"], "timestamp": None}
    ]
