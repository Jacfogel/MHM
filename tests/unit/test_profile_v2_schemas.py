"""Unit tests for profile/tags/chat v2 envelopes and I/O bridging."""

from __future__ import annotations

import pytest

from core.profile_v2_io import (
    ensure_profile_envelope,
    prepare_profile_raw_on_load,
    schedule_categories,
    wrap_chat_interactions_for_save,
    wrap_profile_document_for_save,
)
from storage import user_data_v2_envelopes as envelopes
from storage.user_data_v2_base import SCHEMA_VERSION


@pytest.mark.unit
@pytest.mark.storage
def test_validate_v2_document_account_integration():
    payload = {
        "schema_version": 2,
        "updated_at": "2026-06-01 12:00:00",
        "user_id": "user-1",
        "features": {
            "automated_messages": "disabled",
            "checkins": "disabled",
            "task_management": "disabled",
        },
    }
    data, errors = envelopes.validate_v2_document("account", payload)
    assert errors == []
    assert data["schema_version"] == 2
    assert data["user_id"] == "user-1"


@pytest.mark.unit
@pytest.mark.storage
def test_schedules_v2_save_migrates_flat_periods():
    """Flat in-memory period maps normalize to categories->periods on v2 save."""
    legacy_inner = {
        "motivational": {
            "ALL": {
                "active": True,
                "days": ["ALL"],
                "start_time": "00:00",
                "end_time": "23:59",
            }
        }
    }
    wrapped = wrap_profile_document_for_save("schedules", legacy_inner)
    assert wrapped.get("schema_version") == 2
    motivational = wrapped["categories"]["motivational"]
    assert "periods" in motivational
    assert "ALL" in motivational["periods"]


@pytest.mark.unit
@pytest.mark.storage
def test_schedules_v2_categories_wrapper_round_trip():
    inner = {
        "motivational": {
            "periods": {
                "ALL": {
                    "active": True,
                    "days": ["ALL"],
                    "start_time": "00:00",
                    "end_time": "23:59",
                }
            }
        }
    }
    wrapped = wrap_profile_document_for_save("schedules", inner)
    assert wrapped.get("schema_version") == 2
    assert "categories" in wrapped
    assert "motivational" in wrapped["categories"]
    unwrapped = prepare_profile_raw_on_load("schedules", wrapped)
    assert unwrapped.get("schema_version") == 2
    assert "motivational" in unwrapped["categories"]


@pytest.mark.unit
@pytest.mark.storage
def test_chat_interactions_non_v2_on_disk_returns_empty():
    legacy = [
        {
            "user_message": "hi",
            "ai_response": "hello",
            "context_used": False,
            "timestamp": "2026-06-01 12:00:00",
            "message_length": 2,
            "response_length": 5,
        }
    ]
    loaded = prepare_profile_raw_on_load("chat_interactions", legacy)
    assert loaded == []


@pytest.mark.unit
@pytest.mark.storage
def test_chat_interactions_v2_envelope_unwrap():
    envelope = {
        "schema_version": 2,
        "updated_at": "2026-06-01 12:00:00",
        "interactions": [
            {
                "user_message": "a",
                "ai_response": "b",
                "context_used": True,
                "timestamp": "2026-06-01 12:00:00",
                "message_length": 1,
                "response_length": 1,
            }
        ],
    }
    loaded = prepare_profile_raw_on_load("chat_interactions", envelope)
    assert isinstance(loaded, list)
    assert len(loaded) == 1
    first = loaded[0]
    assert isinstance(first, dict)
    assert first["ai_response"] == "b"


@pytest.mark.unit
@pytest.mark.storage
def test_chat_interactions_save_always_v2_envelope():
    interactions = [
        {
            "user_message": "hi",
            "ai_response": "hello",
            "context_used": False,
            "timestamp": "2026-06-01 12:00:00",
            "message_length": 2,
            "response_length": 5,
        }
    ]
    wrapped = wrap_chat_interactions_for_save(interactions)
    assert wrapped.get("schema_version") == SCHEMA_VERSION
    assert isinstance(wrapped.get("interactions"), list)


@pytest.mark.unit
@pytest.mark.storage
@pytest.mark.parametrize(
    ("document_type", "validator_name"),
    [
        ("account", "validate_account_v2_document"),
        ("preferences", "validate_preferences_v2_document"),
        ("schedules", "validate_schedules_v2_document"),
        ("context", "validate_context_v2_document"),
        ("tags", "validate_tags_v2_document"),
        ("chat_interactions", "validate_chat_interactions_v2_document"),
    ],
)
def test_validate_v2_document_dispatches_profile_types(
    monkeypatch, document_type, validator_name
):
    payload = {"schema_version": 2}
    calls: list[dict] = []

    def fake_validator(data):
        calls.append(data)
        return {"normalized": True}, []

    monkeypatch.setattr(envelopes, validator_name, fake_validator)
    data, errors = envelopes.validate_v2_document(document_type, payload)
    assert calls == [payload]
    assert data == {"normalized": True}
    assert errors == []


