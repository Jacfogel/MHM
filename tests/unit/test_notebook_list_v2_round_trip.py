"""List entries round-trip through v2 persistence helpers with full shared fields."""

import pytest

import notebook.notebook_data_manager as ndm
from notebook.notebook_data_handlers import _entry_runtime_to_v2, _entry_v2_to_runtime
from notebook.notebook_schemas import Entry

pytestmark = [pytest.mark.unit, pytest.mark.notebook]


@pytest.mark.unit
@pytest.mark.notebook
def test_create_list_then_v2_round_trip_preserves_shared_fields(monkeypatch):
    captured: list = []

    def save(uid: str, entries: list) -> None:
        captured[:] = list(entries)

    monkeypatch.setattr(ndm, "load_entries", lambda user_id: [])
    monkeypatch.setattr(ndm, "save_entries", save)

    entry = ndm.create_list(
        "user-list-roundtrip-1",
        title="Groceries",
        tags=["food"],
        items=["Milk", "Eggs"],
    )
    assert entry is not None
    assert len(captured) == 1

    runtime = captured[0].model_dump(mode="json")
    v2 = _entry_runtime_to_v2(runtime)
    assert v2["kind"] == "list"
    assert v2["short_id"]
    assert v2["short_id"].startswith("l")
    assert "-" not in v2["short_id"]
    assert v2["status"] == "active"
    assert v2["source"]["system"] == "mhm"
    assert v2["linked_item_ids"] == []
    assert v2["archived_at"] is None
    assert v2["deleted_at"] is None
    assert v2["metadata"] == {}
    assert isinstance(v2["items"], list) and len(v2["items"]) == 2
    assert v2["items"][0]["text"] == "Milk"

    restored = Entry.model_validate(_entry_v2_to_runtime(v2))
    assert restored.kind == "list"
    assert restored.items and len(restored.items) == 2
    assert restored.items[0].text == "Milk"
    assert restored.items[1].text == "Eggs"


def test_legacy_notebook_group_is_ignored_and_cleared_on_save():
    """Old v2 group values load safely but do not re-enter the runtime model."""
    legacy = {
        "id": "11111111-1111-1111-1111-111111111111",
        "short_id": "n111111",
        "kind": "note",
        "title": "Legacy note",
        "description": "Body",
        "category": "",
        "group": "old-folder",
        "tags": [],
        "status": "active",
        "pinned": False,
        "submitted_at": None,
        "items": None,
        "source": {"system": "mhm", "channel": "", "actor": ""},
        "linked_item_ids": [],
        "created_at": "2026-01-01 00:00:00",
        "updated_at": "2026-01-01 00:00:00",
        "archived_at": None,
        "deleted_at": None,
        "metadata": {},
    }

    runtime = _entry_v2_to_runtime(legacy)
    assert "group" not in runtime
    restored = Entry.model_validate(runtime)
    assert "group" not in restored.model_dump()
    assert _entry_runtime_to_v2(restored.model_dump(mode="json"))["group"] == ""
