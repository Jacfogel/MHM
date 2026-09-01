"""Unit tests for pronoun task references such as 'that'."""

import uuid
from datetime import timedelta

import pytest

from core.response_tracking import store_chat_interaction
from core.time_utilities import TIMESTAMP_FULL, format_timestamp, now_datetime_full
from tasks import complete_task, create_task, load_active_tasks, save_active_tasks
from tasks.task_reference import (
    is_pronoun_task_identifier,
    message_uses_task_pronoun,
    resolve_lookup_identifier,
    resolve_pronoun_task,
)
from tests.test_helpers.test_utilities import TestUserFactory


pytestmark = [pytest.mark.unit, pytest.mark.tasks]


def _old_timestamp() -> str:
    return format_timestamp(now_datetime_full() - timedelta(hours=2), TIMESTAMP_FULL)


@pytest.mark.parametrize(
    "identifier, expected",
    [
        ("that", True),
        ("THAT", True),
        ("it", True),
        ("this task", True),
        ("dentist", False),
        ("1", False),
        ("", False),
        (None, False),
    ],
)
def test_is_pronoun_task_identifier(identifier, expected):
    assert is_pronoun_task_identifier(identifier) is expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("make that due tomorrow", True),
        ("that's urgent", True),
        ("mark that done", True),
        ("add a note to that: bring the card", True),
        ("that's okay", False),
        ("that's a lot", False),
        ("I can't deal with that", False),
    ],
)
def test_message_uses_task_pronoun(text, expected):
    assert message_uses_task_pronoun(text) is expected


def test_resolve_pronoun_task_with_one_active_task(test_data_dir):
    user_id = "pronoun-one-task"
    TestUserFactory.create_basic_user(
        user_id, enable_tasks=True, test_data_dir=test_data_dir
    )
    create_task(user_id, title="call the dentist")

    task = resolve_pronoun_task(user_id)

    assert task is not None
    assert task["title"] == "call the dentist"


def test_resolve_pronoun_task_prefers_title_in_recent_chat(test_data_dir):
    user_id = "pronoun-chat-title"
    TestUserFactory.create_basic_user(
        user_id, enable_tasks=True, test_data_dir=test_data_dir
    )
    create_task(user_id, title="pack the hiking bag")
    create_task(user_id, title="call the dentist")
    tasks = load_active_tasks(user_id)
    old = _old_timestamp()
    for task in tasks:
        task["created_at"] = old
        task["updated_at"] = old
    save_active_tasks(user_id, tasks)
    store_chat_interaction(
        user_id,
        "I keep forgetting to pack the hiking bag for Saturday",
        "That sounds stressful.",
        context_used=True,
    )

    task = resolve_pronoun_task(user_id)

    assert task is not None
    assert task["title"] == "pack the hiking bag"


def test_resolve_pronoun_task_asks_when_old_tasks_are_ambiguous(test_data_dir):
    user_id = "pronoun-ambiguous"
    TestUserFactory.create_basic_user(
        user_id, enable_tasks=True, test_data_dir=test_data_dir
    )
    create_task(user_id, title="pack the hiking bag")
    create_task(user_id, title="call the dentist")
    tasks = load_active_tasks(user_id)
    old = _old_timestamp()
    for task in tasks:
        task["created_at"] = old
        task["updated_at"] = old
    save_active_tasks(user_id, tasks)

    assert resolve_pronoun_task(user_id) is None
    assert resolve_lookup_identifier(user_id, "that") is None


def test_resolve_pronoun_task_does_not_use_leftover_after_complete(test_data_dir):
    user_id = f"pronoun-after-complete-{uuid.uuid4()}"
    TestUserFactory.create_basic_user(
        user_id, enable_tasks=True, test_data_dir=test_data_dir
    )
    first = create_task(user_id, title="email the school")
    second = create_task(user_id, title="water the plants")
    assert complete_task(user_id, second)

    assert resolve_pronoun_task(user_id) is None
    leftover = load_active_tasks(user_id)
    assert [task["id"] for task in leftover] == [first]


def test_resolve_pronoun_task_ignores_single_stale_task(test_data_dir):
    user_id = "pronoun-stale-only"
    TestUserFactory.create_basic_user(
        user_id, enable_tasks=True, test_data_dir=test_data_dir
    )
    create_task(user_id, title="email the school")
    tasks = load_active_tasks(user_id)
    old = _old_timestamp()
    for task in tasks:
        task["created_at"] = old
        task["updated_at"] = old
    save_active_tasks(user_id, tasks)

    assert resolve_pronoun_task(user_id) is None


def test_resolve_lookup_identifier_leaves_real_names_alone(test_data_dir):
    user_id = "pronoun-real-name"
    TestUserFactory.create_basic_user(
        user_id, enable_tasks=True, test_data_dir=test_data_dir
    )

    assert resolve_lookup_identifier(user_id, "dentist") == "dentist"
    assert resolve_lookup_identifier(user_id, "1") == "1"
