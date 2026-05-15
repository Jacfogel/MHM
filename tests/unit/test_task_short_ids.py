"""Unit tests for canonical v2 task short IDs (no-dash, stable, lookup)."""

import pytest

from storage.user_data_v2_base import generate_short_id
from tasks.task_data_manager import _task_matches_identifier

pytestmark = [pytest.mark.unit, pytest.mark.core]


@pytest.mark.unit
@pytest.mark.core
def test_generate_short_id_task_shape_and_stability():
    task_uuid = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    sid = generate_short_id(task_uuid, "task", length=6)
    assert sid.startswith("t")
    assert "-" not in sid
    assert len(sid) == 7
    assert sid == generate_short_id(task_uuid, "task", length=6)
    assert sid.islower()


@pytest.mark.unit
@pytest.mark.core
def test_task_matches_identifier_uuid_and_short_id():
    tid = "bbbbbbbb-bbbb-4bbb-bbbb-bbbbbbbbbbbb"
    short = generate_short_id(tid, "task", length=6)
    task = {"id": tid, "short_id": short, "title": "Example"}
    assert _task_matches_identifier(task, tid) is True
    assert _task_matches_identifier(task, tid.upper()) is True
    assert _task_matches_identifier(task, short) is True
    assert _task_matches_identifier(task, short.upper()) is True
    assert _task_matches_identifier(task, "nope") is False
