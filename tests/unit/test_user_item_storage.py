from pathlib import Path

import pytest

from core.user_item_storage import (
    ensure_user_subdir,
    get_user_subdir_path,
    load_user_json_file,
    save_user_json_file,
)


@pytest.mark.unit
class TestUserItemStorageCoverage:
    def test_get_user_subdir_path_invalid_user_id(self):
        assert get_user_subdir_path("", "tasks") is None

    def test_get_user_subdir_path_empty_base_path(self, monkeypatch):
        monkeypatch.setattr("core.user_item_storage.get_user_data_dir", lambda _uid: "")
        assert get_user_subdir_path("u1", "tasks") is None

    def test_ensure_user_subdir_none_path(self, monkeypatch):
        monkeypatch.setattr("core.user_item_storage.get_user_subdir_path", lambda *_args, **_kwargs: None)
        assert ensure_user_subdir("u1", "tasks") is None

    def test_load_user_json_file_invalid_path_returns_default(self, monkeypatch):
        monkeypatch.setattr("core.user_item_storage.get_user_subdir_path", lambda *_args, **_kwargs: None)
        fallback = {"items": []}
        assert load_user_json_file("u1", "tasks", "active.json", fallback) == fallback

    def test_load_user_json_file_none_raw_returns_default(self, monkeypatch, tmp_path):
        monkeypatch.setattr("core.user_item_storage.get_user_subdir_path", lambda *_args, **_kwargs: Path(tmp_path))
        monkeypatch.setattr("core.user_item_storage.load_json_data", lambda _path: None)

        fallback = []
        assert load_user_json_file("u1", "tasks", "active.json", fallback) == fallback

    def test_load_user_json_file_list_expected_but_wrong_type(self, monkeypatch, tmp_path):
        monkeypatch.setattr("core.user_item_storage.get_user_subdir_path", lambda *_args, **_kwargs: Path(tmp_path))
        monkeypatch.setattr("core.user_item_storage.load_json_data", lambda _path: {"not": "a list"})

        fallback = []
        assert load_user_json_file("u1", "tasks", "active.json", fallback) == fallback

    def test_load_user_json_file_extracts_single_embedded_list(self, monkeypatch, tmp_path):
        monkeypatch.setattr("core.user_item_storage.get_user_subdir_path", lambda *_args, **_kwargs: Path(tmp_path))
        monkeypatch.setattr("core.user_item_storage.load_json_data", lambda _path: {"tasks": [{"id": 1}]})

        assert load_user_json_file("u1", "tasks", "active.json", []) == [{"id": 1}]

    def test_load_user_json_file_dict_expected_but_list_given(self, monkeypatch, tmp_path):
        monkeypatch.setattr("core.user_item_storage.get_user_subdir_path", lambda *_args, **_kwargs: Path(tmp_path))
        monkeypatch.setattr("core.user_item_storage.load_json_data", lambda _path: [{"id": 1}])

        fallback = {"tasks": []}
        assert load_user_json_file("u1", "tasks", "active.json", fallback) == fallback

    def test_save_user_json_file_returns_false_when_subdir_fails(self, monkeypatch):
        monkeypatch.setattr("core.user_item_storage.ensure_user_subdir", lambda *_args, **_kwargs: None)
        assert save_user_json_file("u1", "tasks", "active.json", []) is False

    def test_save_user_json_file_success_path(self, monkeypatch, tmp_path):
        monkeypatch.setattr("core.user_item_storage.ensure_user_subdir", lambda *_args, **_kwargs: Path(tmp_path))
        monkeypatch.setattr("core.user_item_storage.save_json_data", lambda _data, _path: True)
        assert save_user_json_file("u1", "tasks", "active.json", [{"id": 1}]) is True
