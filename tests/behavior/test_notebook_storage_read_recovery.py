"""Real notebook file failures reach read-command replies without rewriting data."""

import json
from unittest.mock import Mock

import pytest

from notebook import notebook_data_handlers as storage
from communication.command_handlers.notebook_handler import NotebookHandler

pytestmark = [pytest.mark.behavior, pytest.mark.communication, pytest.mark.notebook]


@pytest.mark.parametrize("method,entities", [
    ("_handle_list_recent", {}), ("_handle_search_entries", {"query": "work"}),
    ("_handle_list_pinned", {}), ("_handle_list_inbox", {}),
    ("_handle_list_by_tag", {"tag": "work"}), ("_handle_list_archived", {}),
])
@pytest.mark.parametrize("failure", ["json", "empty", "encoding", "envelope", "rows", "row", "permission"])
def test_notebook_storage_failure_is_not_an_empty_view(tmp_path, monkeypatch, method, entities, failure):
    path = tmp_path / "entries.json"
    contents = {
        "json": b'{"PRIVATE BODY":', "empty": b"", "encoding": b"\xff\xfe",
        "envelope": b'{"schema_version":1,"entries":[]}',
        "rows": b'{"schema_version":2,"entries":{}}',
        "row": b'{"schema_version":2,"entries":[{"title":"PRIVATE BODY"}]}',
        "permission": b'{"schema_version":2,"entries":[]}',
    }[failure]
    path.write_bytes(contents)
    if failure == "permission":
        from core import file_operations
        monkeypatch.setattr(file_operations, "open", Mock(side_effect=PermissionError("PRIVATE PATH")), raising=False)
    monkeypatch.setattr(storage, "_get_notebook_file_path", lambda _: path)
    response = getattr(NotebookHandler(), method)("read-error-user", entities)
    assert "couldn't load" in response.message
    assert "does not mean your notebook is empty" in response.message
    assert "PRIVATE" not in response.message
    assert path.read_bytes() == contents
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.parametrize("missing", [False, True])
def test_missing_or_valid_empty_notebook_is_successfully_empty(tmp_path, monkeypatch, missing):
    from notebook import notebook_service
    path = tmp_path / "entries.json"
    if not missing:
        path.write_text(json.dumps({"schema_version": 2, "entries": []}), encoding="utf-8")
    monkeypatch.setattr(storage, "_get_notebook_file_path", lambda _: path)
    result = notebook_service.list_recent_entries("empty-user")
    assert result.success
    assert result.entries == []
    response = NotebookHandler()._handle_list_recent("empty-user", {})
    assert "No recent entries" in response.message
    assert path.exists() == (not missing)


def test_invalid_row_does_not_present_partial_results_as_complete(tmp_path, monkeypatch):
    from notebook.notebook_schemas import Entry
    from notebook import notebook_service
    path = tmp_path / "entries.json"
    payload = storage._entries_payload([Entry(kind="note", title="Valid note")])
    payload["entries"].append({"title": "PRIVATE INVALID"})
    path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(storage, "_get_notebook_file_path", lambda _: path)
    result = notebook_service.list_recent_entries("mixed-user")
    assert not result.success
    assert result.entries == []
    assert json.loads(path.read_text(encoding="utf-8")) == payload


@pytest.mark.parametrize("contents", [None, b"PRIVATE INVALID JSON", b"\xff\xfe"])
def test_shared_json_nonrecovering_read_never_creates_or_repairs(tmp_path, contents):
    from core.file_operations import load_json_data
    path = tmp_path / "unreadable.json"
    if contents is not None:
        path.write_bytes(contents)
    assert load_json_data(str(path), recover=False) is None
    if contents is None:
        assert not path.exists()
    else:
        assert path.read_bytes() == contents
    assert set(tmp_path.iterdir()) == ({path} if contents is not None else set())
