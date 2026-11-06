"""Repeatable local routing profile; provider and delivery latency are excluded."""

import cProfile
import io
import pstats
import statistics
import time
from unittest.mock import Mock

import pytest

from communication.message_processing.conversation_flow_manager import conversation_manager
from tests.behavior.test_communication_interaction_manager_behavior import (
    _create_fast_interaction_manager,
)
from tests.test_helpers.test_utilities import TestUserFactory
from core.logger import get_component_logger

logger = get_component_logger(__name__)


@pytest.mark.slow
@pytest.mark.behavior
@pytest.mark.communication
@pytest.mark.parametrize("redundant_setup", [True, False], ids=["before", "after"])
@pytest.mark.parametrize("channel", ["discord", "email"])
def test_local_message_processing_profile(test_data_dir, monkeypatch, redundant_setup, channel):
    """Measure real local handlers with isolated storage and deterministic chat."""
    import core.config as config

    monkeypatch.setattr(config, "AI_ACTION_PLANNER_ENABLED", False)
    user_id = "test-message-profile"
    assert TestUserFactory.create_basic_user(user_id, test_data_dir=test_data_dir)
    user_id = TestUserFactory.get_test_user_id_by_label(user_id, test_data_dir)
    assert user_id
    from tasks import task_service
    from tasks import task_data_handlers

    task_id = task_service.create_task(user_id, title="Profile fixture task")
    assert task_id
    original_load = task_data_handlers._load_v2_tasks
    if redundant_setup:
        def load_with_previous_setup(uid):
            task_data_handlers.ensure_task_directory(uid)
            return original_load(uid)
        monkeypatch.setattr(task_data_handlers, "_load_v2_tasks", load_with_previous_setup)
    manager = _create_fast_interaction_manager()
    # Start each request outside an active flow so workloads remain comparable.
    workloads = ("list tasks", f"complete task {task_id}", "start checkin", "zzzz")
    profile = cProfile.Profile()
    delivery = Mock()
    for message in workloads:
        samples = []
        for iteration in range(15):
            conversation_manager.user_states.pop(user_id, None)
            if message.startswith("complete task") and iteration:
                assert task_service.restore_task(user_id, task_id)
            start = time.perf_counter()
            response = manager.handle_message(user_id, message, channel)
            elapsed = (time.perf_counter() - start) * 1000
            assert response is not None and response.message
            delivery(user_id, response, channel)
            if message.startswith("complete task"):
                assert any(task["id"] == task_id for task in task_service.load_completed_tasks(user_id))
            if iteration >= 5:
                samples.append(elapsed)
        logger.info(f"PROFILE {channel} before={redundant_setup} {message!r}: median_ms={statistics.median(samples):.3f} "
              f"p95_ms={sorted(samples)[9]:.3f}")
        conversation_manager.user_states.pop(user_id, None)
        if message.startswith("complete task"):
            assert task_service.restore_task(user_id, task_id)
        profile.enable()
        manager.handle_message(user_id, message, channel)
        profile.disable()
    output = io.StringIO()
    pstats.Stats(profile, stream=output).sort_stats("cumulative").print_stats(25)
    logger.info(output.getvalue())
    assert delivery.call_count == 60
    assert all(call.args[2] == channel for call in delivery.call_args_list)
    conversation_manager.user_states.pop(user_id, None)
