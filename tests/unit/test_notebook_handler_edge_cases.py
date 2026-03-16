"""Additional edge-case coverage for notebook handler helper paths."""

from uuid import uuid4
from unittest.mock import patch
from typing import cast

import pytest

from communication.command_handlers.notebook_handler import NotebookHandler
from notebook.notebook_schemas import Entry, EntryKind


def _entry(title: str = "Sample", kind: str = "note") -> Entry:
    if kind == "list":
        from notebook.notebook_schemas import ListItem

        return Entry(
            kind="list",
            id=uuid4(),
            title=title,
            items=[ListItem(text="item", order=0, done=False)],
        )
    return Entry(kind=cast(EntryKind, kind), id=uuid4(), title=title)


@pytest.mark.unit
@pytest.mark.communication
@pytest.mark.notebook
class TestNotebookHandlerEdgeCases:
    def test_toggle_list_item_requires_entry_reference(self):
        handler = NotebookHandler()

        response = handler._handle_toggle_list_item_done("user-1", {"item_index": 1})

        assert response.completed is False
        assert "Which list?" in response.message

    def test_toggle_list_item_requires_item_number(self):
        handler = NotebookHandler()

        response = handler._handle_toggle_list_item_done("user-1", {"entry_ref": "l123"})

        assert response.completed is False
        assert "Which item number?" in response.message

    def test_toggle_list_item_rejects_non_numeric_index(self):
        handler = NotebookHandler()

        response = handler._handle_toggle_list_item_done(
            "user-1", {"entry_ref": "l123", "item_index": "abc"}
        )

        assert response.completed is True
        assert "Invalid item number." in response.message

    def test_toggle_list_item_can_mark_item_undone(self):
        handler = NotebookHandler()
        list_entry = _entry("Groceries", kind="list")

        with patch(
            "communication.command_handlers.notebook_handler.toggle_list_item_done",
            return_value=list_entry,
        ):
            response = handler._handle_toggle_list_item_done(
                "user-1",
                {"entry_ref": "l123", "item_index": 1, "done": False},
            )

        assert response.completed is True
        assert "marked undone" in response.message

    def test_remove_list_item_rejects_non_numeric_index(self):
        handler = NotebookHandler()

        response = handler._handle_remove_list_item(
            "user-1", {"entry_ref": "l123", "item_index": "x"}
        )

        assert response.completed is True
        assert "Invalid item number." in response.message

    def test_list_by_tag_requires_tag(self):
        handler = NotebookHandler()

        response = handler._handle_list_by_tag("user-1", {})

        assert response.completed is False
        assert "Which tag?" in response.message

    def test_list_archived_reports_empty_state(self):
        handler = NotebookHandler()

        with patch(
            "communication.command_handlers.notebook_handler.list_archived",
            return_value=[],
        ):
            response = handler._handle_list_archived("user-1", None)

        assert response.completed is True
        assert "No archived entries found." in response.message

    def test_list_inbox_adds_show_more_suggestion(self):
        handler = NotebookHandler()
        entries = [_entry(f"Inbox {idx}") for idx in range(6)]

        with patch(
            "communication.command_handlers.notebook_handler.list_inbox",
            return_value=entries,
        ):
            response = handler._handle_list_inbox("user-1", {"offset": 0, "limit": 3})

        assert response.completed is True
        assert "Inbox (6 entries)" in response.message
        assert response.suggestions == ["Show More (3 more)"]

