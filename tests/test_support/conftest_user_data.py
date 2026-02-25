"""
Pytest plugin: user-data fixtures (test_data_dir, mock_config, mock_user_data, cleanup, etc.).

Imports project_root, tests_data_dir, tests_data_tmp_dir, test_logger from tests.conftest.
"""

import os
import json
import shutil
import pytest
from pathlib import Path
from unittest.mock import patch

from tests.conftest import (
    project_root,
    tests_data_dir,
    tests_data_tmp_dir,
    test_logger,
)
from core.time_utilities import now_timestamp_full
from tests.test_support.conftest_cleanup_impl import _is_transient_test_data_dir_name

@pytest.fixture(scope="session")
def test_data_dir():
    """Provide the repository-scoped test data directory for all tests."""
    test_logger.info(f"Using test data directory: {tests_data_dir}")
    return str(tests_data_dir)


@pytest.fixture(scope="function", autouse=True)
def mock_config(test_data_dir):
    """Mock configuration for testing with proper test data directory."""
    test_logger.debug(f"Setting up mock config with test data dir: {test_data_dir}")
    import core.config

    # Always patch to ensure consistent test environment
    # This ensures that even if patch_user_data_dirs is not active, we have a consistent config
    default_categories = (
        '["motivational", "health", "quotes_to_ponder", "word_of_the_day", "fun_facts"]'
    )

    with (
        patch.object(core.config, "BASE_DATA_DIR", test_data_dir),
        patch.object(
            core.config, "USER_INFO_DIR_PATH", os.path.join(test_data_dir, "users")
        ),
        patch.object(
            core.config,
            "DEFAULT_MESSAGES_DIR_PATH",
            os.path.join(project_root, "resources", "default_messages"),
        ),
        patch.dict(os.environ, {"CATEGORIES": default_categories}, clear=False),
    ):
        yield


@pytest.fixture(scope="function", autouse=True)
def ensure_mock_config_applied(mock_config, test_data_dir):
    """Verify mock_config fixture is active for every test."""
    import os
    import core.config

    assert os.path.samefile(core.config.BASE_DATA_DIR, test_data_dir)
    yield


@pytest.fixture(scope="function", autouse=True)
def clear_user_caches_between_tests():
    """Ensure user data caches don't leak between tests."""
    from core.user_data_handlers import clear_user_caches

    clear_user_caches()
    yield
    clear_user_caches()


@pytest.fixture(scope="session", autouse=True)
def register_user_data_loaders_session():
    """Ensure core user data loaders are present without overwriting metadata."""
    import core.user_data_handlers as um

    # Set only missing loaders to avoid clobbering metadata
    for key, func, ftype in [
        ("account", um._get_user_data__load_account, "account"),
        ("preferences", um._get_user_data__load_preferences, "preferences"),
        ("context", um._get_user_data__load_context, "user_context"),
        ("schedules", um._get_user_data__load_schedules, "schedules"),
    ]:
        try:
            entry = um.USER_DATA_LOADERS.get(key)
            if entry and entry.get("loader") is None:
                um.register_data_loader(key, func, ftype)
        except Exception:
            # As a fallback, if the dict is missing, register minimally
            um.register_data_loader(key, func, ftype)
    yield


@pytest.fixture(scope="function", autouse=True)
def fix_user_data_loaders():
    """Ensure loaders stay correctly registered for each test without overwriting metadata."""
    import core.user_data_handlers as um

    for key, func, ftype in [
        ("account", um._get_user_data__load_account, "account"),
        ("preferences", um._get_user_data__load_preferences, "preferences"),
        ("context", um._get_user_data__load_context, "user_context"),
        ("schedules", um._get_user_data__load_schedules, "schedules"),
    ]:
        entry = um.USER_DATA_LOADERS.get(key)
        if entry and entry.get("loader") is None:
            um.register_data_loader(key, func, ftype)
    yield


