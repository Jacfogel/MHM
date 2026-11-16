"""Behavior tests for persisted task dependency relationships."""

import pytest

from tasks import (
    complete_task,
    create_task,
    delete_task,
    get_task_by_id,
    set_task_dependencies,
)

pytestmark = [pytest.mark.unit, pytest.mark.tasks]


def test_dependency_relationships_are_persisted_in_both_directions(test_data_dir):
    user_id = "dependency-persistence"
    first = create_task(user_id, "Choose paint")
    second = create_task(user_id, "Buy brushes")
    dependent = create_task(user_id, "Paint the room")

    assert set_task_dependencies(user_id, dependent, [first, second]) is True

    saved_dependent = get_task_by_id(user_id, dependent)
    assert saved_dependent["blocked_by"] == [first, second]
    assert get_task_by_id(user_id, first)["blocks"] == [dependent]
    assert get_task_by_id(user_id, second)["blocks"] == [dependent]


def test_dependency_update_accepts_short_ids_and_replaces_old_edges(test_data_dir):
    user_id = "dependency-short-ids"
    first = create_task(user_id, "First")
    second = create_task(user_id, "Second")
    dependent = create_task(user_id, "Dependent")
    first_short_id = get_task_by_id(user_id, first)["short_id"]

    assert set_task_dependencies(user_id, dependent, [first_short_id]) is True
    assert set_task_dependencies(user_id, dependent, [second]) is True

    assert get_task_by_id(user_id, dependent)["blocked_by"] == [second]
    assert get_task_by_id(user_id, first)["blocks"] == []
    assert get_task_by_id(user_id, second)["blocks"] == [dependent]


def test_dependency_update_rejects_self_missing_and_circular_edges(test_data_dir):
    user_id = "dependency-cycles"
    first = create_task(user_id, "First")
    second = create_task(user_id, "Second")
    third = create_task(user_id, "Third")

    assert set_task_dependencies(user_id, first, [first]) is False
    assert set_task_dependencies(user_id, first, ["missing-task"]) is False
    assert set_task_dependencies(user_id, second, [first]) is True
    assert set_task_dependencies(user_id, third, [second]) is True
    assert set_task_dependencies(user_id, first, [third]) is False

    assert get_task_by_id(user_id, first)["blocked_by"] == []
    assert get_task_by_id(user_id, second)["blocked_by"] == [first]
    assert get_task_by_id(user_id, third)["blocked_by"] == [second]


def test_completing_prerequisites_unblocks_only_satisfied_edges(test_data_dir):
    user_id = "dependency-completion"
    first = create_task(user_id, "Choose paint")
    second = create_task(user_id, "Buy brushes")
    dependent = create_task(user_id, "Paint the room")
    assert set_task_dependencies(user_id, dependent, [first, second]) is True

    assert complete_task(user_id, first) is True
    assert get_task_by_id(user_id, dependent)["blocked_by"] == [second]

    assert complete_task(user_id, second) is True
    ready = get_task_by_id(user_id, dependent)
    assert ready["blocked_by"] == []
    assert ready["status"] == "active"


def test_deleting_prerequisite_unblocks_dependents(test_data_dir):
    user_id = "dependency-deletion"
    prerequisite = create_task(user_id, "Obsolete prerequisite")
    dependent = create_task(user_id, "Continue project")
    assert set_task_dependencies(user_id, dependent, [prerequisite]) is True

    assert delete_task(user_id, prerequisite) is True

    assert get_task_by_id(user_id, dependent)["blocked_by"] == []

