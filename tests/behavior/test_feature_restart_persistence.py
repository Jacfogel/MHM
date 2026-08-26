"""Restart/persistence leftovers from the project-wide manual testing guide."""

from __future__ import annotations

import uuid

import pytest

from checkins.checkin_data_manager import get_checkins_by_days, store_checkin_response
from core import clear_user_caches, get_user_data, update_user_preferences
from core.schedule_runtime import (
    clear_schedule_periods_cache,
    get_schedule_time_periods,
    set_schedule_periods,
)
from core.time_utilities import now_timestamp_full
from notebook.notebook_data_manager import create_note, get_entry
from tests.test_helpers.test_utilities import TestUserFactory


def _user(prefix: str, test_data_dir: str, **kwargs) -> str:
    internal = f"{prefix}_{uuid.uuid4().hex[:8]}"
    assert TestUserFactory.create_basic_user(
        internal, test_data_dir=test_data_dir, **kwargs
    )
    resolved = TestUserFactory.get_test_user_id_by_internal_username(
        internal, test_data_dir
    )
    assert resolved, f"Could not resolve created user {internal}"
    return resolved


@pytest.mark.behavior
@pytest.mark.storage
@pytest.mark.file_io
def test_schedule_survives_cache_clear_and_reload(test_data_dir):
    user_id = _user("restart_sched", test_data_dir)
    periods = {
        "Evening": {
            "start_time": "18:00",
            "end_time": "21:00",
            "active": True,
            "days": ["ALL"],
        }
    }
    assert set_schedule_periods(user_id, "motivational", periods) is True
    clear_schedule_periods_cache()
    clear_user_caches(user_id)
    reloaded = get_schedule_time_periods(user_id, "motivational")
    assert "Evening" in reloaded, f"expected Evening in {list(reloaded)}"
    assert reloaded["Evening"]["start_time"] == "18:00"
    assert reloaded["Evening"]["end_time"] == "21:00"


@pytest.mark.behavior
@pytest.mark.user
@pytest.mark.file_io
def test_preferences_channel_survives_new_loader(test_data_dir):
    user_id = _user("restart_prefs", test_data_dir)
    assert update_user_preferences(user_id, {"channel": {"type": "email"}}) is True
    clear_user_caches(user_id)
    prefs = get_user_data(user_id, "preferences").get("preferences") or {}
    assert prefs.get("channel", {}).get("type") == "email"


@pytest.mark.behavior
@pytest.mark.checkins
@pytest.mark.file_io
def test_completed_checkin_survives_reload(test_data_dir):
    user_id = _user("restart_checkin", test_data_dir, enable_checkins=True)
    store_checkin_response(
        user_id,
        {
            "submitted_at": now_timestamp_full(),
            "responses": {"mood": "5", "energy": "ok"},
            "questions_asked": ["mood", "energy"],
        },
    )
    clear_user_caches(user_id)
    rows = get_checkins_by_days(user_id, days=7)
    assert any(
        (row.get("responses") or {}).get("mood") == "5"
        or row.get("mood") == "5"
        for row in rows
    )


@pytest.mark.behavior
@pytest.mark.notebook
@pytest.mark.file_io
def test_notebook_entry_survives_reload(test_data_dir):
    from notebook.notebook_data_handlers import load_entries
    from storage.user_data_v2_base import generate_short_id

    user_id = _user("restart_note", test_data_dir)
    entry = create_note(user_id, title="Restart note", description="keep me")
    assert entry is not None
    ref = entry.short_id or generate_short_id(str(entry.id), str(entry.kind), length=6)
    reloaded = get_entry(user_id, str(entry.id)) or get_entry(user_id, ref)
    if reloaded is None:
        matches = [item for item in load_entries(user_id) if item.title == "Restart note"]
        assert matches, f"Saved note was not in load_entries for {user_id}"
        reloaded = matches[0]
    assert reloaded.title == "Restart note"
    assert "keep me" in (reloaded.description or "")
