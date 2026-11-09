"""Unit coverage for notebook_service use-case functions."""

from unittest.mock import patch
from uuid import uuid4

import pytest

import notebook.notebook_service as ns
from notebook.notebook_validation import MAX_TITLE_LENGTH
from notebook.notebook_schemas import Entry
from notebook.notebook_data_manager import EntryReferenceResolution


@pytest.mark.unit
@pytest.mark.notebook
@pytest.mark.parametrize("remove", [False, True])
@pytest.mark.parametrize("index", [-1, 2, True])
def test_list_service_rejects_invalid_zero_based_index_before_mutation(remove, index):
    from notebook.notebook_schemas import ListItem
    entry = Entry(kind="list", title="List", items=[
        ListItem(text="First", order=0), ListItem(text="Last", order=1)
    ])
    method = ns.delete_list_item if remove else ns.set_list_item_done
    persistence_name = "remove_list_item" if remove else "toggle_list_item_done"
    with patch.object(ns, "resolve_notebook_entry", return_value=ns.NotebookEntryResult(entry, True)), \
         patch.object(ns.data_manager, persistence_name) as persist:
        result = method("user-1", str(entry.id), index) if remove else method("user-1", str(entry.id), index, True)
    assert result.error == ns.INVALID_LIST_ITEM_INDEX
    persist.assert_not_called()


@pytest.mark.unit
@pytest.mark.notebook
@pytest.mark.parametrize(
    "create,persistence_name",
    [
        (ns.create_note_from_command, "create_note"),
        (ns.create_quick_note_from_command, "create_note"),
        (ns.create_list_from_command, "create_list"),
        (ns.create_journal_from_command, "create_journal"),
    ],
)
def test_notebook_creation_accepts_title_at_limit(create, persistence_name):
    """Preflight validation must preserve the existing inclusive title limit."""
    title = "A" * MAX_TITLE_LENGTH
    entry = Entry(kind="note", title=title)
    with patch.object(ns.data_manager, persistence_name, return_value=entry) as persist:
        result = create("title-limit-user", {"title": title, "items": ["Item"]})
    assert result.success
    assert result.entry is entry
    persist.assert_called_once()


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
    )


@pytest.mark.unit
@pytest.mark.notebook
def test_create_quick_note_from_command_saves_title_and_tags():
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
    )


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


@pytest.mark.unit
@pytest.mark.notebook
def test_failed_mutation_preserves_ambiguous_reference_result():
    with (
        patch(
            "notebook.notebook_service.data_manager.archive_entry",
            return_value=None,
        ),
        patch(
            "notebook.notebook_service.data_manager.resolve_entry_reference",
            return_value=EntryReferenceResolution(None, ambiguous=True, match_count=2),
        ),
    ):
        result = ns.archive_notebook_entry("user-1", "shared title")

    assert result.success is False
    assert result.entry is None
    assert result.error == ns.AMBIGUOUS_ENTRY_REFERENCE
