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

# Note: Do not override BASE_DATA_DIR/USER_INFO_DIR_PATH via environment here,
# as some unit tests assert the library defaults. Session fixtures below
# patch core.config attributes to isolate user data under tests/data/users.

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

# Set environment variable to indicate we're running tests, and enable verbose component logs under tests/logs
os.environ['MHM_TESTING'] = '1'
os.environ['TEST_VERBOSE_LOGS'] = os.environ.get('TEST_VERBOSE_LOGS', '1')

# Force all log paths to tests/logs for absolute isolation, even if modules read env at import time
tests_logs_dir = (Path(__file__).parent / 'logs').resolve()
tests_logs_dir.mkdir(exist_ok=True)
os.environ['LOGS_DIR'] = str(tests_logs_dir)
os.environ['LOG_BACKUP_DIR'] = str(tests_logs_dir / 'backups')
os.environ['LOG_ARCHIVE_DIR'] = str(tests_logs_dir / 'archive')
(tests_logs_dir / 'backups').mkdir(exist_ok=True)
(tests_logs_dir / 'archive').mkdir(exist_ok=True)

# Explicitly set all component log files under tests/logs to catch any env-based lookups
os.environ['LOG_MAIN_FILE'] = str(tests_logs_dir / 'app.log')
os.environ['LOG_DISCORD_FILE'] = str(tests_logs_dir / 'discord.log')
os.environ['LOG_AI_FILE'] = str(tests_logs_dir / 'ai.log')
os.environ['LOG_USER_ACTIVITY_FILE'] = str(tests_logs_dir / 'user_activity.log')
os.environ['LOG_ERRORS_FILE'] = str(tests_logs_dir / 'errors.log')
os.environ['LOG_COMMUNICATION_MANAGER_FILE'] = str(tests_logs_dir / 'communication_manager.log')
os.environ['LOG_EMAIL_FILE'] = str(tests_logs_dir / 'email.log')
os.environ['LOG_TELEGRAM_FILE'] = str(tests_logs_dir / 'telegram.log')
os.environ['LOG_UI_FILE'] = str(tests_logs_dir / 'ui.log')
os.environ['LOG_FILE_OPS_FILE'] = str(tests_logs_dir / 'file_ops.log')
os.environ['LOG_SCHEDULER_FILE'] = str(tests_logs_dir / 'scheduler.log')

# Import core modules for testing (after logging isolation is set up)
from core.config import BASE_DATA_DIR, USER_INFO_DIR_PATH

# Set up dedicated testing logging
def setup_test_logging():
    """Set up dedicated logging for tests with complete isolation from main app logging."""
    # Create test logs directory
    test_logs_dir = Path(project_root) / "tests" / "logs"
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
    
    # Also set up a handler for any "mhm" loggers to go to test logs
    mhm_logger = logging.getLogger("mhm")
    mhm_logger.setLevel(logging.DEBUG)
    mhm_logger.handlers.clear()
    mhm_logger.addHandler(file_handler)
    mhm_logger.propagate = False
    
    return test_logger, test_log_file

# Set up test logging
test_logger, test_log_file = setup_test_logging()

# --- HOUSEKEEPING: Prune old test artifacts to keep repo tidy ---
def _prune_old_files(target_dir: Path, patterns: list[str], older_than_days: int) -> int:
    """Remove files in target_dir matching any pattern older than N days.

    Returns the number of files removed.
    """
    removed_count = 0
    try:
        if older_than_days <= 0:
            return 0
        cutoff = datetime.now().timestamp() - (older_than_days * 24 * 3600)
        for pattern in patterns:
            for file_path in target_dir.rglob(pattern):
                try:
                    if file_path.is_file() and file_path.stat().st_mtime < cutoff:
                        file_path.unlink(missing_ok=True)
                        removed_count += 1
                except Exception:
                    # Best-effort cleanup; ignore individual file errors
                    pass
    except Exception:
        # Never fail tests due to cleanup issues
        pass
    return removed_count