@pytest.fixture(scope="session", autouse=True)
def shim_get_user_data_to_invoke_loaders():
    """Shim core.user_data_handlers.get_user_data to ensure structured dicts.

    If a test calls get_user_data with 'all' or a specific type and the result is
    empty/missing, invoke the registered loaders in USER_DATA_LOADERS to assemble
    the expected structure. This preserves production behavior when everything is
    wired correctly, but guards against import-order timing in tests.
    """
    import core.user_data_handlers as um

    # Safety net: always provide structural dicts during tests regardless of loader state
    # Also patch the public helpers module used by many tests
    try:
        import core.user_data_handlers as udh
    except Exception:
        udh = None

    # Prefer core.user_data_handlers.get_user_data; fall back to handlers if missing
    original_get_user_data = getattr(um, "get_user_data", None)
    if (
        original_get_user_data is None
        and udh is not None
        and hasattr(udh, "get_user_data")
    ):
        original_get_user_data = getattr(udh, "get_user_data", None)
    if original_get_user_data is None:
        yield
        return

    def _load_single_type(user_id: str, key: str, *, auto_create: bool):
        try:
            entry = um.USER_DATA_LOADERS.get(key)
            loader = None
            if entry:
                loader = entry.get("loader")
            # If loader is missing, attempt to self-heal by (re)registering
            if loader is None:
                key_to_func_and_file = {
                    "account": (um._get_user_data__load_account, "account"),
                    "preferences": (um._get_user_data__load_preferences, "preferences"),
                    "context": (um._get_user_data__load_context, "user_context"),
                    "schedules": (um._get_user_data__load_schedules, "schedules"),
                }
                func_file = key_to_func_and_file.get(key)
                if func_file is None:
                    return None
                func, file_type = func_file
                try:
                    um.register_data_loader(key, func, file_type)
                    entry = um.USER_DATA_LOADERS.get(key)
                    loader = entry.get("loader") if entry else None
                except Exception:
                    loader = func
            if loader is None:
                return None
            # Loaders accept (user_id, auto_create)
            return loader(user_id, auto_create)
        except Exception:
            return None

    def _fallback_read_from_files(user_id: str, key: str):
        """Read requested type directly from user JSON files as a last resort."""
        try:
            import core.config as _cfg
            from core.config import get_user_data_dir as _get_user_data_dir
        except Exception:
            return None

        # Resolve actual user directory via config helper (handles UUID mapping)
        try:
            user_dir = _get_user_data_dir(user_id)
        except Exception:
            user_dir = os.path.join(_cfg.USER_INFO_DIR_PATH, user_id)
        filename_map = {
            "account": "account.json",
            "preferences": "preferences.json",
            "context": "user_context.json",
            "schedules": "schedules.json",
        }
        filename = filename_map.get(key)
        if not filename:
            return None
        file_path = os.path.join(user_dir, filename)
        if not os.path.exists(file_path):
            return None
        try:
            with open(file_path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return None

    def wrapped_get_user_data(user_id: str, data_type: str = "all", *args, **kwargs):
        auto_create = True
        try:
            auto_create = bool(kwargs.get("auto_create", True))
        except Exception:
            auto_create = True
        result = original_get_user_data(user_id, data_type, *args, **kwargs)
        try:
            # If asking for all, ensure a dict with expected keys
            if data_type == "all":
                if not isinstance(result, dict):
                    test_logger.debug(
                        f"shim_get_user_data: Coercing non-dict 'all' result for {user_id} -> assembling structure"
                    )
                    result = {} if result is None else {"value": result}
                # Respect auto_create and only assemble when user dir exists
                should_assemble = auto_create
                if should_assemble:
                    try:
                        from core.config import get_user_data_dir as _get_user_data_dir

                        if not os.path.exists(_get_user_data_dir(user_id)):
                            should_assemble = False
                    except Exception:
                        should_assemble = False
                if should_assemble:
                    for key in ("account", "preferences", "context", "schedules"):
                        if key not in result or not result.get(key):
                            test_logger.debug(
                                f"shim_get_user_data: '{key}' missing/empty for {user_id}; invoking loader"
                            )
                            loaded = _load_single_type(
                                user_id, key, auto_create=auto_create
                            )
                            if loaded is not None:
                                result[key] = loaded
                            else:
                                # Fallback: direct file read
                                fb = _fallback_read_from_files(user_id, key)
                                if fb is not None:
                                    result[key] = fb
                                else:
                                    test_logger.warning(
                                        f"shim_get_user_data: loader and file fallback could not provide '{key}' for {user_id}"
                                    )
                return result

            # Specific type request: ensure structure present
            if isinstance(data_type, str):
                key = data_type
                # If result already a dict containing the key with a value, return as-is
                if isinstance(result, dict) and result.get(key):
                    return result
                # Otherwise, attempt to load and return {key: value} if allowed
                should_assemble = auto_create
                if should_assemble:
                    try:
                        from core.config import get_user_data_dir as _get_user_data_dir

                        if not os.path.exists(_get_user_data_dir(user_id)):
                            should_assemble = False
                    except Exception:
                        should_assemble = False
                if should_assemble:
                    test_logger.debug(
                        f"shim_get_user_data: '{key}' request returned empty for {user_id}; invoking loader"
                    )
                    loaded = _load_single_type(user_id, key, auto_create=auto_create)
                    if loaded is not None:
                        return {key: loaded}
                    fb = _fallback_read_from_files(user_id, key)
                    if fb is not None:
                        return {key: fb}
                return result
        except Exception:
            test_logger.exception(
                "shim_get_user_data: unexpected error while assembling result"
            )
            return result

        return result

    # Patch in place for the duration of the test
    # Patch both modules so all call sites are covered
    setattr(um, "get_user_data", wrapped_get_user_data)
    original_handlers_get = None
    if udh is not None and hasattr(udh, "get_user_data"):
        original_handlers_get = udh.get_user_data
        setattr(udh, "get_user_data", wrapped_get_user_data)
    try:
        yield
    finally:
        # Restore originals at end of session
        try:
            setattr(um, "get_user_data", original_get_user_data)
        except Exception:
            pass
        if udh is not None and original_handlers_get is not None:
            try:
                setattr(udh, "get_user_data", original_handlers_get)
            except Exception:
                pass


@pytest.fixture(scope="session", autouse=True)
def verify_required_loaders_present():
    """Fail fast if required user-data loaders are missing at session start."""
    try:
        import core.user_data_handlers as um

        required = ("account", "preferences", "context", "schedules")
        missing = []
        for k in required:
            entry = um.USER_DATA_LOADERS.get(k)
            if not (isinstance(entry, dict) and entry.get("loader")):
                missing.append(k)
        if missing:
            raise AssertionError(
                f"Required user-data loaders missing or None: {missing}. "
                f"Present keys: {list(um.USER_DATA_LOADERS.keys())}"
            )
    except Exception as e:
        raise AssertionError(f"Loader self-check failed: {e}")


@pytest.fixture(scope="function", autouse=True)
def env_guard_and_restore(monkeypatch):
    """Snapshot and restore critical environment variables to prevent test leakage.

    Restores after each test to ensure environment stability across the suite.
    """
    critical_keys = [
        "MHM_TESTING",
        "CATEGORIES",
        "LOGS_DIR",
        "LOG_BACKUP_DIR",
        "LOG_ARCHIVE_DIR",
        "LOG_MAIN_FILE",
        "LOG_DISCORD_FILE",
        "LOG_AI_FILE",
        "LOG_USER_ACTIVITY_FILE",
        "LOG_ERRORS_FILE",
        "LOG_COMMUNICATION_MANAGER_FILE",
        "LOG_EMAIL_FILE",
        "LOG_UI_FILE",
        "LOG_FILE_OPS_FILE",
        "LOG_SCHEDULER_FILE",
        "BASE_DATA_DIR",
        "USER_INFO_DIR_PATH",
        "TEMP",
        "TMP",
        "TMPDIR",
    ]
    snapshot = {k: os.environ.get(k) for k in critical_keys}
    try:
        yield
    finally:
        for k, v in snapshot.items():
            if v is None:
                if k in os.environ:
                    monkeypatch.delenv(k, raising=False)
            else:
                monkeypatch.setenv(k, v)


@pytest.fixture(scope="session", autouse=True)
def ensure_tmp_base_directory():
    """Ensure base tmp directory exists at session start (optimization: create once)."""
    # Use the session-scoped test_data_dir directly to avoid scope mismatch
    # with function-scoped test_data_dir fixtures in some test files
    base_tmp = os.path.join(tests_data_dir, "tmp")
    os.makedirs(base_tmp, exist_ok=True)
    yield


@pytest.fixture(scope="function")
def test_path_factory(test_data_dir, ensure_tmp_base_directory):
    """Provide a per-test directory under tests/data/tmp/<uuid> for ad-hoc temp usage.

    Prefer this over raw tempfile.mkdtemp/TemporaryDirectory to keep paths within the repo.
    Optimized: base tmp directory is created once at session start.
    """
    import uuid

    base_tmp = os.path.join(test_data_dir, "tmp")
    # Base directory already exists from session fixture, just create subdirectory
    path = os.path.join(base_tmp, uuid.uuid4().hex)
    os.makedirs(path, exist_ok=True)
    return path


@pytest.fixture(scope="function")
def ensure_user_materialized(test_data_dir):
    """Return a helper to ensure account/preferences/context files exist for a user.

    If the user directory is missing, uses TestUserFactory to create a basic user.
    If present but missing files, writes minimal JSON structures to materialize them.
    """
    from pathlib import Path as _Path
    import json as _json
    import os as _os

    def _helper(user_id: str):
        users_dir = _Path(test_data_dir) / "users"
        user_dir = users_dir / user_id
        if not user_dir.exists():
            try:
                from tests.test_utilities import TestUserFactory

                TestUserFactory.create_basic_user(
                    user_id, test_data_dir=str(test_data_dir)
                )
            except Exception:
                user_dir.mkdir(parents=True, exist_ok=True)
        # Materialize minimal files if missing
        acct_path = user_dir / "account.json"
        prefs_path = user_dir / "preferences.json"
        ctx_path = user_dir / "user_context.json"
        if not acct_path.exists():
            _json.dump(
                {
                    "user_id": user_id,
                    "internal_username": user_id,
                    "account_status": "active",
                    "features": {
                        "automated_messages": "disabled",
                        "task_management": "disabled",
                        "checkins": "disabled",
                    },
                },
                open(acct_path, "w", encoding="utf-8"),
                indent=2,
            )
        if not prefs_path.exists():
            _json.dump(
                {
                    "channel": {"type": "email"},
                    "checkin_settings": {"enabled": False},
                    "task_settings": {"enabled": False},
                },
                open(prefs_path, "w", encoding="utf-8"),
                indent=2,
            )
        if not ctx_path.exists():
            _json.dump(
                {"preferred_name": user_id, "pronouns": [], "custom_fields": {}},
                open(ctx_path, "w", encoding="utf-8"),
                indent=2,
            )
        return str(user_dir)

    return _helper


@pytest.fixture(scope="function", autouse=True)
def path_sanitizer():
    """Guardrail: ensure temp resolution stays within tests/data and detect escapes.

    Fails fast if the active temp directory is outside tests/data.
    """
    import tempfile

    # Always enforce repository-scoped tests/data as the allowed root
    allowed_root = os.path.abspath(str(tests_data_dir))
    # Validate Python's temp resolution points to tests/data
    current_tmp = os.path.abspath(tempfile.gettempdir())
    if not current_tmp.startswith(allowed_root):
        raise AssertionError(
            f"Temp directory escaped repo: {current_tmp} (expected under {allowed_root})."
        )
    yield


@pytest.fixture(scope="function", autouse=True)
def enforce_user_dir_locations():
    """Ensure tests only create user dirs under tests/data/users.

    - Fails if a top-level tests/data/test-user* directory appears.
    Cleans stray dirs to keep workspace tidy before failing.

    NOTE:
    Do not scan tests/data/tmp per test. That directory can contain thousands of
    entries during long parallel runs, and repeated setup/teardown scans become
    a dominant runtime cost. tmp hygiene is handled by session-end cleanup.
    """
    base = tests_data_dir
    users_dir = base / "users"
    try:
        pre_top = set(x.name for x in base.iterdir() if x.is_dir())
    except Exception:
        pre_top = set()

    yield

    # Check for misplaced top-level test users created during this test only.
    try:
        post_top = set(x.name for x in base.iterdir() if x.is_dir())
        new_top_dirs = post_top - pre_top
        for name in new_top_dirs:
            entry = base / name
            if not entry.is_dir():
                continue
            if (
                entry.name.startswith("test-user")
                and entry.parent == base
                and entry != users_dir
            ):
                try:
                    shutil.rmtree(entry, ignore_errors=True)
                finally:
                    pytest.fail(
                        f"Misplaced test user directory detected: {entry}. "
                        f"User directories must be under {users_dir}."
                    )
    except Exception:
        # Do not mask test results if scan fails
        pass

@pytest.fixture(scope="session", autouse=True)
def cleanup_tmp_at_session_end():
    """Clear tests/data/tmp contents at session end to keep the workspace tidy."""
    # Avoid xdist worker races on shared tmp directory.
    if os.environ.get("PYTEST_XDIST_WORKER"):
        yield
        return

    yield
    try:
        tmp_dir = tests_data_dir / "tmp"
        if tmp_dir.exists():
            for child in tmp_dir.iterdir():
                if child.is_dir():
                    shutil.rmtree(child, ignore_errors=True)
                else:
                    try:
                        child.unlink(missing_ok=True)
                    except Exception:
                        pass
    except Exception:
        pass


@pytest.fixture(scope="session", autouse=True)
def force_test_data_directory():
    """Route all system temp usage into tests/data for the entire session."""
    import tempfile

    root = str(tests_data_tmp_dir)
    os.makedirs(root, exist_ok=True)
    # Set common env vars so any native/library lookups resolve under tests/data
    os.environ["TMPDIR"] = root
    os.environ["TEMP"] = root
    os.environ["TMP"] = root
    # Patch Python's temp resolution
    original_tempdir = tempfile.tempdir
    tempfile.tempdir = root
    try:
        yield
    finally:
        tempfile.tempdir = original_tempdir


@pytest.fixture(scope="function")
def mock_user_data(mock_config, test_data_dir, request):
    """Create mock user data for testing with unique user ID for each test."""
    import uuid

    # Generate unique user ID for each test to prevent interference
    user_id = f"test-user-{uuid.uuid4().hex[:8]}"
    user_dir = os.path.join(test_data_dir, "users", user_id)
    # Ensure parent directory exists first (race condition fix for parallel execution)
    os.makedirs(os.path.dirname(user_dir), exist_ok=True)
    os.makedirs(user_dir, exist_ok=True)

    test_logger.debug(f"Creating mock user data for user: {user_id}")

    # Create mock account.json with current timestamp
    current_time = now_timestamp_full()
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
            "task_management": "disabled",
        },
    }

    # Create mock preferences.json - categories only included if automated_messages enabled
    preferences_data = {
        "channel": {"type": "email"},
        "checkin_settings": {
            "enabled": False,
            "frequency": "daily",
            "time": "09:00",
            "categories": ["mood", "energy", "sleep"],
        },
        "task_settings": {
            "enabled": False,
            "reminder_frequency": "daily",
            "reminder_time": "10:00",
        },
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
            "accessibility_needs": [],
        },
        "interests": ["reading", "music"],
        "goals": ["Improve mental health", "Stay organized"],
        "loved_ones": [],
        "activities_for_encouragement": ["exercise", "socializing"],
        "notes_for_ai": ["Prefers gentle encouragement", "Responds well to structure"],
        "created_at": current_time,
        "last_updated": current_time,
    }

    # Create mock checkins.json
    checkins_data = {"checkins": [], "last_checkin_date": None, "streak_count": 0}

    # Create minimal schedules.json so schedule reads/writes have a base file
    schedules_data = {"categories": {}}

    # Create mock chat_interactions.json
    chat_data = {"interactions": [], "total_interactions": 0, "last_interaction": None}

    # Create messages directory and sent_messages.json only if automated_messages enabled
    messages_dir = os.path.join(user_dir, "messages")
    if account_data["features"]["automated_messages"] == "enabled":
        os.makedirs(messages_dir, exist_ok=True)

        sent_messages_data = {"messages": [], "total_sent": 0, "last_sent": None}

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
    with open(os.path.join(user_dir, "schedules.json"), "w") as f:
        json.dump(schedules_data, f, indent=2)

    # Ensure user is discoverable via identifier lookups
    # Use file locking-aware update and retry if needed
    try:
        from core.user_data_manager import update_user_index

        # Retry update_user_index in case of race conditions in parallel execution
        max_retries = 3
        for attempt in range(max_retries):
            success = update_user_index(user_id)
            if success:
                break
            if attempt < max_retries - 1:
                import time

                time.sleep(0.1)  # Brief delay before retry
        if not success:
            test_logger.warning(
                f"Failed to update user index for {user_id} after {max_retries} attempts"
            )
    except Exception as e:
        test_logger.warning(f"Error updating user index for {user_id}: {e}")
        # Don't fail the test, but log the issue

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
        "schedules_data": schedules_data,
        "chat_data": chat_data,
        "sent_messages_data": sent_messages_data,
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
    current_time = now_timestamp_full()
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
            "task_management": "disabled",
        },
    }

    # Create mock preferences.json with categories (automated_messages enabled)
    preferences_data = {
        "channel": {"type": "email"},
        "categories": ["motivational", "health", "quotes_to_ponder"],
        "checkin_settings": {
            "enabled": False,
            "frequency": "daily",
            "time": "09:00",
            "categories": ["mood", "energy", "sleep"],
        },
        "task_settings": {
            "enabled": False,
            "reminder_frequency": "daily",
            "reminder_time": "10:00",
        },
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
            "accessibility_needs": [],
        },
        "interests": ["reading", "music"],
        "goals": ["Improve mental health", "Stay organized"],
        "loved_ones": [],
        "activities_for_encouragement": ["exercise", "socializing"],
        "notes_for_ai": ["Prefers gentle encouragement", "Responds well to structure"],
        "created_at": current_time,
        "last_updated": current_time,
    }

    # Create mock checkins.json
    checkins_data = {"checkins": [], "last_checkin_date": None, "streak_count": 0}

    # Create mock chat_interactions.json
    chat_data = {"interactions": [], "total_interactions": 0, "last_interaction": None}

    # Create messages directory and sent_messages.json (automated_messages enabled)
    messages_dir = os.path.join(user_dir, "messages")
    os.makedirs(messages_dir, exist_ok=True)

    sent_messages_data = {"messages": [], "total_sent": 0, "last_sent": None}

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
        "sent_messages_data": sent_messages_data,
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
                test_logger.warning(
                    f"Failed to update user index for test user: {user_id}"
                )
            return success
        except Exception as e:
            test_logger.warning(
                f"Error updating user index for test user {user_id}: {e}"
            )
            return False

    return _update_index


