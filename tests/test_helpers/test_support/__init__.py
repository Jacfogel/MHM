"""Test support package: standalone helpers, isolation utilities, and conftest plugins for the test suite.

Use tests.test_helpers.test_support.test_helpers for wait_until and materialize_user_minimal_via_public_apis.
Use tests.test_helpers.test_support.test_isolation for isolation helpers (IsolationManager, ensure_test_isolation, etc.).
Conftest plugins (conftest_env, conftest_mocks, conftest_cleanup, conftest_logging, conftest_user_data,
conftest_hooks) live here and are loaded via pytest_plugins in tests/conftest.py.
"""

from tests.test_helpers.test_support.test_helpers import (
    materialize_user_minimal_via_public_apis,
    wait_until,
)
from tests.test_helpers.test_support.test_isolation import (
    IsolationManager,
    create_safe_scheduler_manager,
    ensure_test_isolation,
    mock_schtasks_call,
    mock_system_calls,
    verify_no_real_tasks_created,
)

__all__ = [
    "IsolationManager",
    "create_safe_scheduler_manager",
    "ensure_test_isolation",
    "materialize_user_minimal_via_public_apis",
    "mock_schtasks_call",
    "mock_system_calls",
    "verify_no_real_tasks_created",
    "wait_until",
]
