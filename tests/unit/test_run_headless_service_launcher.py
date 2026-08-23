"""Unit tests for the headless service launcher CLI."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import run_headless_service


def _manager(**methods: object) -> MagicMock:
    manager = MagicMock()
    for name, value in methods.items():
        setattr(manager, name, value)
    return manager


@pytest.mark.unit
@pytest.mark.core
def test_main_start_delegates_and_returns_0():
    manager = _manager(start_headless_service=MagicMock(return_value=True))
    with (
        patch.object(run_headless_service, "setup_logging"),
        patch.object(run_headless_service, "get_component_logger", return_value=MagicMock()),
        patch.object(run_headless_service, "HeadlessServiceManager", return_value=manager),
    ):
        assert run_headless_service.main(["start"]) == 0
    manager.start_headless_service.assert_called_once()


@pytest.mark.unit
@pytest.mark.core
def test_main_start_failure_returns_1():
    manager = _manager(start_headless_service=MagicMock(return_value=False))
    with (
        patch.object(run_headless_service, "setup_logging"),
        patch.object(run_headless_service, "get_component_logger", return_value=MagicMock()),
        patch.object(run_headless_service, "HeadlessServiceManager", return_value=manager),
    ):
        assert run_headless_service.main(["start"]) == 1


@pytest.mark.unit
@pytest.mark.core
def test_main_stop_delegates_and_returns_0():
    manager = _manager(stop_headless_service=MagicMock(return_value=True))
    with (
        patch.object(run_headless_service, "setup_logging"),
        patch.object(run_headless_service, "get_component_logger", return_value=MagicMock()),
        patch.object(run_headless_service, "HeadlessServiceManager", return_value=manager),
    ):
        assert run_headless_service.main(["stop"]) == 0
    manager.stop_headless_service.assert_called_once()


@pytest.mark.unit
@pytest.mark.core
def test_main_status_delegates_without_starting_a_process():
    manager = _manager(
        get_headless_service_status=MagicMock(return_value=(True, 4242))
    )
    with (
        patch.object(run_headless_service, "setup_logging"),
        patch.object(run_headless_service, "get_component_logger", return_value=MagicMock()),
        patch.object(run_headless_service, "HeadlessServiceManager", return_value=manager),
    ):
        assert run_headless_service.main(["status"]) == 0
    manager.get_headless_service_status.assert_called_once()
    manager.start_headless_service.assert_not_called()
