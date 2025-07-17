"""
Pytest configuration and shared fixtures for MHM testing framework.

This file provides:
- Test configuration
- Shared fixtures for common test data
- Temporary directory management
- Mock configurations for testing
- Dedicated testing log configuration
"""

import pytest
import os
import tempfile
import shutil
import json
import logging
from pathlib import Path
from unittest.mock import Mock, patch
import sys
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# CRITICAL: Set up logging isolation BEFORE importing any core modules
def setup_logging_isolation():
    """Set up logging isolation before any core modules are imported."""
    # Remove all handlers from root logger to prevent test logs from going to app.log
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        handler.close()
        root_logger.removeHandler(handler)
    
    # Also clear any handlers from the main application logger if it exists
    main_logger = logging.getLogger("mhm")
    for handler in main_logger.handlers[:]:
        handler.close()
        main_logger.removeHandler(handler)
    
    # Set propagate to False for main loggers to prevent test logs from bubbling up
    root_logger.propagate = False
    main_logger.propagate = False

# Set up logging isolation immediately
setup_logging_isolation()

# Set environment variable to indicate we're running tests
os.environ['MHM_TESTING'] = '1'

# Import core modules for testing (after logging isolation is set up)
from core.config import BASE_DATA_DIR, USER_INFO_DIR_PATH

