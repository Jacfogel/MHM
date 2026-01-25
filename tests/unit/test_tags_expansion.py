"""
Expanded unit coverage for tag normalization, parsing, and storage helpers.
"""

from pathlib import Path
from uuid import uuid4

import pytest

from core import tags as tags_module


@pytest.fixture()
def tag_env(test_data_dir, monkeypatch):
    """Provide a temporary tag storage environment within tests/data."""
    base_dir = Path(test_data_dir) / "tag-tests" / uuid4().hex
    user_dir = base_dir / "users" / "user_1"
    tags_file = user_dir / "tags.json"

    monkeypatch.setattr(tags_module, "get_user_data_dir", lambda user_id: str(user_dir))
    monkeypatch.setattr(
        tags_module, "get_user_file_path", lambda user_id, file_type: str(tags_file)
    )
    monkeypatch.setattr(
        tags_module, "_load_default_tags_from_resources", lambda: ["home", "work"]
    )

    return {"user_id": "user_1", "user_dir": user_dir, "tags_file": tags_file}


@pytest.mark.unit
@pytest.mark.user_management
@pytest.mark.parametrize(
    "input_tag, expected",
    [
        ("Work", "work"),
        ("#Work", "work"),
        ("  #Urgent  ", "urgent"),
        ("tag", "tag"),
        ("TAG", "tag"),
        ("#mixedCase", "mixedcase"),
        ("#with-hyphen", "with-hyphen"),
        ("#with_underscore", "with_underscore"),
        ("#with:colon", "with:colon"),
        ("  spaced  ", "spaced"),
        (123, "123"),
        (None, "none"),
    ],
)
def test_normalize_tag(input_tag, expected):
    assert tags_module.normalize_tag(input_tag) == expected


@pytest.mark.unit
@pytest.mark.user_management
@pytest.mark.parametrize(
    "input_tags, expected",
    [
        (["#Work", "work", "Urgent"], ["work", "urgent"]),
        (["one", "two", "two", "one"], ["one", "two"]),
        (["  spaced  ", "Spaced"], ["spaced"]),
        ([], []),
        (["#a", "#b", "#a"], ["a", "b"]),
        (["#mixed", "MIXED", "mixed"], ["mixed"]),
        (["#with-hyphen", "#with-hyphen"], ["with-hyphen"]),
        (["#with_underscore", "with_underscore"], ["with_underscore"]),
    ],
)
def test_normalize_tags(input_tags, expected):
    assert tags_module.normalize_tags(input_tags) == expected


@pytest.mark.unit
@pytest.mark.user_management
@pytest.mark.parametrize(
    "input_tags",
    [
        None,
        "not a list",
        123,
        {"tag": "value"},
    ],
)
def test_normalize_tags_invalid_input(input_tags):
    assert tags_module.normalize_tags(input_tags) == []


@pytest.mark.unit
@pytest.mark.user_management
@pytest.mark.parametrize(
    "tag",
    [
        "work",
        "home",
        "tag-1",
        "tag_2",
        "tag:proj",
        "a",
        "z9",
        "alpha123",
        "tag-name",
        "tag_name",
    ],
)
def test_validate_tag_valid(tag):
    assert tags_module.validate_tag(tag) is None


@pytest.mark.unit
@pytest.mark.user_management
@pytest.mark.parametrize(
    "tag",
    [
        "",
        None,
        "Invalid",
        "with space",
        "with/slash",
        "with.dot",
        "with,comma",
        "toolong" * 20,
        "#hash",
        "UPPER",
    ],
)
def test_validate_tag_invalid_returns_none(tag):
    assert tags_module.validate_tag(tag) is None


@pytest.mark.unit
@pytest.mark.user_management
@pytest.mark.parametrize(
    "text, expected_clean, expected_tags",
    [
        ("Review #Work #Urgent", "Review", ["work", "urgent"]),
        ("Plan project key:proj #tag", "Plan project", ["key:proj", "tag"]),
        ("#one #two", "", ["one", "two"]),
        ("No tags here", "No tags here", []),
        ("Mix #One and #two", "Mix  and", ["one", "two"]),
        ("Trailing #tag", "Trailing", ["tag"]),
        ("Embedded #tag in text", "Embedded  in text", ["tag"]),
        ("Multiple key:one key:two", "Multiple", ["key:one", "key:two"]),
        ("#dup #dup #dup", "", ["dup"]),
        ("key:proj #proj", "", ["key:proj", "proj"]),
        ("#with-dash", "-dash", ["with"]),
        ("#with_underscore", "", ["with_underscore"]),
        ("#with:colon", ":colon", ["with"]),
        ("Text #123", "Text", ["123"]),
        ("Text #a_b #c-d", "Text  -d", ["a_b", "c"]),
    ],
)
def test_parse_tags_from_text(text, expected_clean, expected_tags):
    cleaned, tags = tags_module.parse_tags_from_text(text)

    assert cleaned == expected_clean
    assert tags == expected_tags


