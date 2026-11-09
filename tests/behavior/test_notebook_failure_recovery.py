"""Notebook commands retain useful replies across rejected and raised operations."""

from unittest.mock import Mock

import pytest

from communication.command_handlers import notebook_handler
from communication.command_handlers.shared_types import InteractionResponse, ParsedCommand
from notebook.notebook_service import (
    AMBIGUOUS_ENTRY_REFERENCE,
    MISSING_ENTRY_REFERENCE,
    NotebookEntryResult,
)
from notebook import notebook_service
from notebook.notebook_validation import MAX_TITLE_LENGTH

pytestmark = [pytest.mark.behavior, pytest.mark.communication, pytest.mark.notebook]


@pytest.mark.parametrize("failure", ["unconfirmed", "none", "exception"])
@pytest.mark.parametrize(
    "intent,service_name,entities,recovery",
    [
        ("create_note", "create_note_from_command",
         {"title": "PRIVATE TITLE", "description": "PRIVATE TEXT"}, "!recent"),
        ("create_quick_note", "create_quick_note_from_command",
         {"title": "PRIVATE TITLE"}, "!recent"),
        ("create_list", "create_list_from_command",
         {"title": "PRIVATE TITLE", "items": ["PRIVATE TEXT"]}, "!recent"),
        ("create_journal", "create_journal_from_command",
         {"title": "PRIVATE TITLE", "description": "PRIVATE TEXT"}, "!recent"),
        ("append_to_entry", "append_entry_body",
         {"entry_ref": "PRIVATE REFERENCE", "text": "PRIVATE TEXT"}, "!show"),
        ("set_entry_body", "replace_entry_body",
         {"entry_ref": "PRIVATE REFERENCE", "text": "PRIVATE TEXT"}, "!show"),
        ("add_tags_to_entry", "add_entry_tags",
         {"entry_ref": "PRIVATE REFERENCE", "tags": ["PRIVATE TAG"]}, "!tag"),
        ("remove_tags_from_entry", "remove_entry_tags",
         {"entry_ref": "PRIVATE REFERENCE", "tags": ["PRIVATE TAG"]}, "!show"),
        ("pin_entry", "pin_notebook_entry", {"entry_ref": "PRIVATE REFERENCE"}, "!pinned"),
        ("unpin_entry", "pin_notebook_entry", {"entry_ref": "PRIVATE REFERENCE"}, "!pinned"),
        ("archive_entry", "archive_notebook_entry", {"entry_ref": "PRIVATE REFERENCE"}, "!archived"),
        ("unarchive_entry", "archive_notebook_entry", {"entry_ref": "PRIVATE REFERENCE"}, "!archived"),
    ],
)
def test_notebook_command_failure_has_safe_recovery(
    monkeypatch, failure, intent, service_name, entities, recovery
):
    """Use real command routing and verify failed saves never become empty replies."""
    operation = Mock(return_value=None if failure == "none" else NotebookEntryResult(None, False))
    if failure == "exception":
        operation.side_effect = RuntimeError("PRIVATE EXCEPTION")
    monkeypatch.setattr(notebook_handler, service_name, operation)
    log_error = Mock()
    monkeypatch.setattr(notebook_handler.logger, "error", log_error)
    # Avoid any pre-existing conversation state in the note command's compatibility read.
    from communication.message_processing.conversation_flow_manager import conversation_manager
    monkeypatch.setattr(conversation_manager, "get_note_body_flow_data", lambda _: None)

    response = notebook_handler.NotebookHandler().handle(
        "notebook-failure-user", ParsedCommand(intent, entities, 1.0, "")
    )

    operation.assert_called_once()
    assert isinstance(response, InteractionResponse)
    assert response.completed
    assert "couldn't confirm" in response.message
    assert recovery in response.message
    assert "not found" not in response.message
    assert "PRIVATE" not in response.message
    if intent.startswith("create_") or intent in {"append_to_entry", "set_entry_body"}:
        assert "copy" in response.message
    if failure != "exception":
        log_error.assert_called_once()
        logged = log_error.call_args.args[0]
        assert "notebook-failure-user" in logged
        assert "operation=" in logged
        assert "PRIVATE" not in logged


@pytest.mark.parametrize(
    "intent,service_name,entities",
    [
        ("append_to_entry", "append_entry_body", {"text": "draft"}),
        ("set_entry_body", "replace_entry_body", {"text": "draft"}),
        ("add_tags_to_entry", "add_entry_tags", {"tags": ["work"]}),
        ("remove_tags_from_entry", "remove_entry_tags", {"tags": ["work"]}),
        ("pin_entry", "pin_notebook_entry", {}),
        ("archive_entry", "archive_notebook_entry", {}),
    ],
)
@pytest.mark.parametrize("error", [MISSING_ENTRY_REFERENCE, AMBIGUOUS_ENTRY_REFERENCE])
def test_notebook_reference_errors_remain_distinct(
    monkeypatch, intent, service_name, entities, error
):
    """Known reference problems should not be reported as storage failures."""
    operation = Mock(return_value=NotebookEntryResult(None, False, error))
    monkeypatch.setattr(notebook_handler, service_name, operation)
    log_error = Mock()
    monkeypatch.setattr(notebook_handler.logger, "error", log_error)
    response = notebook_handler.NotebookHandler().handle(
        "reference-error-user",
        ParsedCommand(intent, {"entry_ref": "unknown", **entities}, 1.0, ""),
    )
    operation.assert_called_once()
    assert "exact short ID" in response.message
    assert response.completed == (error == MISSING_ENTRY_REFERENCE)
    if error == MISSING_ENTRY_REFERENCE:
        assert "!recent" in response.message
        assert "!archived" in response.message
    else:
        assert "more than one" in response.message
    log_error.assert_not_called()


@pytest.mark.parametrize(
    "intent,persistence_name",
    [
        ("create_note", "create_note"),
        ("create_quick_note", "create_note"),
        ("create_list", "create_list"),
        ("create_journal", "create_journal"),
    ],
)
def test_notebook_long_title_gives_correction_before_persistence(
    monkeypatch, intent, persistence_name
):
    """Known title validation is distinct from an uncertain save outcome."""
    persistence = Mock()
    monkeypatch.setattr(notebook_service.data_manager, persistence_name, persistence)
    from communication.message_processing.conversation_flow_manager import conversation_manager
    monkeypatch.setattr(conversation_manager, "get_note_body_flow_data", lambda _: None)
    response = notebook_handler.NotebookHandler().handle(
        "title-error-user",
        ParsedCommand(intent, {
            "title": "A" * (MAX_TITLE_LENGTH + 1),
            "description": "Private body", "items": ["Private item"],
        }, 1.0, ""),
    )
    persistence.assert_not_called()
    assert "Invalid notebook title" in response.message
    assert str(MAX_TITLE_LENGTH) in response.message
    assert "body" in response.message
    assert "Keep a copy" in response.message
    assert "Private" not in response.message
