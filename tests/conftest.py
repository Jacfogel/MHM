"""
Pytest configuration and shared fixtures for MHM testing framework.

This file provides:
- Test configuration
- Shared fixtures for common test data
- Temporary directory management
- Mock configurations for testing
"""

import pytest
import os
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import Mock, patch
import sys

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import core modules for testing
from core.config import BASE_DATA_DIR, USER_INFO_DIR_PATH
from core.logger import setup_logging

@pytest.fixture(scope="session")
def test_data_dir():
    """Create a temporary test data directory for all tests."""
    temp_dir = tempfile.mkdtemp(prefix="mhm_test_")
    yield temp_dir
    # Cleanup after all tests
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture(scope="function")
def mock_config(test_data_dir):
    """Mock configuration for testing with proper test data directory."""
    # Patch the configuration to use the test data directory
    with patch('core.config.BASE_DATA_DIR', test_data_dir), \
         patch('core.config.USER_INFO_DIR_PATH', os.path.join(test_data_dir, 'users')), \
         patch('core.config.DEFAULT_MESSAGES_DIR_PATH', os.path.join(test_data_dir, 'default_messages')):
        yield

@pytest.fixture(scope="function")
def mock_user_data(test_data_dir, mock_config):
    """Create mock user data for testing."""
    user_id = "test-user-123"
    user_dir = os.path.join(test_data_dir, "users", user_id)
    os.makedirs(user_dir, exist_ok=True)
    
    # Create mock account.json
    account_data = {
        "user_id": user_id,
        "internal_username": "testuser",
        "account_status": "active",
        "chat_id": "",
        "phone": "",
        "email": "",
        "discord_user_id": "",
        "created_at": "2025-01-01T12:00:00Z",
        "updated_at": "2025-01-01T12:00:00Z"
    }
    
    # Create mock preferences.json
    preferences_data = {
        "channel": {
            "type": "email"
        },
        "categories": {
            "motivational": True,
            "health": True,
            "fun_facts": False
        },
        "checkin_settings": {
            "enabled": False
        },
        "task_settings": {
            "enabled": False
        }
    }
    
    # Create mock user_context.json
    context_data = {
        "preferred_name": "",
        "pronouns": [],
        "date_of_birth": "",
        "custom_fields": {
            "health_conditions": [],
            "medications_treatments": [],
            "reminders_needed": []
        },
        "interests": [],
        "goals": [],
        "loved_ones": [],
        "activities_for_encouragement": [],
        "notes_for_ai": [],
        "created_at": "2025-01-01T12:00:00Z",
        "last_updated": "2025-01-01T12:00:00Z"
    }
    
    # Save mock data
    with open(os.path.join(user_dir, "account.json"), "w") as f:
        json.dump(account_data, f, indent=2)
    
    with open(os.path.join(user_dir, "preferences.json"), "w") as f:
        json.dump(preferences_data, f, indent=2)
    
    with open(os.path.join(user_dir, "user_context.json"), "w") as f:
        json.dump(context_data, f, indent=2)
    
    return {
        "user_id": user_id,
        "user_dir": user_dir,
        "account_data": account_data,
        "preferences_data": preferences_data,
        "context_data": context_data
    }

@pytest.fixture(scope="function")
def mock_logger():
    """Mock logger for testing."""
    with patch('core.logger.get_logger') as mock_logger:
        mock_logger.return_value = Mock()
        yield mock_logger

@pytest.fixture(scope="function")
def temp_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
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
        "timestamp": "2025-01-01T12:00:00Z"
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
        "updated_at": "2025-01-01T12:00:00Z"
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
        "active": True
    }

# Configure pytest
def pytest_configure(config):
    """Configure pytest for MHM testing."""
    # Set up logging for tests
    setup_logging()
    
    # Add custom markers
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "ai: mark test as requiring AI functionality"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add default markers."""
    for item in items:
        # Add unit marker by default if no marker is present
        if not any(item.iter_markers()):
            item.add_marker(pytest.mark.unit) 