@pytest.mark.unit
@pytest.mark.user_management
@pytest.mark.parametrize(
    "text",
    [
        123,
        None,
        {"text": "value"},
    ],
)
def test_parse_tags_from_text_invalid_input(text):
    cleaned, tags = tags_module.parse_tags_from_text(text)

    assert cleaned == text
    assert tags == []


@pytest.mark.unit
@pytest.mark.user_management
def test_load_user_tags_invalid_user_id():
    assert tags_module.load_user_tags("") == {}
    assert tags_module.load_user_tags(None) == {}


@pytest.mark.unit
@pytest.mark.user_management
def test_load_user_tags_creates_default_file(tag_env):
    user_id = tag_env["user_id"]
    tags_file = tag_env["tags_file"]

    assert not tags_file.exists()

    data = tags_module.load_user_tags(user_id)

    assert tags_file.exists()
    assert data.get("tags") == ["home", "work"]
    assert data.get("metadata", {}).get("initialized_with_defaults") is True


@pytest.mark.unit
@pytest.mark.user_management
def test_load_user_tags_reinitializes_corrupt_file(tag_env):
    user_id = tag_env["user_id"]
    tags_file = tag_env["tags_file"]
    tags_file.parent.mkdir(parents=True, exist_ok=True)
    tags_file.write_text("{not json", encoding="utf-8")

    data = tags_module.load_user_tags(user_id)

    assert data.get("data") == {}
    assert data.get("file_type") == "generic_json"


@pytest.mark.unit
@pytest.mark.user_management
def test_save_user_tags_updates_metadata(tag_env):
    user_id = tag_env["user_id"]

    data = {"tags": ["alpha", "beta"], "metadata": {"created_at": "old"}}
    assert tags_module.save_user_tags(user_id, data) is True

    loaded = tags_module.load_user_tags(user_id)
    assert loaded.get("tags") == ["alpha", "beta"]
    assert "updated_at" in loaded.get("metadata", {})


@pytest.mark.unit
@pytest.mark.user_management
def test_get_user_tags_returns_list(tag_env):
    user_id = tag_env["user_id"]
    tags_module.save_user_tags(user_id, {"tags": ["alpha"]})

    assert tags_module.get_user_tags(user_id) == ["alpha"]


@pytest.mark.unit
@pytest.mark.user_management
@pytest.mark.parametrize(
    "tag, expected",
    [
        ("work", True),
        ("#work", True),
        ("urgent", True),
        ("invalid tag", True),
        ("", False),
    ],
)
def test_add_user_tag(tag_env, tag, expected):
    user_id = tag_env["user_id"]

    result = tags_module.add_user_tag(user_id, tag)
    assert result is expected


@pytest.mark.unit
@pytest.mark.user_management
def test_add_user_tag_deduplicates(tag_env):
    user_id = tag_env["user_id"]

    assert tags_module.add_user_tag(user_id, "work") is True
    assert tags_module.add_user_tag(user_id, "work") is True

    tags = tags_module.get_user_tags(user_id)
    assert tags.count("work") == 1


@pytest.mark.unit
@pytest.mark.user_management
@pytest.mark.parametrize(
    "tag, expected",
    [
        ("work", True),
        ("missing", True),
        ("invalid tag", True),
    ],
)
def test_remove_user_tag(tag_env, tag, expected):
    user_id = tag_env["user_id"]

    tags_module.save_user_tags(user_id, {"tags": ["work"]})
    result = tags_module.remove_user_tag(user_id, tag)

    assert result is expected


@pytest.mark.unit
@pytest.mark.user_management
def test_ensure_tags_initialized_creates_file(tag_env):
    user_id = tag_env["user_id"]
    tags_file = tag_env["tags_file"]

    assert not tags_file.exists()

    tags_module.ensure_tags_initialized(user_id)

    assert tags_file.exists()