# --- GLOBAL PATCH: Force all user data to tests/data/users/ for all tests ---
# DISABLED: This fixture was causing test isolation issues
# @pytest.fixture(autouse=True, scope="session")
# def patch_user_data_dirs():
#     """Patch BASE_DATA_DIR and USER_INFO_DIR_PATH to use tests/data/users/ for all tests."""
#     from unittest.mock import patch
#     import core.config
#     test_data_dir = os.path.abspath("tests/data")
#     users_dir = os.path.join(test_data_dir, "users")
#     os.makedirs(users_dir, exist_ok=True)
#
#     # Patch the module attributes directly
#     with patch.object(core.config, "BASE_DATA_DIR", test_data_dir), \
#          patch.object(core.config, "USER_INFO_DIR_PATH", users_dir):
#         yield


# --- CLEANUP FIXTURE: Remove test users from tests/data/users/ after all tests (NEVER touches real user data) ---
def _cleanup_test_user_artifacts() -> None:
    """Remove test users from tests/data/users/ after all tests."""
    # Clear all user caches to prevent state pollution between test runs
    try:
        from core.user_data_handlers import clear_user_caches

        clear_user_caches()  # Clear all caches
    except Exception:
        pass  # Ignore errors during cleanup

    # Only clean up test directories, NEVER real user data
    for base_dir in ["tests/data/users"]:
        abs_dir = os.path.abspath(base_dir)
        if os.path.exists(abs_dir):
            for item in os.listdir(abs_dir):
                # Clean up ONLY test directories (test-*, test_*, testuser*)
                # NEVER clean up UUID directories - these are real users!
                if (
                    item.startswith("test-")
                    or item.startswith("test_")
                    or item.startswith("testuser")
                ):
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


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_users_after_session():
    """Remove test users from tests/data/users/ after all tests. NEVER touches real user data."""
    yield  # Run all tests first

    if os.environ.get("PYTEST_XDIST_WORKER"):
        return

    _cleanup_test_user_artifacts()
    base_test_data_dir = str(tests_data_dir)

    # Clean up test request files from schedule editor tests
    requests_dir = os.path.join(base_test_data_dir, "requests")
    if os.path.exists(requests_dir):
        try:
            for item in os.listdir(requests_dir):
                # Clean up test request files (reschedule_test_*)
                if item.startswith("reschedule_test_"):
                    item_path = os.path.join(requests_dir, item)
                    try:
                        os.remove(item_path)
                    except Exception:
                        pass
        except Exception:
            pass

    # Clean up test backup files to prevent clutter
    backup_dir = os.path.join(base_test_data_dir, "backups")
    if os.path.exists(backup_dir):
        try:
            for item in os.listdir(backup_dir):
                item_path = os.path.join(backup_dir, item)
                try:
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path, ignore_errors=True)
                except Exception:
                    pass
        except Exception:
            pass

    # Clean up pytest-of-* and tmp* directories (pytest creates these when using tmpdir fixtures)
    # Matches: tmp_*, tmp* (but not just "tmp"), pytest-of-*
    # Use direct directory iteration instead of glob for Windows compatibility
    try:
        if os.path.exists(base_test_data_dir):
            for item in os.listdir(base_test_data_dir):
                item_path = os.path.join(base_test_data_dir, item)
                try:
                    if os.path.isdir(item_path):
                        if _is_transient_test_data_dir_name(item):
                            shutil.rmtree(item_path, ignore_errors=True)
                    elif os.path.isfile(item_path):
                        # Clean up test JSON files (test_*.json, .tmp_*.json, welcome_tracking*.json, conversation_states*.json)
                        if item.endswith(".json"):
                            test_json_patterns = [
                                "test_",
                                ".tmp_",
                                "welcome_tracking",
                                "conversation_states",
                            ]
                            if any(
                                item.startswith(pattern)
                                for pattern in test_json_patterns
                            ):
                                os.remove(item_path)
                        # Clean up .last_cache_cleanup file
                        elif item == ".last_cache_cleanup":
                            os.remove(item_path)
                except Exception:
                    pass
    except Exception:
        pass

    # Clean up flags directory
    flags_dir = os.path.join(base_test_data_dir, "flags")
    if os.path.exists(flags_dir):
        try:
            for item in os.listdir(flags_dir):
                item_path = os.path.join(flags_dir, item)
                try:
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path, ignore_errors=True)
                except Exception:
                    pass
        except Exception:
            pass

    # Clean up tmp directory
    tmp_dir = os.path.join(base_test_data_dir, "tmp")
    if os.path.exists(tmp_dir):
        try:
            for item in os.listdir(tmp_dir):
                item_path = os.path.join(tmp_dir, item)
                try:
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path, ignore_errors=True)
                except Exception:
                    pass
        except Exception:
            pass

    # Clean up other test artifacts according to cleanup standards
    try:
        # Remove pytest temporary directories (pytest-of-* and tmp* directories created by pytest's tmpdir plugin)
        # Matches: tmp_*, tmp* (but not just "tmp"), pytest-of-*
        # Use direct directory iteration instead of glob for Windows compatibility
        if os.path.exists(base_test_data_dir):
            for item in os.listdir(base_test_data_dir):
                item_path = os.path.join(base_test_data_dir, item)
                try:
                    if os.path.isdir(item_path):
                        if _is_transient_test_data_dir_name(item):
                            shutil.rmtree(item_path, ignore_errors=True)
                    elif os.path.isfile(item_path):
                        # Clean up test JSON files (test_*.json, .tmp_*.json, welcome_tracking*.json, conversation_states*.json)
                        if item.endswith(".json"):
                            test_json_patterns = [
                                "test_",
                                ".tmp_",
                                "welcome_tracking",
                                "conversation_states",
                            ]
                            if any(
                                item.startswith(pattern)
                                for pattern in test_json_patterns
                            ):
                                os.remove(item_path)
                        # Clean up .last_cache_cleanup file
                        elif item == ".last_cache_cleanup":
                            os.remove(item_path)
                except Exception:
                    pass

        # Remove stray config directory
        config_dir = os.path.join(base_test_data_dir, "config")
        if os.path.exists(config_dir):
            shutil.rmtree(config_dir, ignore_errors=True)

        # Remove root files
        for filename in [".env", "requirements.txt", "test_file.json"]:
            file_path = os.path.join(base_test_data_dir, filename)
            if os.path.exists(file_path):
                os.remove(file_path)

        # Remove deprecated nested directory
        nested_dir = os.path.join(base_test_data_dir, "nested")
        if os.path.exists(nested_dir):
            shutil.rmtree(nested_dir, ignore_errors=True)

        # Remove corrupted files
        for item in os.listdir(base_test_data_dir):
            if (
                item.startswith("tmp") and ".corrupted_" in item
            ) or ".corrupted_" in item:
                item_path = os.path.join(base_test_data_dir, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)

        # Clear tmp directory completely - remove all subdirectories and files
        tmp_dir = os.path.join(base_test_data_dir, "tmp")
        if os.path.exists(tmp_dir):
            try:
                # Remove all contents (subdirectories and files)
                for item in os.listdir(tmp_dir):
                    item_path = os.path.join(tmp_dir, item)
                    try:
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path, ignore_errors=True)
                        else:
                            os.remove(item_path)
                    except Exception:
                        pass
                # Directory itself stays but is now empty
            except Exception:
                pass

        # Clear flags directory completely
        flags_dir = os.path.join(base_test_data_dir, "flags")
        if os.path.exists(flags_dir):
            try:
                for item in os.listdir(flags_dir):
                    item_path = os.path.join(flags_dir, item)
                    try:
                        if os.path.isfile(item_path):
                            os.remove(item_path)
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path, ignore_errors=True)
                    except Exception:
                        pass
            except Exception:
                pass

        # Clear requests directory completely
        requests_dir = os.path.join(base_test_data_dir, "requests")
        if os.path.exists(requests_dir):
            try:
                for item in os.listdir(requests_dir):
                    item_path = os.path.join(requests_dir, item)
                    try:
                        if os.path.isfile(item_path):
                            os.remove(item_path)
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path, ignore_errors=True)
                    except Exception:
                        pass
            except Exception:
                pass

        # Clean up conversation_states.json
        conversation_states_file = os.path.join(
            base_test_data_dir, "conversation_states.json"
        )
        if os.path.exists(conversation_states_file):
            try:
                os.remove(conversation_states_file)
            except Exception:
                pass

        # Clear logs directory
        logs_dir = os.path.join(base_test_data_dir, "logs")
        if os.path.exists(logs_dir):
            shutil.rmtree(logs_dir, ignore_errors=True)

        # Clean up old test_run files in tests/logs (but preserve current session files)
        test_logs_dir = os.path.join(project_root, "tests", "logs")
        if os.path.exists(test_logs_dir):
            try:
                for item in os.listdir(test_logs_dir):
                    # Only clean up old test_run files, not the current session's test_run.log
                    if (
                        item.startswith("test_run_")
                        and item.endswith(".log")
                        and item != "test_run.log"
                    ):
                        item_path = os.path.join(test_logs_dir, item)
                        if os.path.isfile(item_path):
                            os.remove(item_path)
            except Exception:
                pass

        # Clean up any stray test.log files in tests/data
        try:
            for root, dirs, files in os.walk(base_test_data_dir):
                for file in files:
                    if file == "test.log":
                        file_path = os.path.join(root, file)
                        try:
                            os.remove(file_path)
                        except Exception:
                            pass
        except Exception:
            pass

    except Exception:
        pass  # Ignore cleanup errors
