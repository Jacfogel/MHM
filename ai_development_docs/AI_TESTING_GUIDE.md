# AI Testing Guide

> **File**: `ai_development_docs/AI_TESTING_GUIDE.md`  
> **Pair**: [TESTING_GUIDE.md](tests/TESTING_GUIDE.md)  
> **Audience**: AI collaborators and tools  
> **Purpose**: Routing & constraints  
> **Style**: Minimal, routing-first  

> For detailed behavior, examples, and rationale, use matching sections in TESTING_GUIDE.md.  
> Keep this file's H2 headings in lockstep with TESTING_GUIDE.md when making changes.

---

## 1. Purpose and Scope

Use this file whenever you:

- Plan to modify or add tests.
- Need to decide which tests to run for a change.
- Must keep tests safe (no real user data, no real Windows tasks).

This guide is **not** a tutorial. It tells you:

- Where tests live.
- Which commands to run.
- Which other docs to consult.
- What safety rules must never be broken.

For full explanations, use the matching sections in [TESTING_GUIDE.md](tests/TESTING_GUIDE.md).

---

## 2. Test Layout and Types

Test locations (must not change without updating this file and [TESTING_GUIDE.md](tests/TESTING_GUIDE.md)):

- `tests/unit/` - pure logic, isolated from external systems.
- `tests/integration/` - interactions between modules and services.
- `tests/behavior/` - end-to-end flows approximating real usage.
- `tests/ui/` - Qt dialogs, widgets, and UI workflows.
- `tests/development_tools/` - infrastructure tests for development tools (config, CLI, exclusions, core analysis tools).
- `tests/conftest.py` - fixtures, hooks, and global configuration.

Rules:

- Tests belong under `tests/`, **never** under `scripts/` or arbitrary directories.
- Prefer integration/behavior tests for real flows; unit tests support them, not replace them.

When adding a test:

- Pure logic -> `tests/unit/`.
- Multi-module or service flows -> `tests/integration/` or `tests/behavior/`.
- UI dialogs or widgets -> `tests/ui/`.
- Development tools or infrastructure -> `tests/development_tools/`.
  - CLI routing tests stay lightweight by mocking `AIToolsService` (no subprocesses).
  - Permission/error scenarios are simulated via monkeypatching so results are identical on Windows/Linux.

**Note:** Core analysis tools (`development_tools/docs/analyze_documentation_sync.py`, `development_tools/functions/generate_function_registry.py`, `development_tools/imports/generate_module_dependencies.py`, `development_tools/legacy/fix_legacy_references.py`, `development_tools/tests/run_test_coverage.py`) have comprehensive test coverage (55+ tests) using a synthetic fixture project at `tests/fixtures/development_tools_demo/`.

For detailed guidance on development tools testing, see [DEVELOPMENT_TOOLS_TESTING_GUIDE.md](tests/DEVELOPMENT_TOOLS_TESTING_GUIDE.md).

For detailed definitions and examples, see section 2. "Test Layout and Types" in [TESTING_GUIDE.md](tests/TESTING_GUIDE.md).

---

## 3. Fixtures, Utilities, and Safety

Critical invariants:

- All test writes must stay under `tests/data/` or fixtures' temporary directories.
- Tests must never:
  - Touch real user directories (for example, `%APPDATA%`, `Documents`, home directories).
  - Write to production data paths.
  - Create or modify real Windows scheduled tasks.

Use existing helpers:

- Fixtures in `tests/conftest.py` for:
  - Temporary directories and fake data.
  - Path redirection for user data and config.
  - Logging configuration for tests.
- Helper functions in `tests/test_utilities.py` (or equivalent) for:
  - Creating test users, messages, schedules.
  - Common assertions on logs and outputs.
- Isolation helpers (for example, `tests/test_isolation.py`) for:
  - Any test that might interact with system-like APIs or Task Scheduler.

Test logging:

- Two main log files: `test_run.log` (test execution) and `test_consolidated.log` (component logs).
- `TEST_VERBOSE_LOGS` controls verbosity: 0=WARNING only, 1=INFO for tests, 2=DEBUG for all.
- Logs rotate at 2MB size or 24-hour intervals (session start/end).
- In parallel mode, per-worker logs are consolidated at session end.

Scheduler rules:

- Always mock scheduler integrations that would create or modify tasks (for example, `scheduler_manager.set_wake_timer` and related calls).
- Never call `schtasks` or similar system commands directly from tests.

If you need new helpers or fixtures, define them in the shared locations above rather than scattering them across test files.

---

## 4. Running Automated Tests

Preferred commands (via `run_tests.py`):

- Run all tests (parallel by default, if configured):

  ```bash
  python run_tests.py
  ```

- Run only unit tests:

  ```bash
  python run_tests.py --mode unit
  ```

- Run only integration tests:

  ```bash
  python run_tests.py --mode integration
  ```

- Disable parallel execution:

  ```bash
  python run_tests.py --no-parallel
  ```

- Run with coverage:

  ```bash
  python run_tests.py --coverage
  ```

When focusing on a small subset:

- Use pytest directly:

  ```bash
  pytest tests/unit/test_example.py
  pytest tests/unit/test_example.py::TestExample::test_case
  pytest -m "integration and not slow"
  ```

If you add or change command-line options, update `run_tests.py`, `pytest.ini`, and section 4 of [TESTING_GUIDE.md](tests/TESTING_GUIDE.md).

---

## 5. Parallel Execution and Coverage

Parallel execution:

- Expected default: tests run in parallel using `pytest-xdist` (for example, `-n auto`).
- Use `--no-parallel` for:
  - Debugging flaky tests.
  - Tests that touch shared resources and cannot be isolated easily.

`no_parallel` marker:

- Use `@pytest.mark.no_parallel` **only** when:
  - Tests depend on shared external resources that cannot be isolated.
  - Refactoring for parallel safety is not feasible.
- Document the reason in a comment in the test file.

Coverage:

- Enable via:

  ```bash
  python run_tests.py --coverage
  ```

- Treat coverage as guidance:
  - Focus on critical paths (scheduling, delivery, error handling, AI behavior).
  - Do not chase 100% coverage at the cost of clarity.

For rationale and examples, see sections 5.1-5.3 in [TESTING_GUIDE.md](tests/TESTING_GUIDE.md).

---

## 6. Writing and Extending Tests

Placement rules:

- Use the correct directory (`unit`, `integration`, `behavior`, `ui`) based on behavior.
- Choose clear file and test names that describe what is being verified.

Marker standards (must stay aligned with `pytest.ini` and section 6 in [TESTING_GUIDE.md](tests/TESTING_GUIDE.md)):

- Every test must have **exactly one** category marker:
  - `unit`, `integration`, `behavior`, or `ui`.
- Add feature markers as needed, for example:
  - `tasks`, `scheduler`, `checkins`, `messages`, `analytics`,
    `user_management`, `communication`, `ai`.
- Use:
  - `slow` for long-running tests.
  - `fast` (optional) for very quick tests.
  - `asyncio` for async tests.
  - `no_parallel` when absolutely necessary (see section 5).
  - `critical`, `regression`, `smoke` for quality tiers.

Examples (pattern only; do not copy literally):

```python
import pytest

@pytest.mark.unit
@pytest.mark.tasks
def test_create_task_valid_payload():
    ...

@pytest.mark.integration
@pytest.mark.communication
@pytest.mark.slow
@pytest.mark.no_parallel
def test_discord_delivery_flow():
    ...
```

If you add or rename markers:

- Update `pytest.ini`.
- Update this section and the equivalent part of [TESTING_GUIDE.md](tests/TESTING_GUIDE.md).

Use fixtures and helpers:

- Prefer fixtures from `tests/conftest.py`.
- Prefer helpers from `tests/test_utilities.py` and isolation tools from `tests/test_isolation.py`.

---

## 7. Debugging and Troubleshooting

On any test failure:

1. Re-run the failing test with high verbosity:

   ```bash
   pytest -vv path/to/test_file.py::test_name
   ```

2. Check logs:
   - Test run logs (for example, `test_run.log`, `test_consolidated.log`).
   - Component logs under `logs/` if enabled.

3. If it fails only in parallel runs:
   - Re-run with:

     ```bash
     python run_tests.py --no-parallel
     ```

   - Investigate:
     - Shared files or directories.
     - Global state or singletons.
     - External services.

Routing to other AI docs:

- See Section 2 ("Architecture Overview") and section 3 ("Usage Patterns") in [AI_ERROR_HANDLING_GUIDE.md](ai_development_docs/AI_ERROR_HANDLING_GUIDE.md) for required error-handling constraints and routing.
- See Section 2 ("Logging Architecture") and section 3 ("Log Levels and When to Use Them") in [AI_LOGGING_GUIDE.md](ai_development_docs/AI_LOGGING_GUIDE.md) for required logging behavior when writing or testing code.

Refer to section 7 of [TESTING_GUIDE.md](tests/TESTING_GUIDE.md) for detailed troubleshooting guidance.

---

## 8. Manual and Channel-Specific Testing Overview

Automated tests do not cover everything. Some changes require manual or channel-specific testing.

When manual testing is required (examples, not exhaustive):

- Changes to scheduling rules or reminder behavior.
- Significant UI changes (dialogs, flows, validation).
- Changes to Discord or email behavior.
- Changes to AI conversation flows or prompts.

Routing:

- For general manual testing flows (startup, shutdown, scheduling, UI, email):
  - Use [MANUAL_TESTING_GUIDE.md](tests/MANUAL_TESTING_GUIDE.md), especially:
    - Section 2. "Core Manual Flows".
    - Section 3. "UI Manual Testing".
    - Section 4. "Scheduling & Reminder Manual Tests".
- For Discord-specific manual testing of task reminder flows:
  - Use [MANUAL_DISCORD_TEST_GUIDE.md](tests/MANUAL_DISCORD_TEST_GUIDE.md), especially:
    - Section 1. "Prerequisites".
    - Section 2. "Task Reminder Follow-up Flow Testing".
    - Section 7. "Quick Test Checklist".
- For AI conversation and functionality testing:
  - Use [SYSTEM_AI_FUNCTIONALITY_TEST_GUIDE.md](tests/SYSTEM_AI_FUNCTIONALITY_TEST_GUIDE.md), especially:
    - Section 1. "Quick Start".
    - Section 2. "Test Suite Structure".
    - Section 6. "Test Features".
    - Section 7. "Test Categories".

This AI file should not duplicate those manuals. It only tells you **which** manual to use and **when**.

For high-level AI subsystem behavior that these tests validate, see [SYSTEM_AI_GUIDE.md](ai/SYSTEM_AI_GUIDE.md).

---

## 9. Memory Profiling and Resource Management

During parallel test execution, system memory usage can reach 95-98%, which is normal but should be understood and monitored.

**Why memory gets high:**
- pytest-xdist workers (6 workers × ~1-2GB each = 6-12GB)
- Test data accumulation, Python objects, file handles
- Windows memory management behavior

**Current mitigations:**
- Streaming log consolidation
- Periodic garbage collection (every 100 tests)
- Critical memory termination (auto-terminate at 98%)
- Resource monitoring (warnings at 90%, critical at 95%)

**Tools:**
- `scripts/testing/test_memory_profiler.py` - Profile memory usage per test
- `scripts/testing/verify_process_cleanup.py` - Verify process cleanup works
- `scripts/testing/read_backup_results.py` - Read backup test results

**Recommendations:**
- Monitor but don't panic - high memory is expected during parallel tests
- Reduce workers if needed (`--workers 2` instead of 4 or 6)
- Run tests in smaller batches (`--mode fast`)
- Profile memory-heavy tests to identify optimization opportunities

For detailed explanations and usage examples, see section 9 in [TESTING_GUIDE.md](tests/TESTING_GUIDE.md).