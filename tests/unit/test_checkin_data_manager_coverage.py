"""Unit coverage for checkin_data_manager edge paths."""

from __future__ import annotations

import json

import pytest

from checkins.checkin_data_manager import (
    checkin_runtime_timestamp,
    get_checkins_by_days,
    get_recent_checkins,
    is_user_checkins_enabled,
    store_checkin_response,
)


@pytest.mark.unit
@pytest.mark.checkins
def test_checkin_runtime_timestamp_handles_non_dict_and_missing_submitted_at():
    assert checkin_runtime_timestamp(None) == ""
    assert checkin_runtime_timestamp("not-a-dict") == ""
    assert checkin_runtime_timestamp({}) == ""


@pytest.mark.unit
@pytest.mark.checkins
def test_get_recent_checkins_rejects_non_v2_envelope(tmp_path, monkeypatch):
    checkins_file = tmp_path / "checkins.json"
    checkins_file.write_text(json.dumps({"schema_version": 1, "checkins": []}), encoding="utf-8")
    monkeypatch.setattr(
        "checkins.checkin_data_manager.get_user_file_path",
        lambda _user_id, _file_type: str(checkins_file),
    )

    assert get_recent_checkins("user-1") == []


@pytest.mark.unit
@pytest.mark.checkins
def test_store_checkin_response_skips_invalid_envelope(tmp_path, monkeypatch):
    checkins_file = tmp_path / "checkins.json"
    checkins_file.write_text(json.dumps({"schema_version": 1}), encoding="utf-8")
    monkeypatch.setattr(
        "checkins.checkin_data_manager.get_user_file_path",
        lambda _user_id, _file_type: str(checkins_file),
    )

    store_checkin_response("user-1", {"mood": 4, "questions_asked": ["mood"]})

    assert json.loads(checkins_file.read_text(encoding="utf-8"))["schema_version"] == 1


@pytest.mark.unit
@pytest.mark.checkins
def test_get_checkins_by_days_filters_by_cutoff(tmp_path, monkeypatch):
    from datetime import datetime

    from core.time_utilities import format_timestamp, TIMESTAMP_FULL

    anchor = datetime(2026, 5, 11, 12, 0, 0)
    recent_ts = format_timestamp(anchor, TIMESTAMP_FULL)
    old_ts = format_timestamp(datetime(2020, 1, 1, 8, 0, 0), TIMESTAMP_FULL)

    checkins_file = tmp_path / "checkins.json"
    checkins_file.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "updated_at": recent_ts,
                "checkins": [
                    {
                        "id": "old",
                        "submitted_at": old_ts,
                        "responses": {"mood": 2},
                        "questions_asked": ["mood"],
                        "created_at": old_ts,
                        "updated_at": old_ts,
                    },
                    {
                        "id": "recent",
                        "submitted_at": recent_ts,
                        "responses": {"mood": 4},
                        "questions_asked": ["mood"],
                        "created_at": recent_ts,
                        "updated_at": recent_ts,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "checkins.checkin_data_manager.get_user_file_path",
        lambda _user_id, _file_type: str(checkins_file),
    )
    monkeypatch.setattr("checkins.checkin_data_manager.now_datetime_full", lambda: anchor)

    recent = get_checkins_by_days("user-1", days=7)

    assert len(recent) == 1
    assert recent[0]["mood"] == 4


@pytest.mark.unit
@pytest.mark.checkins
def test_is_user_checkins_enabled_reads_account_features(monkeypatch):
    monkeypatch.setattr(
        "checkins.checkin_data_manager.get_user_data",
        lambda _user_id, _data_type: {
            "account": {"features": {"checkins": "enabled"}}
        },
    )
    assert is_user_checkins_enabled("user-1") is True

    monkeypatch.setattr(
        "checkins.checkin_data_manager.get_user_data",
        lambda _user_id, _data_type: {"account": {"features": {"checkins": "disabled"}}},
    )
    assert is_user_checkins_enabled("user-1") is False