@pytest.fixture(scope="session", autouse=True)
def prune_test_artifacts_before_and_after_session():
    """Prune old logs (tests/logs) and backups (tests/data/backups) before and after the session.

    Defaults: logs older than 14 days, test backups older than 7 days.
    Override via TEST_LOG_RETENTION_DAYS and TEST_BACKUP_RETENTION_DAYS env vars.
    """
    project_root_path = Path(project_root)
    logs_dir = project_root_path / "tests" / "logs"
    test_backups_dir = project_root_path / "tests" / "data" / "backups"

    log_retention_days = int(os.getenv("TEST_LOG_RETENTION_DAYS", "14"))
    backup_retention_days = int(os.getenv("TEST_BACKUP_RETENTION_DAYS", "7"))

    # Prune before tests
    if logs_dir.exists():
        removed = _prune_old_files(
            logs_dir,
            patterns=["*.log", "*.log.*", "*.gz"],
            older_than_days=log_retention_days,
        )
        if removed:
            test_logger.info(f"Pruned {removed} old test log files from {logs_dir}")

    if test_backups_dir.exists():
        removed = _prune_old_files(
            test_backups_dir,
            patterns=["*.zip"],
            older_than_days=backup_retention_days,
        )
        if removed:
            test_logger.info(f"Pruned {removed} old test backup files from {test_backups_dir}")

    yield

    # Prune again after tests
    if logs_dir.exists():
        removed = _prune_old_files(
            logs_dir,
            patterns=["*.log", "*.log.*", "*.gz"],
            older_than_days=log_retention_days,
        )
        if removed:
            test_logger.info(f"Post-run prune removed {removed} old test log files from {logs_dir}")

    if test_backups_dir.exists():
        removed = _prune_old_files(
            test_backups_dir,
            patterns=["*.zip"],
            older_than_days=backup_retention_days,
        )
        if removed:
            test_logger.info(f"Post-run prune removed {removed} old test backup files from {test_backups_dir}")

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
         patch('core.config.DEFAULT_MESSAGES_DIR_PATH', os.path.join(test_data_dir, 'resources', 'default_messages')):
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
    
    # Create mock checkins.json
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
    
    with open(os.path.join(user_dir, "checkins.json"), "w") as f:
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
    
    # Create mock checkins.json
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
    
    with open(os.path.join(user_dir, "checkins.json"), "w") as f:
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

# --- GLOBAL PATCH: Force all user data to tests/data/users/ for all tests ---
@pytest.fixture(autouse=True, scope="session")
def patch_user_data_dirs():
    """Patch BASE_DATA_DIR and USER_INFO_DIR_PATH to use tests/data/users/ for all tests."""
    from unittest.mock import patch
    import core.config
    test_data_dir = os.path.abspath("tests/data")
    users_dir = os.path.join(test_data_dir, "users")
    os.makedirs(users_dir, exist_ok=True)
    
    # Patch the module attributes directly
    with patch.object(core.config, "BASE_DATA_DIR", test_data_dir), \
         patch.object(core.config, "USER_INFO_DIR_PATH", users_dir):
        yield

