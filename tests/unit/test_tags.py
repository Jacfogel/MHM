"""
Unit tests for `core.tags`, covering normalization, parsing, and user tag persistence.
"""

import json
import shutil
import uuid
from pathlib import Path

import pytest

from core import tags as tags_module
from core.tags import (
    add_user_tag,
    ensure_tags_initialized,
    load_user_tags,
    normalize_tag,
    normalize_tags,
    parse_tags_from_text,
    remove_user_tag,
    save_user_tags,
)


pytestmark = [
    pytest.mark.unit,
    pytest.mark.user_management,
    pytest.mark.regression,
]


@pytest.fixture
def unique_user_id():
    """Return a unique user id for each test to avoid collisions."""
    return f"tags_user_{uuid.uuid4().hex}"


@pytest.fixture
def user_dir(test_data_dir, unique_user_id):
    """Provide a user directory path and clean it up after the test."""
    path = Path(test_data_dir) / "users" / unique_user_id
    yield path
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


@pytest.mark.unit
def test_normalize_tag_strips_whitespace_and_hashes():
    assert normalize_tag("  #Work-Now  ") == "work-now"
    assert normalize_tag("Priority") == "priority"
    assert normalize_tag("#MiXeD:Case") == "mixed:case"


@pytest.mark.unit
def test_normalize_tags_handles_duplicates_and_invalid_types():
    assert normalize_tags("not a list") == []
    assert normalize_tags(["Work", "#work", "Personal", " personal "]) == [
        "work",
        "personal",
    ]


@pytest.mark.unit
def test_parse_tags_from_text_extracts_and_normalizes():
    text, discovered_tags = parse_tags_from_text(
        "Plan #Work personal:priority #work extra details"
    )
    assert "Plan" in text
    assert "extra" in text
    assert "#Work" not in text
    assert "personal:priority" not in text
    assert discovered_tags == ["work", "personal:priority"]


@pytest.mark.unit
def test__load_default_tags_from_resources_returns_known_values():
    defaults = tags_module._load_default_tags_from_resources()
    assert isinstance(defaults, list)
    assert "work" in defaults


@pytest.mark.unit
def test_ensure_user_dir_for_tags_returns_none_for_invalid_ids():
    assert tags_module.ensure_user_dir_for_tags("") is None
    assert tags_module.ensure_user_dir_for_tags(None) is None


@pytest.mark.unit
def test_load_user_tags_initializes_defaults(user_dir, unique_user_id):
    tags_file = user_dir / "tags.json"
    assert not tags_file.exists()

    result = load_user_tags(unique_user_id)

    assert tags_file.exists(), "tags.json should be created when missing"
    assert result["tags"] == tags_module._load_default_tags_from_resources()
    metadata = result.get("metadata", {})
    assert metadata.get("initialized_with_defaults", False)
    assert "created_at" in metadata
    assert "updated_at" in metadata


@pytest.mark.unit
def test_save_user_tags_normalizes_and_updates_metadata(user_dir, unique_user_id):
    tags_file = user_dir / "tags.json"
    payload = {
        "tags": ["Work", "#work", "New:Tag", "NEW:TAG"],
        "metadata": {"created_at": "initial"},
    }

    assert save_user_tags(unique_user_id, payload) is True
    assert tags_file.exists()

    saved = json.loads(tags_file.read_text(encoding="utf-8"))
    assert saved["tags"] == ["work", "new:tag"]
    assert saved["metadata"]["created_at"] == "initial"
    assert "updated_at" in saved["metadata"]


@pytest.mark.unit
def test_add_and_remove_user_tag_respects_normalization(user_dir, unique_user_id):
    tag_value = "Special_Tag"

    assert add_user_tag(unique_user_id, tag_value) is True
    data = load_user_tags(unique_user_id)
    assert "special_tag" in data["tags"]

    assert remove_user_tag(unique_user_id, tag_value) is True
    data = load_user_tags(unique_user_id)
    assert "special_tag" not in data["tags"]


@pytest.mark.unit
def test_ensure_tags_initialized_is_idempotent(user_dir, unique_user_id):
    ensure_tags_initialized(unique_user_id)
    assert (user_dir / "tags.json").exists()

    # Second call should be a no-op but still succeed
    ensure_tags_initialized(unique_user_id)
    assert (user_dir / "tags.json").exists()
