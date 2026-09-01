"""Unit tests for corrupt health JSON recovery."""

import json
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest

from integrations.google_health.data_handlers import (
    delete_user_health_data,
    ensure_health_directory,
    has_valid_auth,
    load_auth,
    load_daily_summaries,
    load_health_signals,
    load_sync_state,
    save_auth,
    save_daily_summaries,
    save_health_signals,
    save_sync_state,
)
from tests.test_helpers.test_utilities.test_user_factory import TestUserFactory

pytestmark = [pytest.mark.integrations]


@pytest.mark.unit
@pytest.mark.user
def test_corrupt_daily_summaries_returns_empty_document(test_data_dir):
    from pathlib import Path

    from core.config import get_user_data_dir

    user_id = "health-corrupt-user"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    health_dir = Path(get_user_data_dir(user_id)) / "health"
    health_dir.mkdir(parents=True, exist_ok=True)
    (health_dir / "daily_summaries.json").write_text("{not valid json", encoding="utf-8")

    doc = load_daily_summaries(user_id)
    assert doc is not None
    assert doc.get("schema_version") == 2
    assert doc.get("summaries") == []


@pytest.mark.unit
@pytest.mark.user
def test_schema_round_trip(test_data_dir):
    user_id = "health-roundtrip-user"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    payload = {
        "schema_version": 2,
        "updated_at": "2026-06-27 12:00:00",
        "summaries": [
            {
                "date": "2026-06-27",
                "sleep_duration_minutes": 420,
                "steps": 5000,
                "completeness": ["sleep", "activity"],
            }
        ],
    }
    assert save_daily_summaries(user_id, payload) is True
    loaded = load_daily_summaries(user_id)
    assert loaded["summaries"][0]["steps"] == 5000


@pytest.mark.unit
@pytest.mark.user
def test_invalid_user_id_returns_safe_defaults():
    assert ensure_health_directory("") is False
    assert load_auth("") is None
    assert save_auth("", {"access_token": "x"}) is False
    assert load_daily_summaries("") is None
    assert save_daily_summaries("", {"summaries": []}) is False
    assert load_health_signals("") is None
    assert save_health_signals("", {"signals": []}) is False
    assert load_sync_state("") is None
    assert save_sync_state("", {}) is False
    assert delete_user_health_data("") is False
    assert has_valid_auth("") is False


@pytest.mark.unit
@pytest.mark.user
def test_non_object_json_returns_empty_document(test_data_dir):
    from core.config import get_user_data_dir

    user_id = f"health-non-object-{uuid.uuid4().hex[:10]}"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    health_dir = Path(get_user_data_dir(user_id)) / "health"
    health_dir.mkdir(parents=True, exist_ok=True)
    (health_dir / "daily_summaries.json").write_text("[]", encoding="utf-8")

    doc = load_daily_summaries(user_id)
    assert doc is not None
    assert doc.get("schema_version") == 2
    assert doc.get("summaries") == []


@pytest.mark.unit
@pytest.mark.user
def test_invalid_schema_document_returns_empty_document(test_data_dir):
    from core.config import get_user_data_dir

    user_id = f"health-invalid-schema-{uuid.uuid4().hex[:10]}"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    health_dir = Path(get_user_data_dir(user_id)) / "health"
    health_dir.mkdir(parents=True, exist_ok=True)
    (health_dir / "sync_state.json").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "updated_at": "2026-01-01 00:00:00",
                "unknown_field": True,
            }
        ),
        encoding="utf-8",
    )

    state = load_sync_state(user_id)
    assert state is not None
    assert state.get("last_error") == ""
    assert "unknown_field" not in state


@pytest.mark.unit
@pytest.mark.user
def test_has_valid_auth_requires_a_token(test_data_dir):
    user_id = f"health-has-auth-{uuid.uuid4().hex[:10]}"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    ensure_health_directory(user_id)
    assert has_valid_auth(user_id) is False
    save_auth(
        user_id,
        {
            "schema_version": 2,
            "updated_at": "2026-06-28 12:00:00",
            "access_token": "token",
            "refresh_token": "",
        },
    )
    assert has_valid_auth(user_id) is True


@pytest.mark.unit
@pytest.mark.user
def test_health_document_round_trips(test_data_dir):
    user_id = f"health-docs-roundtrip-{uuid.uuid4().hex[:10]}"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    assert save_health_signals(
        user_id,
        {
            "schema_version": 2,
            "updated_at": "2026-06-28 12:00:00",
            "signals": [],
        },
    ) is True
    signals = load_health_signals(user_id)
    assert signals is not None
    assert signals.get("schema_version") == 2

    assert save_sync_state(
        user_id,
        {
            "schema_version": 2,
            "last_success_at": "2026-08-31 09:00:00",
            "last_error": "",
        },
    ) is True
    state = load_sync_state(user_id)
    assert state["last_success_at"] == "2026-08-31 09:00:00"


@pytest.mark.unit
@pytest.mark.user
def test_delete_user_health_data_removes_directory(test_data_dir):
    from core.config import get_user_data_dir

    user_id = f"health-delete-dir-{uuid.uuid4().hex[:10]}"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    ensure_health_directory(user_id)
    health_dir = Path(get_user_data_dir(user_id)) / "health"
    assert health_dir.exists()
    assert delete_user_health_data(user_id) is True
    assert health_dir.exists() is False
    assert delete_user_health_data(user_id) is True


@pytest.mark.unit
@pytest.mark.user
def test_delete_user_health_data_returns_false_on_oserror(test_data_dir):
    user_id = f"health-delete-oserror-{uuid.uuid4().hex[:10]}"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    ensure_health_directory(user_id)
    with patch(
        "integrations.google_health.data_handlers.shutil.rmtree",
        side_effect=OSError("locked"),
    ):
        assert delete_user_health_data(user_id) is False


@pytest.mark.unit
@pytest.mark.user
def test_load_auth_returns_none_when_document_load_fails(test_data_dir):
    user_id = f"health-load-none-{uuid.uuid4().hex[:10]}"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    with patch(
        "integrations.google_health.data_handlers._load_or_default",
        return_value=None,
    ):
        assert load_auth(user_id) is None


@pytest.mark.unit
@pytest.mark.user
def test_save_auth_returns_false_when_prepare_fails(test_data_dir):
    user_id = f"health-save-prepare-{uuid.uuid4().hex[:10]}"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    with patch(
        "integrations.google_health.data_handlers.prepare_auth_for_storage",
        return_value=None,
    ):
        assert save_auth(user_id, {"access_token": "token"}) is False


@pytest.mark.unit
@pytest.mark.user
def test_non_dict_loaded_json_returns_empty_document(test_data_dir):
    user_id = f"health-non-dict-load-{uuid.uuid4().hex[:10]}"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    with patch(
        "integrations.google_health.data_handlers.load_user_json_file",
        return_value=["not", "a", "dict"],
    ):
        doc = load_daily_summaries(user_id)
    assert doc is not None
    assert doc.get("summaries") == []