# --- CLEANUP FIXTURE: Remove test users from both data/users/ and tests/data/users/ after all tests ---
@pytest.fixture(scope="session", autouse=True)
def cleanup_test_users_after_session():
    """Remove test users from both data/users/ and tests/data/users/ after all tests."""
    yield  # Run all tests first
    
    # Clear all user caches to prevent state pollution between test runs
    try:
        from core.user_management import clear_user_caches
        clear_user_caches()  # Clear all caches
    except Exception:
        pass  # Ignore errors during cleanup
    
    for base_dir in ["data/users", "tests/data/users"]:
        abs_dir = os.path.abspath(base_dir)
        if os.path.exists(abs_dir):
            for item in os.listdir(abs_dir):
                # Clean up test directories (test-*, test_*, testuser*) and UUID directories
                # UUIDs are 32 hex characters in 8-4-4-4-12 format
                import re
                uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
                if (item.startswith("test-") or 
                    item.startswith("test_") or 
                    item.startswith("testuser") or
                    uuid_pattern.match(item)):
                    item_path = os.path.join(abs_dir, item)
                    try:
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                        else:
                            os.remove(item_path)
                    except Exception:
                        pass
    
    # Additional cleanup: Remove ALL directories in tests/data/users/ for complete isolation
    # This ensures no test data persists between test runs
    test_users_dir = os.path.abspath("tests/data/users")
    if os.path.exists(test_users_dir):
        for item in os.listdir(test_users_dir):
            item_path = os.path.join(test_users_dir, item)
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
            except Exception:
                pass
    
    # Also clean up the user index file to prevent stale entries
    test_data_dir = os.path.abspath("tests/data")
    user_index_file = os.path.join(test_data_dir, "user_index.json")
    if os.path.exists(user_index_file):
        try:
            os.remove(user_index_file)
        except Exception:
            pass

@pytest.fixture(scope="function", autouse=True)
def clear_user_caches_between_tests():
    """Clear user caches between tests to prevent state pollution."""
    yield  # Run the test
    # Clear caches after each test
    try:
        from core.user_management import clear_user_caches
        clear_user_caches()  # Clear all caches
    except Exception:
        pass  # Ignore errors during cleanup

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
    
    # Core test type markers
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "behavior: mark test as a behavior test"
    )
    config.addinivalue_line(
        "markers", "ui: mark test as testing UI components"
    )
    
    # Performance & resource markers
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance testing"
    )
    config.addinivalue_line(
        "markers", "memory: mark test as memory intensive"
    )
    config.addinivalue_line(
        "markers", "network: mark test as requiring network connectivity"
    )
    config.addinivalue_line(
        "markers", "external: mark test as requiring external services"
    )
    config.addinivalue_line(
        "markers", "file_io: mark test as having heavy file operations"
    )
    
    # Feature-specific markers
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
        "markers", "config: mark test as configuration and settings functionality"
    )
    config.addinivalue_line(
        "markers", "tasks: mark test as task management functionality"
    )
    config.addinivalue_line(
        "markers", "checkins: mark test as check-in system functionality"
    )
    config.addinivalue_line(
        "markers", "schedules: mark test as schedule management functionality"
    )
    config.addinivalue_line(
        "markers", "messages: mark test as message system functionality"
    )
    config.addinivalue_line(
        "markers", "analytics: mark test as analytics and reporting functionality"
    )
    config.addinivalue_line(
        "markers", "user_management: mark test as user account management functionality"
    )
    config.addinivalue_line(
        "markers", "channels: mark test as communication channel functionality"
    )
    
    # Test quality markers
    config.addinivalue_line(
        "markers", "flaky: mark test as occasionally failing"
    )
    config.addinivalue_line(
        "markers", "known_issue: mark test as testing known bugs or limitations"
    )
    config.addinivalue_line(
        "markers", "regression: mark test as preventing regression issues"
    )
    config.addinivalue_line(
        "markers", "smoke: mark test as basic functionality smoke test"
    )
    config.addinivalue_line(
        "markers", "critical: mark test as critical path test"
    )
    
    # Development workflow markers
    config.addinivalue_line(
        "markers", "wip: mark test as work in progress"
    )
    config.addinivalue_line(
        "markers", "todo: mark test as not yet implemented"
    )
    config.addinivalue_line(
        "markers", "skip_ci: mark test as to skip in CI/CD pipeline"
    )
    config.addinivalue_line(
        "markers", "manual: mark test as requiring manual intervention"
    )
    config.addinivalue_line(
        "markers", "debug: mark test as debug specific"
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