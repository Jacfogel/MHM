"""Unit tests for hourly service status metric collection."""

from unittest.mock import Mock, patch

import pytest

from core.service import MHMService


pytestmark = [pytest.mark.core]


@pytest.mark.unit
@pytest.mark.core
def test_collect_service_status_metrics_uses_live_manager_apis():
    """Status logging should count jobs, users, and channels from real APIs."""
    service = MHMService()
    service.scheduler_manager = Mock()
    service.scheduler_manager.get_active_job_count.return_value = 12
    service.communication_manager = Mock()
    service.communication_manager.get_active_channels.return_value = ["email", "discord"]

    with patch("core.service.get_all_user_ids", return_value=["u1", "u2", "u3"]):
        metrics = service._collect_service_status_metrics(60)

    assert "60m uptime" in metrics
    assert "12 active jobs" in metrics
    assert "3 users" in metrics
    assert "2 channels" in metrics


@pytest.mark.unit
@pytest.mark.core
def test_collect_service_status_metrics_without_managers_still_counts_users():
    """Missing scheduler/channel managers should omit those metrics, not invent zeros."""
    service = MHMService()
    service.scheduler_manager = None
    service.communication_manager = None

    with patch("core.service.get_all_user_ids", return_value=["u1"]):
        metrics = service._collect_service_status_metrics(5)

    assert "5m uptime" in metrics
    assert "1 users" in metrics
    assert not any("jobs" in item for item in metrics)
    assert not any("channels" in item for item in metrics)


@pytest.mark.unit
@pytest.mark.core
def test_collect_service_status_metrics_ignores_legacy_missing_methods():
    """Do not report 0 jobs/channels just because old method names are absent."""
    service = MHMService()
    service.scheduler_manager = Mock(spec=["get_active_job_count"])
    service.scheduler_manager.get_active_job_count.return_value = 4
    service.communication_manager = Mock(spec=["get_active_channels"])
    service.communication_manager.get_active_channels.return_value = ["discord"]

    with patch("core.service.get_all_user_ids", return_value=["u1", "u2"]):
        metrics = service._collect_service_status_metrics(120)

    joined = ", ".join(metrics)
    assert "4 active jobs" in joined
    assert "2 users" in joined
    assert "1 channels" in joined
    assert "0 active jobs" not in joined
    assert "0 users" not in joined
    assert "0 channels" not in joined
