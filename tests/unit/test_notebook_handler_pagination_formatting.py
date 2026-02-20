"""Targeted unit coverage for notebook handler pagination and formatting helpers."""

from uuid import uuid4
from unittest.mock import patch

import pytest

from communication.command_handlers.notebook_handler import NotebookHandler
from notebook.schemas import Entry, ListItem


def _note_entry(title: str) -> Entry:
    return Entry(kind="note", id=uuid4(), title=title, body="body")


@pytest.mark.unit
@pytest.mark.communication
@pytest.mark.notebook
class TestNotebookHandlerPaginationAndFormatting:
    def test_search_entries_adds_show_more_suggestion(self):
        handler = NotebookHandler()
        entries = [_note_entry(f"Note {i}") for i in range(6)]

        with patch(
            "communication.command_handlers.notebook_handler.search_entries",
            return_value=entries,
        ):
            response = handler._handle_search_entries(
                "user-1",
                {"query": "note", "offset": 2, "limit": 2},
            )

        assert response.completed is True
        assert "Found 6 entries" in response.message
        assert "Note 2" in response.message
        assert "Note 3" in response.message
        assert response.suggestions == ["Show More (2 more)"]

    def test_list_by_group_requires_group_name(self):
        handler = NotebookHandler()

        response = handler._handle_list_by_group("user-1", {})

        assert response.completed is False
        assert "Which group?" in response.message

    def test_list_pinned_with_default_entities_supports_pagination(self):
        handler = NotebookHandler()
        entries = [_note_entry(f"Pinned {i}") for i in range(7)]

        with patch(
            "communication.command_handlers.notebook_handler.list_pinned",
            return_value=entries,
        ):
            response = handler._handle_list_pinned("user-1", None)

        assert response.completed is True
        assert "Pinned entries (7)" in response.message
        assert response.suggestions == ["Show More (2 more)"]

    def test_format_entry_id_falls_back_when_short_id_is_missing(self):
        handler = NotebookHandler()
        entry = _note_entry("Fallback")

        with patch(
            "communication.command_handlers.notebook_handler.format_short_id",
            return_value=None,
        ):
            short_id = handler._format_entry_id(entry)

        assert short_id.startswith("n")
        assert len(short_id) == 7

    def test_format_entry_response_includes_list_metadata_and_items(self):
        handler = NotebookHandler()
        entry = Entry(
            kind="list",
            id=uuid4(),
            title="Weekend Plan",
            body="Checklist",
            group="home",
            tags=["work", "urgent"],
            pinned=True,
            archived=True,
            items=[
                ListItem(text="Clean kitchen", order=0, done=True),
                ListItem(text="Laundry", order=1, done=False),
            ],
        )

        response_text = handler._format_entry_response(entry)

        assert "Weekend Plan" in response_text
        assert "Group: home" in response_text
        assert "Tags: work, urgent" in response_text
        assert "Pinned" in response_text
        assert "Archived" in response_text
        assert "Clean kitchen" in response_text
        assert "Laundry" in response_text