# Set up dedicated testing logging
def setup_test_logging():
    """Set up dedicated logging for tests with complete isolation from main app logging."""
    # Create test logs directory
    test_logs_dir = Path(project_root) / "test_logs"
    test_logs_dir.mkdir(exist_ok=True)
    
    # Create test log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_log_file = test_logs_dir / f"test_run_{timestamp}.log"
    
    # Configure test logger
    test_logger = logging.getLogger("mhm_tests")
    test_logger.setLevel(logging.DEBUG)
    
    # Clear any existing handlers
    test_logger.handlers.clear()
    
    # File handler for test logs
    file_handler = logging.FileHandler(test_log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    # Console handler for test output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # Less verbose for console
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to test logger only
    test_logger.addHandler(file_handler)
    test_logger.addHandler(console_handler)
    
    # Prevent test logger from propagating to root logger
    test_logger.propagate = False
    
    return test_logger, test_log_file

# Set up test logging
test_logger, test_log_file = setup_test_logging()

@pytest.fixture(scope="session", autouse=True)
def isolate_logging():
    """Ensure complete logging isolation during tests to prevent test logs from appearing in main app.log."""
    # Store original handlers
    root_logger = logging.getLogger()
    original_root_handlers = root_logger.handlers[:]
    
    main_logger = logging.getLogger("mhm")
    original_main_handlers = main_logger.handlers[:]
    
    # Remove all handlers from main loggers to prevent test logs from going to app.log
    for handler in root_logger.handlers[:]:
        handler.close()
        root_logger.removeHandler(handler)
    
    for handler in main_logger.handlers[:]:
        handler.close()
        main_logger.removeHandler(handler)
    
    # Set propagate to False for main loggers to prevent test logs from bubbling up
    root_logger.propagate = False
    main_logger.propagate = False
    
    test_logger.info("Logging isolation activated - test logs will not appear in main app.log")
    
    yield
    
    # Restore original handlers after tests complete
    for handler in original_root_handlers:
        root_logger.addHandler(handler)
    
    for handler in original_main_handlers:
        main_logger.addHandler(handler)
    
    # Restore propagate settings
    root_logger.propagate = True
    main_logger.propagate = True
    
    test_logger.info("Logging isolation deactivated - main app logging restored")

@pytest.fixture(scope="session")
def test_data_dir():
    """Create a temporary test data directory for all tests."""
    temp_dir = tempfile.mkdtemp(prefix="mhm_test_")
    test_logger.info(f"Created test data directory: {temp_dir}")
    yield temp_dir
    # Cleanup after all tests
    shutil.rmtree(temp_dir, ignore_errors=True)
    test_logger.info(f"Cleaned up test data directory: {temp_dir}")

@pytest.fixture(scope="function")
def mock_config(test_data_dir):
    """Mock configuration for testing with proper test data directory."""
    test_logger.debug(f"Setting up mock config with test data dir: {test_data_dir}")
    # Patch the configuration to use the test data directory
    with patch('core.config.BASE_DATA_DIR', test_data_dir), \
         patch('core.config.USER_INFO_DIR_PATH', os.path.join(test_data_dir, 'users')), \
         patch('core.config.DEFAULT_MESSAGES_DIR_PATH', os.path.join(test_data_dir, 'default_messages')):
        yield

@pytest.fixture(scope="function")
def mock_user_data(test_data_dir, mock_config, request):
    """Create mock user data for testing with unique user ID for each test."""
    import uuid
    
    # Generate unique user ID for each test to prevent interference
    user_id = f"test-user-{uuid.uuid4().hex[:8]}"
    user_dir = os.path.join(test_data_dir, "users", user_id)
    os.makedirs(user_dir, exist_ok=True)
    
    test_logger.debug(f"Creating mock user data for user: {user_id}")
    
    # Create mock account.json with current timestamp
    current_time = datetime.now().isoformat() + "Z"
    account_data = {
        "user_id": user_id,
        "internal_username": f"testuser_{user_id[-4:]}",
        "account_status": "active",
        "chat_id": "",
        "phone": "",
        "email": f"test_{user_id[-4:]}@example.com",
        "discord_user_id": "",
        "created_at": current_time,
        "updated_at": current_time,
        "features": {
            "automated_messages": "disabled",
            "checkins": "disabled",
            "task_management": "disabled"
        }
    }
    
    # Create mock preferences.json - categories only included if automated_messages enabled
    preferences_data = {
        "channel": {
            "type": "email"
        },
        "checkin_settings": {
            "enabled": False,
            "frequency": "daily",
            "time": "09:00",
            "categories": ["mood", "energy", "sleep"]
        },
        "task_settings": {
            "enabled": False,
            "reminder_frequency": "daily",
            "reminder_time": "10:00"
        }
    }
    
    # Only add categories if automated_messages is enabled
    if account_data["features"]["automated_messages"] == "enabled":
        preferences_data["categories"] = ["motivational", "health", "quotes_to_ponder"]
    
    # Create mock user_context.json
    context_data = {
        "preferred_name": f"Test User {user_id[-4:]}",
        "pronouns": ["they/them"],
        "date_of_birth": "",
        "custom_fields": {
            "health_conditions": [],
            "medications_treatments": [],
            "reminders_needed": [],
            "gender_identity": "",
            "accessibility_needs": []
        },
        "interests": ["reading", "music"],
        "goals": ["Improve mental health", "Stay organized"],
        "loved_ones": [],
        "activities_for_encouragement": ["exercise", "socializing"],
        "notes_for_ai": ["Prefers gentle encouragement", "Responds well to structure"],
        "created_at": current_time,
        "last_updated": current_time
    }
    
    # Create mock daily_checkins.json
    checkins_data = {
        "checkins": [],
        "last_checkin_date": None,
        "streak_count": 0
    }
    
    # Create mock chat_interactions.json
    chat_data = {
        "interactions": [],
        "total_interactions": 0,
        "last_interaction": None
    }
    
    # Create messages directory and sent_messages.json only if automated_messages enabled
    messages_dir = os.path.join(user_dir, "messages")
    if account_data["features"]["automated_messages"] == "enabled":
        os.makedirs(messages_dir, exist_ok=True)
        
        sent_messages_data = {
            "messages": [],
            "total_sent": 0,
            "last_sent": None
        }
        
        with open(os.path.join(messages_dir, "sent_messages.json"), "w") as f:
            json.dump(sent_messages_data, f, indent=2)
    else:
        sent_messages_data = None
    
    # Save all mock data
    with open(os.path.join(user_dir, "account.json"), "w") as f:
        json.dump(account_data, f, indent=2)
    
    with open(os.path.join(user_dir, "preferences.json"), "w") as f:
        json.dump(preferences_data, f, indent=2)
    
    with open(os.path.join(user_dir, "user_context.json"), "w") as f:
        json.dump(context_data, f, indent=2)
    
    with open(os.path.join(user_dir, "daily_checkins.json"), "w") as f:
        json.dump(checkins_data, f, indent=2)
    
    with open(os.path.join(user_dir, "chat_interactions.json"), "w") as f:
        json.dump(chat_data, f, indent=2)
    
    test_logger.debug(f"Created complete mock user data files in: {user_dir}")
    
    # Store user_id for cleanup
    request.node.user_id = user_id
    
    return {
        "user_id": user_id,
        "user_dir": user_dir,
        "account_data": account_data,
        "preferences_data": preferences_data,
        "context_data": context_data,
        "checkins_data": checkins_data,
        "chat_data": chat_data,
        "sent_messages_data": sent_messages_data
    }

@pytest.fixture(scope="function")
def mock_user_data_with_messages(test_data_dir, mock_config, request):
    """Create mock user data for testing with automated_messages enabled and categories."""
    import uuid
    
    # Generate unique user ID for each test to prevent interference
    user_id = f"test-user-messages-{uuid.uuid4().hex[:8]}"
    user_dir = os.path.join(test_data_dir, "users", user_id)
    os.makedirs(user_dir, exist_ok=True)
    
    test_logger.debug(f"Creating mock user data with messages for user: {user_id}")
    
    # Create mock account.json with automated_messages enabled
    current_time = datetime.now().isoformat() + "Z"
    account_data = {
        "user_id": user_id,
        "internal_username": f"testuser_{user_id[-4:]}",
        "account_status": "active",
        "chat_id": "",
        "phone": "",
        "email": f"test_{user_id[-4:]}@example.com",
        "discord_user_id": "",
        "created_at": current_time,
        "updated_at": current_time,
        "features": {
            "automated_messages": "enabled",
            "checkins": "disabled",
            "task_management": "disabled"
        }
    }
    
    # Create mock preferences.json with categories (automated_messages enabled)
    preferences_data = {
        "channel": {
            "type": "email"
        },
        "categories": ["motivational", "health", "quotes_to_ponder"],
        "checkin_settings": {
            "enabled": False,
            "frequency": "daily",
            "time": "09:00",
            "categories": ["mood", "energy", "sleep"]
        },
        "task_settings": {
            "enabled": False,
            "reminder_frequency": "daily",
            "reminder_time": "10:00"
        }
    }
    
    # Create mock user_context.json
    context_data = {
        "preferred_name": f"Test User {user_id[-4:]}",
        "pronouns": ["they/them"],
        "date_of_birth": "",
        "custom_fields": {
            "health_conditions": [],
            "medications_treatments": [],
            "reminders_needed": [],
            "gender_identity": "",
            "accessibility_needs": []
        },
        "interests": ["reading", "music"],
        "goals": ["Improve mental health", "Stay organized"],
        "loved_ones": [],
        "activities_for_encouragement": ["exercise", "socializing"],
        "notes_for_ai": ["Prefers gentle encouragement", "Responds well to structure"],
        "created_at": current_time,
        "last_updated": current_time
    }
    
    # Create mock daily_checkins.json
    checkins_data = {
        "checkins": [],
        "last_checkin_date": None,
        "streak_count": 0
    }
    
    # Create mock chat_interactions.json
    chat_data = {
        "interactions": [],
        "total_interactions": 0,
        "last_interaction": None
    }
    
    # Create messages directory and sent_messages.json (automated_messages enabled)
    messages_dir = os.path.join(user_dir, "messages")
    os.makedirs(messages_dir, exist_ok=True)
    
    sent_messages_data = {
        "messages": [],
        "total_sent": 0,
        "last_sent": None
    }
    
    # Save all mock data
    with open(os.path.join(user_dir, "account.json"), "w") as f:
        json.dump(account_data, f, indent=2)
    
    with open(os.path.join(user_dir, "preferences.json"), "w") as f:
        json.dump(preferences_data, f, indent=2)
    
    with open(os.path.join(user_dir, "user_context.json"), "w") as f:
        json.dump(context_data, f, indent=2)
    
    with open(os.path.join(user_dir, "daily_checkins.json"), "w") as f:
        json.dump(checkins_data, f, indent=2)
    
    with open(os.path.join(user_dir, "chat_interactions.json"), "w") as f:
        json.dump(chat_data, f, indent=2)
    
    with open(os.path.join(messages_dir, "sent_messages.json"), "w") as f:
        json.dump(sent_messages_data, f, indent=2)
    
    test_logger.debug(f"Created complete mock user data with messages in: {user_dir}")
    
    # Store user_id for cleanup
    request.node.user_id = user_id
    
    return {
        "user_id": user_id,
        "user_dir": user_dir,
        "account_data": account_data,
        "preferences_data": preferences_data,
        "context_data": context_data,
        "checkins_data": checkins_data,
        "chat_data": chat_data,
        "sent_messages_data": sent_messages_data
    }

@pytest.fixture(scope="function")
def update_user_index_for_test(test_data_dir):
    """Helper fixture to update user index for test users."""
    def _update_index(user_id):
        try:
            from core.user_data_manager import update_user_index
            success = update_user_index(user_id)
            if success:
                test_logger.debug(f"Updated user index for test user: {user_id}")
            else:
                test_logger.warning(f"Failed to update user index for test user: {user_id}")
            return success
        except Exception as e:
            test_logger.warning(f"Error updating user index for test user {user_id}: {e}")
            return False
    
    return _update_index

@pytest.fixture(scope="function")
def cleanup_test_users(request, test_data_dir):
    """Clean up test users after each test."""
    yield  # Run the test
    
    # Cleanup after test
    try:
        # Clean up any test users created during the test
        if hasattr(request.node, 'user_id'):
            user_id = request.node.user_id
            user_dir = os.path.join(test_data_dir, "users", user_id)
            if os.path.exists(user_dir):
                shutil.rmtree(user_dir)
                test_logger.debug(f"Cleaned up test user: {user_id}")
        
        # Also clean up any other test users that might have been created
        users_dir = os.path.join(test_data_dir, "users")
        if os.path.exists(users_dir):
            for item in os.listdir(users_dir):
                item_path = os.path.join(users_dir, item)
                if os.path.isdir(item_path) and item.startswith("test-user-"):
                    shutil.rmtree(item_path)
                    test_logger.debug(f"Cleaned up test user directory: {item}")
                    
    except Exception as e:
        test_logger.warning(f"Error during test cleanup: {e}")

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

@pytest.fixture(scope="function")
def mock_service_data():
    """Mock service data for testing."""
    return {
        "service_id": "test-service-123",
        "name": "Test Service",
        "status": "running",
        "pid": 12345,
        "start_time": "2025-01-01T12:00:00Z",
        "config": {
            "port": 8080,
            "host": "localhost"
        }
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
        "status": "sent"
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
                "active": True
            },
            "evening": {
                "start_time": "18:00",
                "end_time": "20:00",
                "days": ["monday", "wednesday", "friday"],
                "active": True
            }
        }
    }

