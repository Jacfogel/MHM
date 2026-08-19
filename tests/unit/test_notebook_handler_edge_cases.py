"""Additional edge-case coverage for notebook handler helper paths."""

from uuid import uuid4
from unittest.mock import patch
from typing import cast

import pytest

from communication.command_handlers.shared_types import PaginationAction
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
            "communication.command_handlers.notebook_handler.set_list_item_done",
            return_value=type("Result", (), {"entry": list_entry})(),
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
            "communication.command_handlers.notebook_handler.list_archived_entries",
            return_value=type("Result", (), {"entries": []})(),
        ):
            response = handler._handle_list_archived("user-1", None)

        assert response.completed is True
        assert "No archived entries found." in response.message

    def test_list_inbox_adds_show_more_suggestion(self):
        handler = NotebookHandler()
        entries = [_entry(f"Inbox {idx}") for idx in range(6)]

        with patch(
            "communication.command_handlers.notebook_handler.list_inbox_entries",
            return_value=type("Result", (), {"entries": entries})(),
        ):
            response = handler._handle_list_inbox("user-1", {"offset": 0, "limit": 3})

        assert response.completed is True
        assert "Inbox (6 entries)" in response.message
        assert response.suggestions is None
        actions = (response.rich_data or {}).get("pagination_actions")
        assert isinstance(actions, list) and len(actions) == 1
        action = actions[0]
        assert isinstance(action, PaginationAction)
        assert action.domain == "notebook"
        assert action.action == "list_inbox_entries"
        assert action.params == {}
        assert action.limit == 3
        assert action.offset == 0
        assert action.next_offset == 3
        assert action.remaining_count == 3


@pytest.mark.unit
@pytest.mark.communication
@pytest.mark.notebook
class TestNotebookHandlerPublicFlowStart:
    """Notebook handler starts conversation flows through public APIs only."""

    def test_create_note_title_only_starts_note_body_flow(self):
        handler = NotebookHandler()
        with patch(
            "communication.message_processing.conversation_flow_manager.conversation_manager"
        ) as mock_cm:
            mock_cm.get_note_body_flow_data.return_value = None
            response = handler._handle_create_note("user-1", {"title": "Hello"})

        mock_cm.start_note_body_flow.assert_called_once_with(
            "user-1", title="Hello", tags=[], group=None
        )
        mock_cm._save_user_states.assert_not_called()
        assert response.completed is False
        assert "body" in response.message.lower()

    def test_create_note_with_body_does_not_start_flow(self):
        handler = NotebookHandler()
        created = _entry("Hello")
        with patch(
            "communication.message_processing.conversation_flow_manager.conversation_manager"
        ) as mock_cm, patch(
            "communication.command_handlers.notebook_handler.create_note_from_command",
            return_value=type("Result", (), {"entry": created})(),
        ):
            mock_cm.get_note_body_flow_data.return_value = None
            response = handler._handle_create_note(
                "user-1", {"title": "Hello", "description": "body"}
            )

        mock_cm.start_note_body_flow.assert_not_called()
        mock_cm._save_user_states.assert_not_called()
        assert response.completed is True
        assert "created" in response.message.lower()

    def test_create_note_merges_active_note_body_flow_data(self):
        handler = NotebookHandler()
        captured: dict = {}

        def _create(_user_id, entities):
            captured.update(entities)
            return type("Result", (), {"entry": _entry(entities["title"])})()

        with patch(
            "communication.message_processing.conversation_flow_manager.conversation_manager"
        ) as mock_cm, patch(
            "communication.command_handlers.notebook_handler.create_note_from_command",
            side_effect=_create,
        ):
            mock_cm.get_note_body_flow_data.return_value = {
                "title": "FromFlow",
                "tags": ["keep"],
                "group": "Inbox",
            }
            handler._handle_create_note("user-1", {"description": "body text"})

        assert captured["title"] == "FromFlow"
        assert captured["tags"] == ["keep"]
        assert captured["group"] == "Inbox"
        mock_cm.start_note_body_flow.assert_not_called()

    def test_create_list_title_only_starts_list_items_flow(self):
        handler = NotebookHandler()
        with patch(
            "communication.message_processing.conversation_flow_manager.conversation_manager"
        ) as mock_cm:
            response = handler._handle_create_list("user-1", {"title": "Groceries"})

        mock_cm.start_list_items_flow.assert_called_once_with(
            "user-1", title="Groceries", tags=[], group=None
        )
        mock_cm._save_user_states.assert_not_called()
        assert response.completed is False

    def test_create_journal_title_only_starts_journal_body_flow(self):
        handler = NotebookHandler()
        with patch(
            "communication.message_processing.conversation_flow_manager.conversation_manager"
        ) as mock_cm:
            response = handler._handle_create_journal("user-1", {"title": "Today"})

        mock_cm.start_journal_body_flow.assert_called_once_with(
            "user-1", title="Today", tags=[], group=None
        )
        mock_cm._save_user_states.assert_not_called()
        assert response.completed is False

    def test_edit_entry_starts_entry_edit_flow(self):
        handler = NotebookHandler()
        entry = _entry("Editable")
        with patch(
            "communication.command_handlers.notebook_handler.get_entry",
            return_value=entry,
        ), patch(
            "communication.message_processing.conversation_flow_manager.conversation_manager"
        ) as mock_cm:
            response = handler._handle_edit_entry(
                "user-1", {"entry_ref": str(entry.id)}
            )

        mock_cm.start_entry_edit_flow.assert_called_once_with(
            "user-1",
            entry_ref=str(entry.id),
            short_id=handler._format_entry_id(entry),
            title="Editable",
        )
        mock_cm._save_user_states.assert_not_called()
        assert response.completed is False
        assert "editing" in response.message.lower()
