import copy

import pytest

from core.profile_v2_io import ensure_profile_envelope, schedule_categories
from core.profile_v2_schemas import (
    validate_account_v2_document,
    validate_preferences_v2_document,
)

pytestmark = [pytest.mark.core]


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
@pytest.mark.core
def test_validate_account_v2_normalizes_features_when_validation_fails(features, expected_checkins):
    bad_account = {
        "schema_version": 2,
        "updated_at": "2026-08-25 12:00:00",
        "internal_username": "tester",
        "features": features,
        "extra_field": "preserve",
    }

    normalized, errors = validate_account_v2_document(copy.deepcopy(bad_account))

    assert errors, "Validation errors should be reported when required fields are missing"
    assert normalized == bad_account


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.core
def test_validate_preferences_v2_reports_errors_and_returns_original(monkeypatch):
    monkeypatch.setattr("messages.message_data_manager.get_message_categories", lambda: ["allowed"])
    data = {
        "schema_version": 2,
        "updated_at": "2026-08-25 12:00:00",
        "categories": ["invalid"],
        "channel": {"type": "email", "contact": "user@example.com"},
        "checkin_settings": None,
        "extra": "keep",
    }

    normalized, errors = validate_preferences_v2_document(copy.deepcopy(data))

    assert errors, "Invalid categories should surface as validation errors"
    assert normalized == data, "On validation failure the original payload should be returned"


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.core
def test_ensure_profile_envelope_migrates_flat_schedule_compatibility_shape():
    compatibility_shape = {
        "general": {
            "morning": {
                "days": ["Funday", "ALL"],
                "start_time": "99:00",
                "end_time": "not-a-time",
            }
        }
    }

    normalized = ensure_profile_envelope("schedules", compatibility_shape)
    categories = schedule_categories(normalized)

    assert set(categories.keys()) == {"general"}
    periods = categories["general"]["periods"]
    assert set(periods.keys()) == {"morning"}
    assert periods["morning"]["days"] == ["ALL"]
    assert periods["morning"]["start_time"] == "00:00"
    assert periods["morning"]["end_time"] == "00:00"


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.core
def test_schedule_categories_reads_categories_map_without_schema_version():
    payload = {
        "categories": {
            "motivational": {
                "periods": {
                    "Evening": {
                        "active": True,
                        "days": ["ALL"],
                        "start_time": "18:00",
                        "end_time": "21:00",
                    }
                }
            }
        }
    }
    categories = schedule_categories(payload)
    assert categories["motivational"]["periods"]["Evening"]["start_time"] == "18:00"


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.core
def test_schedule_categories_reads_envelope_with_extra_keys():
    payload = {
        "schema_version": 2,
        "updated_at": "2026-08-26 12:00:00",
        "categories": {
            "motivational": {
                "periods": {
                    "Evening": {
                        "active": True,
                        "days": ["ALL"],
                        "start_time": "18:00",
                        "end_time": "21:00",
                    }
                }
            }
        },
        "_metadata": {"file_path": "schedules.json"},
    }
    categories = schedule_categories(payload)
    assert categories["motivational"]["periods"]["Evening"]["end_time"] == "21:00"
