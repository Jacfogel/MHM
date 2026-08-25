import copy

import pytest

from core.profile_v2_io import ensure_profile_envelope, schedule_categories
from core.profile_v2_schemas import (
    validate_account_v2_document,
    validate_preferences_v2_document,
    validate_schedules_v2_document,
)

pytestmark = [pytest.mark.core]


@pytest.fixture()
def base_account_envelope():
    return {
        "schema_version": 2,
        "updated_at": "2026-08-25 12:00:00",
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
@pytest.mark.core
def test_validate_account_v2_coerces_features_and_normalizes_email(base_account_envelope):
    normalized, errors = validate_account_v2_document(base_account_envelope)

    assert errors == []
    assert normalized["email"] == ""
    assert normalized["features"] == {
        "automated_messages": "enabled",
        "checkins": "enabled",
        "task_management": "disabled",
        "google_health": "disabled",
    }


@pytest.mark.unit
@pytest.mark.core
def test_validate_account_v2_reports_errors_when_required_fields_missing(base_account_envelope):
    incomplete = copy.deepcopy(base_account_envelope)
    incomplete.pop("user_id")

    normalized, errors = validate_account_v2_document(incomplete)

    assert errors, "Expected validation errors for missing required fields"
    assert normalized == incomplete


@pytest.mark.unit
@pytest.mark.core
def test_validate_preferences_v2_retains_original_on_error():
    prefs = {
        "schema_version": 2,
        "updated_at": "2026-08-25 12:00:00",
        "categories": ["unknown_category"],
        "channel": {"type": "email", "contact": "user@example.com"},
        "checkin_settings": None,
    }

    normalized, errors = validate_preferences_v2_document(prefs)

    assert errors
    assert normalized == prefs


@pytest.mark.unit
@pytest.mark.core
def test_validate_schedules_v2_normalizes_days_and_times():
    envelope = ensure_profile_envelope(
        "schedules",
        {
            "motivational": {
                "periods": {
                    "morning": {
                        "active": True,
                        "days": ["Monday", "Funday"],
                        "start_time": "25:00",
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
        },
    )
    normalized, errors = validate_schedules_v2_document(envelope)

    assert errors == []
    periods = schedule_categories(normalized)["motivational"]["periods"]
    assert periods["morning"]["days"] == ["Monday"]
    assert periods["morning"]["start_time"] == "00:00"
    assert periods["evening"]["days"] == ["ALL"]
    assert periods["evening"]["end_time"] == "00:00"
