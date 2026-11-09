"""Bulk schedule writes and numbered notebook list commands report failures safely."""

from copy import deepcopy
from unittest.mock import Mock

import pytest

from communication.command_handlers import notebook_handler
from communication.command_handlers.schedule_handler import ScheduleManagementHandler
from notebook.notebook_service import NotebookEntryResult

pytestmark = [pytest.mark.behavior, pytest.mark.communication]


@pytest.mark.parametrize("action", ["enable", "disable"])
@pytest.mark.parametrize("outcome", ["saved", "rejected", "exception", "empty"])
def test_bulk_schedule_outcomes_preserve_loaded_snapshot(monkeypatch, action, outcome):
    from core import schedule_runtime
    source = {} if outcome == "empty" else {
        "morning": {"active": False, "days": ["ALL"]},
        "evening": {"active": True, "days": ["Monday"]},
    }
    before = deepcopy(source)
    monkeypatch.setattr(schedule_runtime, "get_schedule_time_periods", lambda *_: source)
    save = Mock(return_value=outcome == "saved")
    if outcome == "exception":
        save.side_effect = RuntimeError("PRIVATE EXCEPTION")
    monkeypatch.setattr(schedule_runtime, "set_schedule_periods", save)
    response = ScheduleManagementHandler()._handle_update_schedule(
        "bulk-schedule-user", {"category": "task", "action": action}
    )
    assert source == before
    assert "PRIVATE" not in response.message
    if outcome == "empty":
        save.assert_not_called()
        assert "no schedule periods" in response.message
    else:
        save.assert_called_once()
        assert all(row["active"] == (action == "enable") for row in save.call_args.args[2].values())
        if outcome == "saved":
            assert ("enabled" if action == "enable" else "disabled") in response.message
        else:
            assert "couldn't confirm" in response.message
            assert "show my schedule" in response.message
            assert "✅" not in response.message


@pytest.mark.notebook
@pytest.mark.parametrize(
    "method,service,entities",
    [
        ("_handle_add_list_item", "add_item_to_list", {"item_text": "PRIVATE TEXT"}),
        ("_handle_toggle_list_item_done", "set_list_item_done", {"item_index": 1}),
        ("_handle_remove_list_item", "delete_list_item", {"item_index": 1}),
    ],
)
@pytest.mark.parametrize("raises", [False, True])
def test_list_mutation_failure_has_safe_recovery(monkeypatch, method, service, entities, raises):
    operation = Mock(return_value=NotebookEntryResult(None, False))
    if raises:
        operation.side_effect = RuntimeError("PRIVATE EXCEPTION")
    monkeypatch.setattr(notebook_handler, service, operation)
    response = getattr(notebook_handler.NotebookHandler(), method)(
        "list-failure-user", {"entry_ref": "PRIVATE REFERENCE", **entities}
    )
    operation.assert_called_once()
    assert "couldn't confirm" in response.message
    assert "!show <list ID>" in response.message
    assert "not found" not in response.message
    assert "PRIVATE" not in response.message
    if method == "_handle_remove_list_item":
        assert "numbering" in response.message


@pytest.mark.notebook
@pytest.mark.parametrize("number", [0, -1, 1.5, True, False, "1.5", "abc", "0"])
@pytest.mark.parametrize(
    "method,service",
    [("_handle_toggle_list_item_done", "set_list_item_done"),
     ("_handle_remove_list_item", "delete_list_item")],
)
def test_invalid_item_number_never_reaches_mutation(monkeypatch, number, method, service):
    operation = Mock()
    monkeypatch.setattr(notebook_handler, service, operation)
    response = getattr(notebook_handler.NotebookHandler(), method)(
        "list-index-user", {"entry_ref": "list-ref", "item_index": number}
    )
    operation.assert_not_called()
    assert "whole number starting at 1" in response.message
    assert "!show" in response.message


@pytest.mark.notebook
@pytest.mark.parametrize("method", ["_handle_toggle_list_item_done", "_handle_remove_list_item"])
def test_item_number_just_past_end_never_changes_last_item(test_data_dir, method):
    """Item 3 on a two-item list must not fall back to the last item."""
    from tests.test_helpers.test_utilities import TestUserFactory
    from notebook.notebook_data_manager import create_list, get_entry
    user_id = "list-past-end-user"
    TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    entry = create_list(user_id, title="Numbering check", items=["First", "Last"])
    entry_ref = str(entry.id)
    response = getattr(notebook_handler.NotebookHandler(), method)(
        user_id, {"entry_ref": entry_ref, "item_index": 3}
    )
    assert "Invalid item number" in response.message
    saved = get_entry(user_id, entry_ref)
    assert [(item.text, item.done) for item in saved.items] == [("First", False), ("Last", False)]
