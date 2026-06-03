"""Unit tests for profile/tags/chat v2 envelopes and I/O bridging."""

from __future__ import annotations

import pytest

from core.profile_v2_io import (
    prepare_profile_raw_on_load,
    wrap_profile_document_for_save,
)
from storage import user_data_v2_envelopes as envelopes


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
def test_schedules_v2_save_migrates_flat_periods(monkeypatch):
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
    monkeypatch.setenv("PROFILE_V2_WRITE", "true")
    from importlib import reload
    import core.config as config_module

    reload(config_module)
    wrapped = wrap_profile_document_for_save("schedules", legacy_inner)
    assert wrapped.get("schema_version") == 2
    motivational = wrapped["categories"]["motivational"]
    assert "periods" in motivational
    assert "ALL" in motivational["periods"]


@pytest.mark.unit
@pytest.mark.storage
def test_schedules_v2_categories_wrapper_round_trip(monkeypatch):
    legacy = {
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
    inner = prepare_profile_raw_on_load("schedules", legacy)
    assert "motivational" in inner

    monkeypatch.setenv("PROFILE_V2_WRITE", "true")
    from importlib import reload
    import core.config as config_module

    reload(config_module)
    wrapped = wrap_profile_document_for_save("schedules", inner)
    assert wrapped.get("schema_version") == 2
    assert "categories" in wrapped
    assert "motivational" in wrapped["categories"]
    unwrapped = prepare_profile_raw_on_load("schedules", wrapped)
    assert "motivational" in unwrapped


@pytest.mark.unit
@pytest.mark.storage
def test_chat_interactions_legacy_list_dual_read():
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
    assert isinstance(loaded, list)
    assert loaded[0]["user_message"] == "hi"


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

