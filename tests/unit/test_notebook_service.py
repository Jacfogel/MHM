"""Unit coverage for notebook_service use-case functions."""

from unittest.mock import patch
from uuid import uuid4

import pytest

import notebook.notebook_service as ns
from notebook.notebook_schemas import Entry


@pytest.mark.unit
@pytest.mark.notebook
def test_create_note_from_command_normalizes_title_body_and_tags():
    entry = Entry(kind="note", id=uuid4(), title="Body text", tags=["idea"])

    with patch(
        "notebook.notebook_service.data_manager.create_note",
        return_value=entry,
    ) as create_note:
        result = ns.create_note_from_command(
            "user-1", {"description": "Body text #idea", "tags": []}
        )

    assert result.success is True
    assert result.entry is entry
    create_note.assert_called_once_with(
        "user-1",
        title="Body text",
        description=None,
        tags=["idea"],
        group=None,
    )


@pytest.mark.unit
@pytest.mark.notebook
def test_create_quick_note_from_command_assigns_quick_notes_group():
    entry = Entry(kind="note", id=uuid4(), title="Quick")

    with patch(
        "notebook.notebook_service.data_manager.create_note",
        return_value=entry,
    ) as create_note:
        result = ns.create_quick_note_from_command("user-1", {"title": "Quick #tag"})

    assert result.success is True
    create_note.assert_called_once_with(
        "user-1",
        title="Quick",
        description=None,
        tags=["tag"],
        group="Quick Notes",
    )


@pytest.mark.unit
@pytest.mark.notebook
def test_list_entries_by_group_returns_structured_result():
    entries = [Entry(kind="note", id=uuid4(), title="Grouped")]

    with patch(
        "notebook.notebook_service.data_manager.list_by_group",
        return_value=entries,
    ) as list_by_group:
        result = ns.list_entries_by_group("user-1", "work", limit=10)

    assert result.entries == entries
    assert result.total == 1
    assert result.filter_name == "group"
    assert result.filter_value == "work"
    list_by_group.assert_called_once_with("user-1", "work", limit=10)


@pytest.mark.unit
@pytest.mark.notebook
def test_add_entry_tags_returns_structured_result():
    entry = Entry(kind="note", id=uuid4(), title="Tagged", tags=["a"])

    with patch(
        "notebook.notebook_service.data_manager.add_tags",
        return_value=entry,
    ) as add_tags:
        result = ns.add_entry_tags("user-1", "n123", ["a"])

    assert result.success is True
    assert result.entry is entry
    add_tags.assert_called_once_with("user-1", "n123", ["a"])