# Configure pytest
def pytest_configure(config):
    """Configure pytest for MHM testing."""
    test_logger.info("Configuring pytest for MHM testing")
    
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
    config.addinivalue_line(
        "markers", "service: mark test as testing service functionality"
    )
    config.addinivalue_line(
        "markers", "communication: mark test as testing communication channels"
    )
    config.addinivalue_line(
        "markers", "ui: mark test as testing UI components"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add default markers."""
    for item in items:
        # Add unit marker by default if no marker is present
        if not any(item.iter_markers()):
            item.add_marker(pytest.mark.unit)

def pytest_sessionstart(session):
    """Log test session start."""
    test_logger.info(f"Starting test session with {len(session.items)} tests")
    test_logger.info(f"Test log file: {test_log_file}")

def pytest_sessionfinish(session, exitstatus):
    """Log test session finish."""
    test_logger.info(f"Test session finished with exit status: {exitstatus}")
    if hasattr(session, 'testscollected'):
        test_logger.info(f"Tests collected: {session.testscollected}")

def pytest_runtest_logreport(report):
    """Log individual test results."""
    if report.when == 'call':
        if report.passed:
            test_logger.debug(f"✓ PASSED: {report.nodeid}")
        elif report.failed:
            test_logger.error(f"✗ FAILED: {report.nodeid}")
            if report.longrepr:
                test_logger.error(f"Error details: {report.longrepr}")
        elif report.skipped:
            test_logger.warning(f"⚠ SKIPPED: {report.nodeid}") 