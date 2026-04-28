"""Focused gap-coverage tests for notebook_data_manager."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

import pytest

import notebook.notebook_data_manager as ndm
from notebook.notebook_schemas import Entry, ListItem
from notebook.notebook_validation import MAX_BODY_LENGTH


def _note(
    entry_id: str,
    title: str,
    body: str | None = None,
    tags: list[str] | None = None,
    group: str | None = None,
    archived: bool = False,
    pinned: bool = False,
    updated_at: str = "2026-01-01 00:00:00",
) -> Entry:
    return Entry(
        id=UUID(entry_id),
        kind="note",
        title=title,
        body=body,
        tags=tags or [],
        group=group,
        archived=archived,
        pinned=pinned,
        updated_at=updated_at,
    )


def _list(
    entry_id: str,
    title: str,
    item_texts: list[str],
    tags: list[str] | None = None,
    group: str | None = None,
    archived: bool = False,
    pinned: bool = False,
    updated_at: str = "2026-01-01 00:00:00",
) -> Entry:
    items = [ListItem(text=text, order=i) for i, text in enumerate(item_texts)]
    return Entry(
        id=UUID(entry_id),
        kind="list",
        title=title,
        items=items,
        tags=tags or [],
        group=group,
        archived=archived,
        pinned=pinned,
        updated_at=updated_at,
    )


@pytest.mark.unit
@pytest.mark.notebook
class TestNotebookDataManagerGapCoverage:
    def test_find_entry_by_ref_variants(self):
        entries = [
            _note("11111111-1111-1111-1111-111111111111", "Alpha Entry"),
            _note("22222222-2222-2222-2222-222222222222", "Beta Entry"),
        ]

        assert ndm._find_entry_by_ref(entries, str(entries[0].id)) == entries[0]
        assert ndm._find_entry_by_ref(entries, "n111111") == entries[0]
        assert ndm._find_entry_by_ref(entries, "beta entry") == entries[1]
        assert ndm._find_entry_by_ref(entries, "alpha") == entries[0]
        assert ndm._find_entry_by_ref(entries, "bad ref !") is None

    def test_find_entry_by_ref_multiple_short_id_match_returns_first(self):
        entries = [
            _note("aaaaaa11-1111-1111-1111-111111111111", "First"),
            _note("aaaaaa22-2222-2222-2222-222222222222", "Second"),
        ]
        assert ndm._find_entry_by_ref(entries, "naaaaaa") == entries[0]

    def test_create_entry_rejects_missing_user_and_bad_kind(self):
        assert ndm.create_entry("", "note", title="T", body="B") is None
        assert ndm.create_entry("user-1", "invalid_kind", title="T", body="B") is None

    def test_create_entry_accepts_listitem_objects(self, monkeypatch):
        saved_entries = []
        monkeypatch.setattr(ndm, "load_entries", lambda user_id: [])
        monkeypatch.setattr(
            ndm, "save_entries", lambda user_id, entries: saved_entries.extend(entries)
        )
        item = ListItem(text="One", order=0)

        entry = ndm.create_entry(
            "user-1",
            "list",
            title="My list",
            items=[item],
        )
        assert entry is not None
        assert entry.kind == "list"
        assert len(entry.items or []) == 1
        assert len(saved_entries) == 1

    def test_create_entry_rejects_invalid_list_item_dict(self, monkeypatch):
        monkeypatch.setattr(ndm, "load_entries", lambda user_id: [])
        monkeypatch.setattr(ndm, "save_entries", lambda user_id, entries: None)
        # Missing required text field for ListItem validation.
        assert ndm.create_entry("user-1", "list", title="Bad list", items=[{}]) is None

    def test_create_entry_ignores_items_for_non_list_kind(self, monkeypatch):
        monkeypatch.setattr(ndm, "load_entries", lambda user_id: [])
        monkeypatch.setattr(ndm, "save_entries", lambda user_id, entries: None)
        entry = ndm.create_entry(
            "user-1",
            "note",
            title="Note title",
            body="Body",
            items=[{"text": "ignored", "order": 0}],
        )
        assert entry is not None
        assert entry.items is None

    def test_create_list_default_and_blank_items_fallback(self, monkeypatch):
        monkeypatch.setattr(ndm, "load_entries", lambda user_id: [])
        monkeypatch.setattr(ndm, "save_entries", lambda user_id, entries: None)

        default_item_entry = ndm.create_list("user-1", "Default list", items=None)
        assert default_item_entry is not None
        assert (default_item_entry.items or [])[0].text == "New item"

        fallback_entry = ndm.create_list("user-1", "Fallback list", items=["   ", ""])
        assert fallback_entry is not None
        assert len(fallback_entry.items or []) == 1
        assert (fallback_entry.items or [])[0].text == "New item"

    def test_create_note_wrapper(self, monkeypatch):
        monkeypatch.setattr(ndm, "load_entries", lambda user_id: [])
        monkeypatch.setattr(ndm, "save_entries", lambda user_id, entries: None)
        entry = ndm.create_note("user-1", title="Note wrapper", body="wrapped")
        assert entry is not None
        assert entry.kind == "note"

    def test_create_journal_wrapper(self, monkeypatch):
        monkeypatch.setattr(ndm, "load_entries", lambda user_id: [])
        monkeypatch.setattr(ndm, "save_entries", lambda user_id, entries: None)
        entry = ndm.create_journal("user-1", title="Journal", body="Today was good")
        assert entry is not None
        assert entry.kind == "journal_entry"

    def test_save_updated_entry_helper(self, monkeypatch):
        note = _note("12121212-1212-1212-1212-121212121212", "Save helper")
        monkeypatch.setattr(ndm, "now_timestamp_full", lambda: "2026-02-01 01:02:03")
        monkeypatch.setattr(ndm, "save_entries", lambda user_id, entries: None)
        result = ndm._save_updated_entry("user-1", note, [note])
        assert result.updated_at == "2026-02-01 01:02:03"

    def test_append_to_entry_body_edge_paths(self, monkeypatch):
        note = _note("33333333-3333-3333-3333-333333333333", "Body note", body=None)
        list_entry = _list(
            "44444444-4444-4444-4444-444444444444", "List", ["A", "B"]
        )

        assert ndm.append_to_entry_body("", str(note.id), "x") is None

        monkeypatch.setattr(ndm, "load_entries", lambda user_id: [list_entry])
        assert ndm.append_to_entry_body("user-1", str(list_entry.id), "x") is None

        too_long_note = _note(
            "55555555-5555-5555-5555-555555555555",
            "Long body",
            body="x" * MAX_BODY_LENGTH,
        )
        monkeypatch.setattr(ndm, "load_entries", lambda user_id: [too_long_note])
        assert ndm.append_to_entry_body("user-1", str(too_long_note.id), "x") is None

        monkeypatch.setattr(ndm, "load_entries", lambda user_id: [note])
        monkeypatch.setattr(ndm, "_save_updated_entry", lambda user_id, entry, all_entries: entry)
        updated = ndm.append_to_entry_body("user-1", str(note.id), "new text")
        assert updated is not None
        assert updated.body == "new text"

    def test_set_entry_body_edge_paths(self, monkeypatch):
        note = _note("66666666-6666-6666-6666-666666666666", "Set body", body="old")
        list_entry = _list(
            "77777777-7777-7777-7777-777777777777", "Set body list", ["item"]
        )

        assert ndm.set_entry_body("", str(note.id), "new") is None

        monkeypatch.setattr(ndm, "load_entries", lambda user_id: [])
        assert ndm.set_entry_body("user-1", str(note.id), "new") is None

        monkeypatch.setattr(ndm, "load_entries", lambda user_id: [list_entry])
        assert ndm.set_entry_body("user-1", str(list_entry.id), "new") is None

        monkeypatch.setattr(ndm, "load_entries", lambda user_id: [note])
        monkeypatch.setattr(ndm, "_save_updated_entry", lambda user_id, entry, all_entries: entry)
        updated = ndm.set_entry_body("user-1", str(note.id), "new")
        assert updated is not None
        assert updated.body == "new"

    def test_search_entries_validation_and_sort_fallback(self, monkeypatch):
        assert ndm.search_entries("", "query") == []
        assert ndm.search_entries("user-1", "   ") == []

        note_title = _note(
            "88888888-8888-8888-8888-888888888888",
            "Project Alpha",
            body="body text",
            updated_at="2026-01-03 12:00:00",
        )
        note_body = _note(
            "99999999-9999-9999-9999-999999999999",
            "Unrelated",
            body="Contains query term",
            updated_at="2026-01-02 12:00:00",
        )
        list_entry = _list(
            "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "Shopping",
            ["query item"],
            updated_at="2026-01-01 12:00:00",
        )
        archived_note = _note(
            "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            "query in archived",
            archived=True,
        )
        monkeypatch.setattr(
            ndm, "load_entries", lambda user_id: [note_title, note_body, list_entry, archived_note]
        )
        result = ndm.search_entries("user-1", "query", limit=10)
        assert len(result) == 2
        assert all(not entry.archived for entry in result)

        monkeypatch.setattr(ndm, "parse_timestamp_full", lambda ts: (_ for _ in ()).throw(ValueError("bad parse")))
        unsorted_result = ndm.search_entries("user-1", "query", limit=10)
        assert len(unsorted_result) == 2

    def test_add_toggle_remove_list_items_edge_paths(self, monkeypatch):
        list_entry = _list(
            "cccccccc-cccc-cccc-cccc-cccccccccccc",
            "Todos",
            ["A", "B", "C"],
        )
        non_list = _note("dddddddd-dddd-dddd-dddd-dddddddddddd", "Not list")
        empty_items_list = _list(
            "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
            "Empty by patch",
            ["x"],
        )
        empty_items_list.items = None

        assert ndm.add_list_item("", str(list_entry.id), "x") is None
        assert ndm.add_list_item("user-1", str(list_entry.id), "   ") is None

        monkeypatch.setattr(ndm, "load_entries", lambda user_id: [])
        assert ndm.add_list_item("user-1", str(list_entry.id), "x") is None

        monkeypatch.setattr(ndm, "load_entries", lambda user_id: [non_list])
        assert ndm.add_list_item("user-1", str(non_list.id), "x") is None

        monkeypatch.setattr(ndm, "load_entries", lambda user_id: [empty_items_list])
        monkeypatch.setattr(ndm, "_save_updated_entry", lambda user_id, entry, all_entries: entry)
        added = ndm.add_list_item("user-1", str(empty_items_list.id), "new")
        assert added is not None
        assert len(added.items or []) == 1
        assert (added.items or [])[0].text == "new"

        monkeypatch.setattr(ndm, "load_entries", lambda user_id: [non_list])
        assert ndm.toggle_list_item_done("user-1", str(non_list.id), 1) is None
        assert ndm.remove_list_item("user-1", str(non_list.id), 1) is None

        monkeypatch.setattr(ndm, "load_entries", lambda user_id: [list_entry])
        assert ndm.toggle_list_item_done("user-1", str(list_entry.id), 999) is None
        assert ndm.remove_list_item("user-1", str(list_entry.id), 999) is None

        toggled = ndm.toggle_list_item_done("user-1", str(list_entry.id), 1, done=True)
        assert toggled is not None
        assert any(item.done for item in (toggled.items or []))

        removed = ndm.remove_list_item("user-1", str(list_entry.id), 2)
        assert removed is not None
        assert len(removed.items or []) == 2
        assert [item.order for item in (removed.items or [])] == [0, 1]

    def test_get_entry_list_recent_and_mutation_wrappers(self, monkeypatch):
        first = _note(
            "13131313-1313-1313-1313-131313131313",
            "First",
            tags=["alpha"],
            updated_at="2026-01-01 12:00:00",
        )
        second = _note(
            "14141414-1414-1414-1414-141414141414",
            "Second",
            tags=["beta"],
            archived=True,
            updated_at="2026-01-02 12:00:00",
        )
        monkeypatch.setattr(ndm, "load_entries", lambda user_id: [first, second])
        monkeypatch.setattr(ndm, "_save_updated_entry", lambda user_id, entry, all_entries: entry)

        found = ndm.get_entry("user-1", str(first.id))
        assert found is not None
        assert found.title == "First"

        recent_unarchived = ndm.list_recent("user-1", n=5, include_archived=False)
        assert len(recent_unarchived) == 1
        assert recent_unarchived[0].title == "First"

        recent_all = ndm.list_recent("user-1", n=5, include_archived=True)
        assert len(recent_all) == 2
        assert recent_all[0].title == "Second"

        tagged = ndm.add_tags("user-1", str(first.id), ["beta", "Gamma"])
        assert tagged is not None
        assert "beta" in tagged.tags
        assert "gamma" in tagged.tags

        untagged = ndm.remove_tags("user-1", str(first.id), ["alpha"])
        assert untagged is not None
        assert "alpha" not in untagged.tags

        pinned = ndm.pin_entry("user-1", str(first.id), pinned=True)
        assert pinned is not None
        assert pinned.pinned is True

        archived = ndm.archive_entry("user-1", str(first.id), archived=True)
        assert archived is not None
        assert archived.archived is True

        grouped = ndm.set_group("user-1", str(first.id), "  work  ")
        assert grouped is not None
        assert grouped.group == "work"

        cleared_group = ndm.set_group("user-1", str(first.id), None)
        assert cleared_group is not None
        assert cleared_group.group is None

    def test_mutation_wrappers_return_none_for_missing_or_invalid_group(self, monkeypatch):
        monkeypatch.setattr(ndm, "load_entries", lambda user_id: [])
        assert ndm.add_tags("user-1", "missing-ref", ["x"]) is None
        assert ndm.remove_tags("user-1", "missing-ref", ["x"]) is None
        assert ndm.pin_entry("user-1", "missing-ref", pinned=True) is None
        assert ndm.archive_entry("user-1", "missing-ref", archived=True) is None
        assert ndm.set_group("user-1", "missing-ref", "work") is None
        assert ndm.set_group("user-1", "missing-ref", "bad@group") is None

    def test_organization_listing_paths(self, monkeypatch):
        recent_now = datetime(2026, 1, 31, 12, 0, 0)
        entries = [
            _note(
                "f1f1f1f1-f1f1-f1f1-f1f1-f1f1f1f1f1f1",
                "Work one",
                group="work",
                tags=[],
                pinned=True,
                updated_at="2026-01-31 11:00:00",
            ),
            _note(
                "f2f2f2f2-f2f2-f2f2-f2f2-f2f2f2f2f2f2",
                "Work archived",
                group="work",
                tags=["x"],
                pinned=True,
                archived=True,
                updated_at="2026-01-30 11:00:00",
            ),
            _note(
                "f3f3f3f3-f3f3-f3f3-f3f3-f3f3f3f3f3f3",
                "Tagged",
                tags=["work"],
                updated_at="2026-01-29 11:00:00",
            ),
            _note(
                "f4f4f4f4-f4f4-f4f4-f4f4-f4f4f4f4f4f4",
                "Bad timestamp inbox",
                tags=[],
                updated_at="not-a-timestamp",
            ),
        ]
        monkeypatch.setattr(ndm, "load_entries", lambda user_id: entries)
        monkeypatch.setattr(ndm, "now_datetime_full", lambda: recent_now)

        by_group = ndm.list_by_group("user-1", "WORK", limit=10)
        assert len(by_group) == 2

        pinned = ndm.list_pinned("user-1", limit=10)
        assert len(pinned) == 1
        assert pinned[0].title == "Work one"

        inbox = ndm.list_inbox("user-1", days=7, limit=10)
        assert any(entry.title == "Bad timestamp inbox" for entry in inbox)

        archived = ndm.list_archived("user-1", limit=10)
        assert len(archived) == 1
        assert archived[0].archived is True

        by_tag = ndm.list_by_tag("user-1", "WORK", limit=10)
        assert len(by_tag) == 1
        assert by_tag[0].title == "Tagged"
