"""Unit coverage for storage.user_data_v2_envelopes validate_v2_document dispatcher."""

from __future__ import annotations

import pytest

from storage import user_data_v2_envelopes as envelopes


@pytest.mark.unit
@pytest.mark.storage
def test_validate_v2_document_unknown_type_returns_error():
    payload = {"schema_version": 2}
    data, errors = envelopes.validate_v2_document("unknown_kind", payload)

    assert data is payload
    assert errors == ["Unknown v2 document type: unknown_kind"]


@pytest.mark.unit
@pytest.mark.storage
@pytest.mark.parametrize(
    ("document_type", "validator_name"),
    [
        ("tasks", "validate_tasks_v2_document"),
        ("notebook", "validate_notebook_v2_document"),
        ("checkins", "validate_checkins_v2_document"),
        ("messages", "validate_messages_v2_document"),
        ("deliveries", "validate_deliveries_v2_document"),
    ],
)
def test_validate_v2_document_dispatches_to_domain_validator(
    monkeypatch, document_type, validator_name
):
    payload = {"schema_version": 2, "items": []}
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
def test_validate_v2_document_checkins_integration():
    payload = {
        "schema_version": 2,
        "updated_at": "2026-05-11 08:00:00",
        "checkins": [
            {
                "id": "chk-001",
                "submitted_at": "2026-05-11 08:00:00",
                "responses": {"mood": 4},
                "questions_asked": ["mood"],
                "linked_item_ids": [],
                "created_at": "2026-05-11 08:00:00",
                "updated_at": "2026-05-11 08:00:00",
            }
        ],
    }

    data, errors = envelopes.validate_v2_document("checkins", payload)

    assert errors == []
    assert data["schema_version"] == 2
    assert len(data["checkins"]) == 1
