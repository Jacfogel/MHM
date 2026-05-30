"""Unit coverage for check-in v2 schema validation."""

from __future__ import annotations

import pytest

from checkins.checkin_schemas import validate_checkins_v2_document


def _valid_checkin(**overrides) -> dict:
    base = {
        "id": "chk-001",
        "submitted_at": "2026-05-11 08:00:00",
        "responses": {"mood": 4},
        "questions_asked": ["mood"],
        "linked_item_ids": [],
        "created_at": "2026-05-11 08:00:00",
        "updated_at": "2026-05-11 08:00:00",
    }
    base.update(overrides)
    return base


def _valid_envelope(**overrides) -> dict:
    base = {
        "schema_version": 2,
        "updated_at": "2026-05-11 08:00:00",
        "checkins": [_valid_checkin()],
    }
    base.update(overrides)
    return base


@pytest.mark.unit
@pytest.mark.checkins
def test_validate_checkins_v2_document_accepts_valid_envelope():
    data = _valid_envelope()
    normalized, errors = validate_checkins_v2_document(data)

    assert errors == []
    assert normalized["schema_version"] == 2
    assert len(normalized["checkins"]) == 1
    assert normalized["checkins"][0]["id"] == "chk-001"


@pytest.mark.unit
@pytest.mark.checkins
def test_validate_checkins_v2_document_rejects_invalid_timestamp():
    data = _valid_envelope(
        checkins=[_valid_checkin(submitted_at="not-a-timestamp")]
    )
    _, errors = validate_checkins_v2_document(data)

    assert errors
    assert any("timestamp" in err.lower() for err in errors)


@pytest.mark.unit
@pytest.mark.checkins
def test_validate_checkins_v2_document_rejects_extra_top_level_fields():
    data = _valid_envelope(unexpected_field="nope")
    _, errors = validate_checkins_v2_document(data)

    assert errors


@pytest.mark.unit
@pytest.mark.checkins
def test_validate_checkins_v2_document_rejects_wrong_schema_version():
    data = _valid_envelope(schema_version=1)
    _, errors = validate_checkins_v2_document(data)

    assert errors