@pytest.mark.unit
@pytest.mark.storage
def test_context_in_memory_extra_keys_normalize_on_save():
    """In-memory context with stray keys normalizes into strict v2 on save."""
    inner = {
        "preferred_name": "Julie",
        "pronouns": [],
        "date_of_birth": "1990-03-09",
        "custom_fields": {
            "health_conditions": ["ADHD"],
            "medications_treatments": ["Antidepressants"],
            "reminders_needed": [],
            "allergies_sensitivities": ["Cats"],
        },
        "interests": ["Programming"],
        "goals": ["Mental Health"],
        "loved_ones": [],
        "activities_for_encouragement": [],
        "notes_for_ai": [],
        "created_at": "2025-07-07 01:03:35",
        "last_updated": "2025-10-15T19:53:55.986831",
        "reminders_needed": ["Take medication"],
        "user_id": "user-stray-1",
        "timezone": "America/Regina",
    }
    wrapped = wrap_profile_document_for_save("context", inner)
    assert wrapped.get("schema_version") == 2
    assert wrapped.get("pronouns") == []
    assert "user_id" not in wrapped
    assert wrapped["updated_at"] == "2025-10-15 19:53:55"
    assert wrapped["custom_fields"]["reminders_needed"] == ["Take medication"]
    _, errors = envelopes.validate_v2_document("context", wrapped)
    assert errors == []

    loaded = prepare_profile_raw_on_load("context", wrapped)
    assert loaded["preferred_name"] == "Julie"
    assert loaded.get("user_id") is None


@pytest.mark.unit
@pytest.mark.storage
def test_tags_non_v2_on_disk_returns_empty():
    loaded = prepare_profile_raw_on_load("tags", ["health", "home", "family"])
    assert loaded == {"tags": [], "metadata": {}}


@pytest.mark.unit
@pytest.mark.storage
def test_tags_v2_envelope_round_trip():
    envelope = {
        "schema_version": 2,
        "updated_at": "2026-06-01 12:00:00",
        "tags": ["health", "home", "family"],
        "metadata": {"updated_at": "2026-06-01 12:00:00"},
    }
    loaded = prepare_profile_raw_on_load("tags", envelope)
    assert loaded["tags"] == ["health", "home", "family"]
    wrapped = wrap_profile_document_for_save("tags", loaded)
    assert wrapped.get("schema_version") == 2


@pytest.mark.unit
@pytest.mark.storage
def test_wrap_schedules_envelope_is_idempotent():
    inner = {
        "motivational": {
            "periods": {
                "ALL": {
                    "active": True,
                    "days": ["ALL"],
                    "start_time": "00:00",
                    "end_time": "23:59",
                }
            }
        }
    }
    wrapped = wrap_profile_document_for_save("schedules", inner)
    again = wrap_profile_document_for_save("schedules", wrapped)
    assert again.get("schema_version") == 2
    assert "motivational" in again["categories"]
    assert "ALL" in again["categories"]["motivational"]["periods"]


@pytest.mark.unit
@pytest.mark.storage
def test_schedule_categories_accepts_envelope_and_flat_map():
    flat = {
        "motivational": {
            "periods": {
                "ALL": {
                    "active": True,
                    "days": ["ALL"],
                    "start_time": "00:00",
                    "end_time": "23:59",
                }
            }
        }
    }
    envelope = ensure_profile_envelope("schedules", flat)
    assert schedule_categories(flat)["motivational"]["periods"]["ALL"]["start_time"] == "00:00"
    assert schedule_categories(envelope)["motivational"]["periods"]["ALL"]["start_time"] == "00:00"
    schedule_categories(envelope)["motivational"]["periods"]["evening"] = {
        "active": True,
        "days": ["Monday"],
        "start_time": "18:00",
        "end_time": "21:00",
    }
    assert "evening" in envelope["categories"]["motivational"]["periods"]


@pytest.mark.unit
@pytest.mark.storage
def test_account_extra_reads_metadata_overflow():
    from core.profile_v2_io import account_extra

    inner = {
        "user_id": "user-1",
        "internal_username": "user-1",
        "timezone": "UTC",
        "created_at": "2024-01-01 00:00:00",
        "features": {"automated_messages": "enabled"},
        "enabled_features": ["messages", "tasks"],
    }
    wrapped = wrap_profile_document_for_save("account", inner)
    assert wrapped.get("schema_version") == 2
    assert "enabled_features" not in wrapped
    assert wrapped["metadata"]["enabled_features"] == ["messages", "tasks"]
    loaded = prepare_profile_raw_on_load("account", wrapped)
    assert account_extra(loaded, "enabled_features") == ["messages", "tasks"]


@pytest.mark.unit
@pytest.mark.storage
def test_preferences_natural_language_defaults_survive_wrap_and_load():
    inner = {
        "categories": ["motivational"],
        "channel": {"type": "email", "contact": "user@example.com"},
        "natural_language_defaults": {
            "tonight_start_time": "20:00",
            "after_work_school_time": "17:00",
            "time_of_day_defaults": {"morning": "09:00"},
            "weekend_this_week_means_coming_week": True,
        },
    }
    wrapped = wrap_profile_document_for_save("preferences", inner)
    assert wrapped.get("schema_version") == 2
    assert wrapped["natural_language_defaults"]["tonight_start_time"] == "20:00"
    loaded = prepare_profile_raw_on_load("preferences", wrapped)
    assert loaded["natural_language_defaults"]["tonight_start_time"] == "20:00"
    _, errors = envelopes.validate_v2_document("preferences", wrapped)
    assert errors == []

