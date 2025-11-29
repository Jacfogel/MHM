import copy

import pytest

from core.schemas import (
    validate_account_dict,
    validate_messages_file_dict,
    validate_preferences_dict,
    validate_schedules_dict,
)


@pytest.mark.unit
@pytest.mark.smoke
@pytest.mark.regression
@pytest.mark.parametrize(
    "features,expected_checkins",
    [
        ({"automated_messages": True, "checkins": "yes", "task_management": 0}, "enabled"),
        ({"automated_messages": "enabled", "checkins": "no", "task_management": False}, "disabled"),
    ],
)
def test_validate_account_dict_normalizes_features_when_validation_fails(features, expected_checkins):
    bad_account = {
        # Missing required user_id triggers validation error path
        "internal_username": "tester",
        "features": features,
        "extra_field": "preserve",
    }

    normalized, errors = validate_account_dict(copy.deepcopy(bad_account))

    assert errors, "Validation errors should be reported when required fields are missing"
    assert normalized["features"] == {
        "automated_messages": "enabled",
        "checkins": expected_checkins,
        "task_management": "disabled",
    }
    assert normalized.get("extra_field") == "preserve"


@pytest.mark.unit
@pytest.mark.regression
def test_validate_preferences_dict_reports_errors_and_returns_original(monkeypatch):
    monkeypatch.setattr("core.message_management.get_message_categories", lambda: ["allowed"])
    data = {
        "categories": ["invalid"],
        "channel": {"type": "email", "contact": "user@example.com"},
        "checkin_settings": None,
        "extra": "keep",
    }

    normalized, errors = validate_preferences_dict(copy.deepcopy(data))

    assert errors, "Invalid categories should surface as validation errors"
    assert normalized == data, "On validation failure the original payload should be returned"


@pytest.mark.unit
@pytest.mark.regression
def test_validate_schedules_dict_normalizes_legacy_shape_and_invalid_fields():
    legacy_shape = {
        "general": {
            "morning": {
                "days": ["Funday", "ALL"],
                "start_time": "99:00",
                "end_time": "not-a-time",
                "unexpected": "ignore",
            }
        }
    }

    normalized, errors = validate_schedules_dict(legacy_shape)

    assert errors == []
    assert set(normalized.keys()) == {"general"}
    periods = normalized["general"]["periods"]
    assert set(periods.keys()) == {"morning"}
    assert periods["morning"] == {
        "active": True,
        "days": ["ALL"],
        "start_time": "00:00",
        "end_time": "00:00",
    }


@pytest.mark.unit
@pytest.mark.regression
def test_validate_messages_file_dict_best_effort_normalization_with_bad_rows():
    payload = {
        "messages": [
            {
                "message_id": "1",
                "message": "hey",
                "days": [],
                "time_periods": [],
                "extra": "drop",
            },
            {
                "message_id": "2",
                "message": "bye",
                "days": ["Funday"],
                "time_periods": ["morning"],
            },
            {"message_id": "3"},
            "bad-entry",
        ]
    }

    normalized, errors = validate_messages_file_dict(payload)

    assert errors, "Mixed-quality payloads should report validation issues"
    assert normalized["messages"] == [
        {
            "message_id": "1",
            "message": "hey",
            "days": ["ALL"],
            "time_periods": ["ALL"],
            "timestamp": None,
        },
        {
            "message_id": "2",
            "message": "bye",
            "days": ["Funday"],
            "time_periods": ["morning"],
            "timestamp": None,
        },
    ]
