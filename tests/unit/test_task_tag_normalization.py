"""Unit tests for shared task tag normalization."""

import pytest

import storage.user_item_storage as user_item_storage
from tasks import task_service
from tasks.task_data_manager import create_task, get_task_by_id, update_task
from tasks.task_tag_helpers import normalize_task_tag_filter, sanitize_task_tags


@pytest.fixture
def task_user_id():
    return "test-user-tag-normalization"


@pytest.fixture(autouse=True)
def _isolate_task_user_data_dir(monkeypatch, test_path_factory, task_user_id):
    root = test_path_factory

    def _fake_get_user_data_dir(_uid: str) -> str:
        return root

    monkeypatch.setattr(user_item_storage, "get_user_data_dir", _fake_get_user_data_dir)


@pytest.mark.unit
@pytest.mark.tasks
def test_sanitize_task_tags_normalizes_and_deduplicates():
    assert sanitize_task_tags(["Work", "#work", "Health"]) == ["work", "health"]


@pytest.mark.unit
@pytest.mark.tasks
def test_sanitize_task_tags_rejects_invalid_characters():
    assert sanitize_task_tags(["valid-tag", "bad tag", "also_ok"]) == [
        "valid-tag",
        "also_ok",
    ]


@pytest.mark.unit
@pytest.mark.tasks
def test_normalize_task_tag_filter_strips_hash_and_case():
    assert normalize_task_tag_filter("#Work") == "work"


@pytest.mark.unit
@pytest.mark.tasks
def test_filter_tasks_tag_filter_is_case_insensitive():
    tasks = [
        {"id": "1", "title": "A", "tags": ["Work"]},
        {"id": "2", "title": "B", "tags": ["personal"]},
    ]
    filtered = task_service.filter_tasks("u1", tasks, None, None, "#work")
    assert [task["id"] for task in filtered] == ["1"]


@pytest.mark.unit
@pytest.mark.tasks
def test_create_task_stores_normalized_tags(task_user_id):
    task_id = create_task(
        task_user_id,
        "Tagged task",
        tags=["#Groceries", "WORK", "work"],
    )
    assert task_id

    tasks = task_service.load_active_tasks(task_user_id)
    task = next(t for t in tasks if t["id"] == task_id)
    assert task["tags"] == ["groceries", "work"]


@pytest.mark.unit
@pytest.mark.tasks
def test_update_task_normalizes_tags(task_user_id):
    task_id = create_task(task_user_id, "Update tags", tags=["home"])
    assert task_id

    assert update_task(task_user_id, task_id, {"tags": ["#Health", "HEALTH"]}) is True

    task = get_task_by_id(task_user_id, task_id)
    assert task is not None
    assert task["tags"] == ["health"]
