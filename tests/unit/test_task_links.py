"""Unit tests for structured task link helpers and persistence."""

from unittest.mock import patch

import pytest

from tasks.task_link_helpers import (
    MAX_TASK_LINKS,
    build_task_link,
    extract_urls_from_text,
    find_task_link_index,
    format_task_links_display,
    normalize_task_url,
    parse_link_remainder,
    restore_url_case,
    sanitize_task_links,
)
from tasks.task_schemas import TaskV2Model


TIMESTAMP = "2026-08-27 17:15:00"


@pytest.mark.unit
@pytest.mark.tasks
@pytest.mark.parametrize(
    "raw, expected",
    [
        ("https://example.com/form", "https://example.com/form"),
        ("http://example.com/a", "http://example.com/a"),
        ("<https://example.com/form>", "https://example.com/form"),
        ("https://example.com/form.", "https://example.com/form"),
        ("www.example.com/form", "https://www.example.com/form"),
        ("javascript:alert(1)", None),
        ("not-a-url", None),
        ("", None),
    ],
)
def test_normalize_task_url(raw, expected):
    assert normalize_task_url(raw) == expected


@pytest.mark.unit
@pytest.mark.tasks
def test_sanitize_task_links_dedupes_and_drops_invalid():
    cleaned = sanitize_task_links(
        [
            "https://example.com/a",
            {"url": "https://example.com/a", "label": "dup"},
            {"url": "https://example.com/b", "label": "Portal"},
            "javascript:alert(1)",
            "www.example.com/c",
        ]
    )
    assert cleaned == [
        {"url": "https://example.com/a", "label": ""},
        {"url": "https://example.com/b", "label": "Portal"},
        {"url": "https://www.example.com/c", "label": ""},
    ]


@pytest.mark.unit
@pytest.mark.tasks
def test_extract_urls_from_text_strips_links_from_title():
    urls, remainder = extract_urls_from_text(
        "fill out this form https://example.com/Form tomorrow"
    )
    assert urls == ["https://example.com/Form"]
    assert remainder == "fill out this form tomorrow"


@pytest.mark.unit
@pytest.mark.tasks
def test_parse_link_remainder_uses_words_before_url_as_label():
    parsed = parse_link_remainder("portal https://example.com/form")
    assert parsed == {
        "url": "https://example.com/form",
        "label": "portal",
    }


@pytest.mark.unit
@pytest.mark.tasks
def test_restore_url_case_prefers_original_message_spelling():
    restored = restore_url_case(
        "https://example.com/form",
        "add link to task 1 https://example.com/Form",
    )
    assert restored == "https://example.com/Form"


@pytest.mark.unit
@pytest.mark.tasks
def test_find_task_link_index_matches_label_or_url():
    links = [
        {"url": "https://example.com/a", "label": "portal"},
        {"url": "https://example.com/b", "label": ""},
    ]
    assert find_task_link_index(links, "portal") == 0
    assert find_task_link_index(links, "https://example.com/b") == 1
    assert find_task_link_index(links, "missing") is None


@pytest.mark.unit
@pytest.mark.tasks
def test_format_task_links_display_includes_labels():
    text = format_task_links_display(
        [{"url": "https://example.com/a", "label": "portal"}]
    )
    assert "**Links:**" in text
    assert "portal: https://example.com/a" in text


@pytest.mark.unit
@pytest.mark.tasks
def test_task_v2_model_defaults_missing_links_and_rejects_unknown_keys():
    task = TaskV2Model.model_validate(
        {
            "id": "task-1",
            "short_id": "tlink01",
            "kind": "task",
            "title": "Call dentist",
            "created_at": TIMESTAMP,
            "updated_at": TIMESTAMP,
        }
    )
    assert task.links == []
    dumped = task.model_dump(mode="json")
    assert dumped["links"] == []


@pytest.mark.unit
@pytest.mark.tasks
def test_task_v2_model_accepts_link_records():
    task = TaskV2Model.model_validate(
        {
            "id": "task-1",
            "short_id": "tlink01",
            "kind": "task",
            "title": "Call dentist",
            "created_at": TIMESTAMP,
            "updated_at": TIMESTAMP,
            "links": [{"url": "https://example.com/form", "label": "portal"}],
        }
    )
    assert task.links[0].url == "https://example.com/form"
    assert task.links[0].label == "portal"


@pytest.mark.unit
@pytest.mark.tasks
def test_append_task_link_adds_duplicate_and_invalid_statuses():
    from tasks import task_service

    task = {"id": "task-1", "links": []}
    with patch("tasks.get_task_by_id", return_value=task), patch(
        "tasks.update_task", return_value=True
    ) as mock_update:
        assert (
            task_service.append_task_link(
                "u1", "task-1", "https://example.com/a", "portal"
            )
            == "added"
        )
        mock_update.assert_called_once_with(
            "u1",
            "task-1",
            {"links": [{"url": "https://example.com/a", "label": "portal"}]},
        )

    task["links"] = [{"url": "https://example.com/a", "label": "portal"}]
    with patch("tasks.get_task_by_id", return_value=task), patch(
        "tasks.update_task", return_value=True
    ):
        assert (
            task_service.append_task_link("u1", "task-1", "https://example.com/a")
            == "duplicate"
        )

    assert task_service.append_task_link("u1", "task-1", "javascript:alert(1)") == "invalid"


@pytest.mark.unit
@pytest.mark.tasks
def test_append_task_link_enforces_max_links():
    from tasks import task_service

    task = {
        "id": "task-1",
        "links": [
            {"url": f"https://example.com/{index}", "label": ""}
            for index in range(MAX_TASK_LINKS)
        ],
    }
    with patch("tasks.get_task_by_id", return_value=task), patch(
        "tasks.update_task", return_value=True
    ):
        assert (
            task_service.append_task_link("u1", "task-1", "https://example.com/new")
            == "limit"
        )


@pytest.mark.unit
@pytest.mark.tasks
def test_remove_task_link_by_label():
    from tasks import task_service

    task = {
        "id": "task-1",
        "links": [{"url": "https://example.com/a", "label": "portal"}],
    }
    with patch("tasks.get_task_by_id", return_value=task), patch(
        "tasks.update_task", return_value=True
    ) as mock_update:
        assert task_service.remove_task_link("u1", "task-1", "portal") == "removed"
        mock_update.assert_called_once_with("u1", "task-1", {"links": []})


@pytest.mark.unit
@pytest.mark.tasks
def test_build_task_link_rejects_empty_url():
    assert build_task_link("") is None
    assert build_task_link(None) is None
