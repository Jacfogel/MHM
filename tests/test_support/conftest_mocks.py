"""Pytest plugin: mock and temp-file fixtures for MHM tests.

Loaded via pytest_plugins in tests/conftest.py. Fixture names remain in the same
namespace so tests and development_tools/conftest overrides continue to work.
"""

import os
import tempfile

import pytest
from unittest.mock import Mock, patch

from tests.conftest import tests_data_dir

# Use same tmp dir as root conftest for temp_file fixture
tests_data_tmp_dir = tests_data_dir / "tmp"


@pytest.fixture(scope="function")
def mock_logger():
    """Mock logger for testing."""
    with patch("core.logger.get_logger") as mock_logger:
        mock_logger.return_value = Mock()
        yield mock_logger


@pytest.fixture(scope="function")
def temp_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(
        mode="w+", delete=False, dir=str(tests_data_tmp_dir)
    ) as f:
        yield f.name
    # Cleanup
    os.unlink(f.name)


@pytest.fixture(scope="function")
def mock_ai_response():
    """Mock AI response for testing."""
    return {
        "response": "This is a test AI response.",
        "confidence": 0.85,
        "model": "test-model",
        "timestamp": "2025-01-01T12:00:00Z",
    }


@pytest.fixture(scope="function")
def mock_task_data():
    """Mock task data for testing."""
    return {
        "task_id": "test-task-123",
        "title": "Test Task",
        "description": "This is a test task",
        "priority": "medium",
        "due_date": "2025-01-15",
        "completed": False,
        "created_at": "2025-01-01T12:00:00Z",
        "updated_at": "2025-01-01T12:00:00Z",
    }


@pytest.fixture(scope="function")
def mock_message_data():
    """Mock message data for testing."""
    return {
        "message_id": "test-message-123",
        "text": "This is a test message",
        "category": "motivational",
        "days": ["monday", "wednesday", "friday"],
        "time_periods": ["18:00-20:00"],
        "active": True,
    }


@pytest.fixture(scope="function")
def mock_service_data():
    """Mock service data for testing."""
    return {
        "service_id": "test-service-123",
        "name": "Test Service",
        "status": "running",
        "pid": 12345,
        "start_time": "2025-01-01T12:00:00Z",
        "config": {"port": 8080, "host": "localhost"},
    }


@pytest.fixture(scope="function")
def mock_communication_data():
    """Mock communication data for testing."""
    return {
        "message_id": "test-msg-123",
        "user_id": "test-user-123",
        "channel": "email",
        "content": "Test message content",
        "sent_at": "2025-01-01T12:00:00Z",
        "status": "sent",
    }


@pytest.fixture(scope="function")
def mock_schedule_data():
    """Mock schedule data for testing."""
    return {
        "category": "motivational",
        "periods": {
            "morning": {
                "start_time": "08:00",
                "end_time": "10:00",
                "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                "active": True,
            },
            "evening": {
                "start_time": "18:00",
                "end_time": "20:00",
                "days": ["monday", "wednesday", "friday"],
                "active": True,
            },
        },
    }
