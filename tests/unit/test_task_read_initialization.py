"""Task reads initialize missing storage and always see subsequent writes."""

import uuid
from pathlib import Path

import pytest

from tasks.task_data_handlers import (
    load_active_tasks,
    load_completed_tasks,
    save_task_lists,
)
from tasks.task_service import create_task, complete_task


@pytest.mark.unit
@pytest.mark.tasks
@pytest.mark.parametrize("reader", [load_active_tasks, load_completed_tasks])
def test_first_read_initializes_missing_task_file(test_data_dir, reader):
    user_id = str(uuid.uuid4())
    assert reader(user_id) == []
    assert (Path(test_data_dir) / "users" / user_id / "tasks" / "tasks.json").is_file()


@pytest.mark.unit
@pytest.mark.tasks
def test_reads_observe_writes_and_keep_users_separate(test_data_dir):
    user_id, other_id = str(uuid.uuid4()), str(uuid.uuid4())
    assert load_active_tasks(user_id) == []
    task_id = create_task(user_id, title="Fresh task")
    assert task_id
    assert [task["id"] for task in load_active_tasks(user_id)] == [task_id]
    assert load_active_tasks(other_id) == []
    assert complete_task(user_id, task_id)
    assert load_active_tasks(user_id) == []
    assert [task["id"] for task in load_completed_tasks(user_id)] == [task_id]
    assert save_task_lists(user_id, [], [])
    assert load_completed_tasks(user_id) == []
