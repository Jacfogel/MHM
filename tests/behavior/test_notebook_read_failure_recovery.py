"""Notebook service/query failures must not masquerade as successful empty views."""

from unittest.mock import Mock

import pytest

from communication.command_handlers import notebook_handler
from notebook import notebook_service
from notebook.notebook_schemas import Entry

pytestmark = [pytest.mark.behavior, pytest.mark.communication, pytest.mark.notebook]


@pytest.mark.parametrize(
    "method,query,entities,command,empty_message",
    [
        ("_handle_list_recent", "list_recent", {}, "!recent", "No recent entries"),
        ("_handle_search_entries", "search_entries", {"query": "PRIVATE"}, "!s", "No entries"),
        ("_handle_list_pinned", "list_pinned", {}, "!pinned", "No pinned entries"),
        ("_handle_list_inbox", "list_inbox", {}, "!inbox", "Inbox is empty"),
        ("_handle_list_by_tag", "list_by_tag", {"tag": "PRIVATE"}, "!t", "No entries"),
        ("_handle_list_archived", "list_archived", {}, "!archived", "No archived entries"),
    ],
)
@pytest.mark.parametrize("outcome", ["exception", "absent", "empty", "display_exception"])
def test_notebook_read_failure_is_distinct_from_empty(
    monkeypatch, method, query, entities, command, empty_message, outcome
):
    monkeypatch.setattr(notebook_service, "load_entries_for_query", lambda _: [])
    load = Mock(return_value=[] if outcome == "empty" else None)
    if outcome == "exception":
        load.side_effect = RuntimeError("PRIVATE EXCEPTION")
    if outcome == "display_exception":
        load.return_value = [Entry(kind="note", title="Entry")]
        monkeypatch.setattr(
            notebook_handler, "paginate_items", Mock(side_effect=RuntimeError("PRIVATE EXCEPTION"))
        )
    monkeypatch.setattr(notebook_service.data_manager, query + "_from_snapshot", load)
    response = getattr(notebook_handler.NotebookHandler(), method)("query-failure-user", entities)
    load.assert_called_once()
    assert response is not None
    if outcome == "empty":
        assert empty_message in response.message
    else:
        assert "couldn't" in response.message
        assert command in response.message or "!recent" in response.message
        assert empty_message not in response.message
        assert "PRIVATE" not in response.message


@pytest.mark.parametrize("notes_only", [False, True])
def test_recent_notes_failure_keeps_query_failure_status(monkeypatch, notes_only):
    monkeypatch.setattr(notebook_service, "load_entries_for_query", lambda _: [])
    monkeypatch.setattr(notebook_service.data_manager, "list_recent_from_snapshot", Mock(side_effect=OSError("unavailable")))
    result = notebook_service.list_recent_entries("notes-user", notes_only=notes_only)
    assert not result.success
    response = notebook_handler.NotebookHandler()._handle_list_recent("notes-user", {}, notes_only=notes_only)
    assert "couldn't load" in response.message
    assert "No recent notes" not in response.message
