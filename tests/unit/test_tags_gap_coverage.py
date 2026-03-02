"""Gap-coverage tests for core.tags error and fallback paths."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core import tags as tags_module


@pytest.mark.unit
@pytest.mark.user_management
class TestTagsGapCoverage:
    def test_ensure_user_dir_for_tags_exception(self, monkeypatch):
        monkeypatch.setattr(
            tags_module,
            "get_user_data_dir",
            lambda user_id: (_ for _ in ()).throw(RuntimeError("dir fail")),
        )
        assert tags_module.ensure_user_dir_for_tags("u1") is None

    def test_load_default_tags_missing_invalid_and_exception(self, test_data_dir, monkeypatch):
        # Missing file branch.
        monkeypatch.setattr(
            tags_module,
            "Path",
            lambda *_args, **_kwargs: Path(test_data_dir) / "missing_default_tags.json",
        )
        assert tags_module._load_default_tags_from_resources() == []

        # Invalid format branch.
        default_file = Path(test_data_dir) / "default_tags_invalid.json"
        default_file.write_text(json.dumps({"unexpected": []}), encoding="utf-8")
        monkeypatch.setattr(tags_module, "Path", lambda *_args, **_kwargs: default_file)
        assert tags_module._load_default_tags_from_resources() == []

        # Exception branch.
        monkeypatch.setattr(tags_module.json, "load", lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("json fail")))
        assert tags_module._load_default_tags_from_resources() == []

    def test_load_default_tags_invalid_format_and_json_error_via_real_path(self, test_data_dir, monkeypatch):
        fake_module_dir = Path(test_data_dir) / "pkg" / "core"
        resources_dir = fake_module_dir.parent / "resources"
        resources_dir.mkdir(parents=True, exist_ok=True)

        # Point module __file__ so loader resolves resources/default_tags.json under test_data_dir.
        monkeypatch.setattr(tags_module, "__file__", str(fake_module_dir / "tags.py"))

        default_file = resources_dir / "default_tags.json"
        default_file.write_text(json.dumps({"not_tags": []}), encoding="utf-8")
        assert tags_module._load_default_tags_from_resources() == []

        default_file.write_text("{not-json}", encoding="utf-8")
        assert tags_module._load_default_tags_from_resources() == []

    def test_load_user_tags_error_branches(self, monkeypatch):
        assert tags_module.load_user_tags("") == {}

        monkeypatch.setattr(tags_module, "ensure_user_dir_for_tags", lambda user_id: None)
        monkeypatch.setattr(tags_module, "get_user_file_path", lambda user_id, file_type: "/tmp/tags.json")
        monkeypatch.setattr(tags_module.Path, "exists", lambda self: True)

        # Corrupted (None) branch.
        monkeypatch.setattr(tags_module, "load_json_data", lambda path: None)
        monkeypatch.setattr(tags_module, "_load_default_tags_from_resources", lambda: ["work"])
        monkeypatch.setattr(tags_module, "save_json_data", lambda data, path: True)
        data = tags_module.load_user_tags("u1")
        assert data.get("metadata", {}).get("reinitialized") is True

        # Invalid structure branch.
        monkeypatch.setattr(tags_module, "load_json_data", lambda path: [])
        data = tags_module.load_user_tags("u1")
        assert "tags" in data
        assert "metadata" in data

        # Outer exception branch.
        monkeypatch.setattr(
            tags_module,
            "get_user_file_path",
            lambda user_id, file_type: (_ for _ in ()).throw(RuntimeError("path fail")),
        )
        assert tags_module.load_user_tags("u1") == {}

    def test_save_user_tags_error_and_failure_paths(self, monkeypatch):
        assert tags_module.save_user_tags("", {"tags": []}) is False
        assert tags_module.save_user_tags("u1", ["not-dict"]) is False

        monkeypatch.setattr(tags_module, "ensure_user_dir_for_tags", lambda user_id: None)
        monkeypatch.setattr(tags_module, "get_user_file_path", lambda user_id, file_type: "/tmp/tags.json")
        monkeypatch.setattr(tags_module, "save_json_data", lambda data, path: False)

        payload = {"tags": ["Work"]}
        assert tags_module.save_user_tags("u1", payload) is False
        assert "metadata" in payload
        assert payload["tags"] == ["work"]

        monkeypatch.setattr(
            tags_module,
            "save_json_data",
            lambda data, path: (_ for _ in ()).throw(RuntimeError("save fail")),
        )
        assert tags_module.save_user_tags("u1", {"tags": []}) is False

    def test_add_user_tag_error_paths(self, monkeypatch):
        assert tags_module.add_user_tag("", "work") is False
        assert tags_module.add_user_tag("u1", "") is False
        assert tags_module.add_user_tag("u1", "#") is False

        original_validate_tag = tags_module.validate_tag
        monkeypatch.setattr(
            tags_module,
            "validate_tag",
            lambda tag: (_ for _ in ()).throw(ValueError("invalid tag")),
        )
        assert tags_module.add_user_tag("u1", "bad") is False
        monkeypatch.setattr(tags_module, "validate_tag", original_validate_tag)

        monkeypatch.setattr(tags_module, "load_user_tags", lambda user_id: {"tags": []})
        monkeypatch.setattr(tags_module, "save_user_tags", lambda user_id, data: False)
        assert tags_module.add_user_tag("u1", "newtag") is False

        monkeypatch.setattr(
            tags_module,
            "load_user_tags",
            lambda user_id: (_ for _ in ()).throw(RuntimeError("load fail")),
        )
        assert tags_module.add_user_tag("u1", "newtag") is False

    def test_remove_user_tag_error_paths(self, monkeypatch):
        assert tags_module.remove_user_tag("", "work") is False
        assert tags_module.remove_user_tag("u1", "") is False
        assert tags_module.remove_user_tag("u1", "#") is False

        monkeypatch.setattr(tags_module, "load_user_tags", lambda user_id: {"tags": ["work"]})
        monkeypatch.setattr(tags_module, "save_user_tags", lambda user_id, data: False)
        assert tags_module.remove_user_tag("u1", "work") is False

        monkeypatch.setattr(
            tags_module,
            "load_user_tags",
            lambda user_id: (_ for _ in ()).throw(RuntimeError("load fail")),
        )
        assert tags_module.remove_user_tag("u1", "work") is False

    def test_ensure_tags_initialized_branches(self, monkeypatch):
        # Empty user ID early return.
        assert tags_module.ensure_tags_initialized("") is None

        monkeypatch.setattr(
            tags_module,
            "get_user_tags",
            lambda user_id: (_ for _ in ()).throw(RuntimeError("init fail")),
        )
        assert tags_module.ensure_tags_initialized("u1") is None
