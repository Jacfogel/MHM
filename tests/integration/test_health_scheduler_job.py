"""Integration tests for scheduled Google Health sync registration."""

from unittest.mock import patch

import pytest

import schedule

pytestmark = [pytest.mark.scheduler]


@pytest.mark.integration
def test_register_health_sync_jobs_when_disabled():
    schedule.clear()
    with patch("scheduler.health_sync_jobs.GOOGLE_HEALTH_ENABLED", False):
        from scheduler.health_sync_jobs import register_health_sync_jobs

        register_health_sync_jobs()
    assert len(schedule.jobs) == 0


@pytest.mark.integration
def test_register_health_sync_jobs_when_enabled():
    schedule.clear()
    with patch("scheduler.health_sync_jobs.GOOGLE_HEALTH_ENABLED", True), patch(
        "core.config.parse_google_health_sync_times",
        return_value=["06:30", "18:00"],
    ):
        from scheduler.health_sync_jobs import register_health_sync_jobs

        register_health_sync_jobs()
    assert len(schedule.jobs) >= 1
    schedule.clear()


@pytest.mark.integration
def test_scheduled_sync_skips_in_testing_mode(monkeypatch):
    monkeypatch.setenv("MHM_TESTING", "1")
    with patch("scheduler.health_sync_jobs.GOOGLE_HEALTH_ENABLED", True), patch(
        "scheduler.health_sync_jobs.sync_all_enabled_users"
    ) as mock_sync:
        from scheduler.health_sync_jobs import run_scheduled_health_sync

        run_scheduled_health_sync()
        mock_sync.assert_not_called()
