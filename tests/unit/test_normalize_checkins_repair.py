"""Tests for offline check-in envelope normalization."""

import json

import pytest

from core.response_tracking import normalize_checkins_envelope_for_repair, store_user_response
from core.user_data_v2 import SCHEMA_VERSION, validate_v2_document

TS = "2026-04-26 09:15:00"


@pytest.mark.unit
@pytest.mark.core
def test_normalize_none_is_empty_envelope():
    env = normalize_checkins_envelope_for_repair(None)
    assert env["schema_version"] == SCHEMA_VERSION
    assert env["checkins"] == []
    assert validate_v2_document("checkins", env)[1] == []


@pytest.mark.unit
@pytest.mark.core
def test_normalize_bare_list_to_v2():
    raw = [
        {
            "timestamp": TS,
            "mood": "okay",
            "questions_asked": ["mood"],
        }
    ]
    env = normalize_checkins_envelope_for_repair(raw)
    assert env["schema_version"] == SCHEMA_VERSION
    assert len(env["checkins"]) == 1
    assert env["checkins"][0]["submitted_at"] == TS
    assert env["checkins"][0]["responses"] == {"mood": "okay"}
    assert validate_v2_document("checkins", env)[1] == []


@pytest.mark.unit
@pytest.mark.core
def test_normalize_v2_round_trip_stable_rows():
    raw = {
        "schema_version": SCHEMA_VERSION,
        "updated_at": TS,
        "checkins": [
            {
                "id": "c1",
                "submitted_at": TS,
                "source": {"system": "mhm", "channel": "", "actor": ""},
                "responses": {"mood": "low"},
                "questions_asked": ["mood"],
                "linked_item_ids": [],
                "created_at": TS,
                "updated_at": TS,
                "archived_at": None,
                "deleted_at": None,
                "metadata": {},
            }
        ],
    }
    env = normalize_checkins_envelope_for_repair(raw)
    _, errs = validate_v2_document("checkins", env)
    assert errs == []
    assert json.dumps(raw["checkins"], sort_keys=True) == json.dumps(env["checkins"], sort_keys=True)


@pytest.mark.unit
@pytest.mark.core
def test_store_user_response_appends_to_v2_envelope(tmp_path, monkeypatch):
    checkins = tmp_path / "checkins.json"
    checkins.write_text(
        json.dumps(
            {
                "schema_version": SCHEMA_VERSION,
                "updated_at": TS,
                "checkins": [
                    {
                        "id": "existing",
                        "submitted_at": TS,
                        "source": {"system": "mhm", "channel": "", "actor": ""},
                        "responses": {"energy": "high"},
                        "questions_asked": ["energy"],
                        "linked_item_ids": [],
                        "created_at": TS,
                        "updated_at": TS,
                        "archived_at": None,
                        "deleted_at": None,
                        "metadata": {},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "core.response_tracking.get_user_file_path",
        lambda _uid, _ft: str(checkins),
    )
    store_user_response(
        "u1",
        {"mood": "fine", "questions_asked": ["mood"]},
        "checkin",
    )
    data = json.loads(checkins.read_text(encoding="utf-8"))
    assert data["schema_version"] == SCHEMA_VERSION
    assert len(data["checkins"]) == 2
    assert validate_v2_document("checkins", data)[1] == []
