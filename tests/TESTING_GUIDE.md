# Testing Guide

> **File**: `tests/TESTING_GUIDE.md`  
> **Audience**: Developers and AI assistants working on MHM  
> **Purpose**: Comprehensive testing framework focused on real behavior, integration scenarios, and side-effect verification  
> **Style**: Technical, comprehensive, actionable  
> **Pair**: [AI_TESTING_GUIDE.md](ai_development_docs/AI_TESTING_GUIDE.md)  
> This document is paired with [AI_TESTING_GUIDE.md](ai_development_docs/AI_TESTING_GUIDE.md) and any changes must consider both docs.

---

## 1. Purpose and Scope

MHM's test strategy is built around one core idea: **test real behavior, not just isolated functions**.

This guide explains:

- How tests are laid out and discovered.
- Which types of tests exist and when to use them.
- How fixtures and utilities protect the filesystem and external systems.
- How to run tests safely (including parallel runs and coverage).
- How to add or extend tests using standard markers and patterns.
- How to debug and troubleshoot failures.
- How automated tests relate to manual and channel-specific testing.

Use this guide whenever you:

- Add new features or refactor existing ones.
- Change scheduling, messaging, AI behavior, or UI flows.
- Touch any integration (Discord, email, future channels).
- Need to understand how tests should behave in CI or local runs.

The paired AI doc ([AI_TESTING_GUIDE.md](ai_development_docs/AI_TESTING_GUIDE.md)) provides a routing-first, constraint-focused view for AI tools and automated assistance. This human-facing guide is the canonical source for detailed behavior, rationale, and examples.

---

## 2. Test Layout and Types

Pytest configuration for the project is defined in `pytest.ini` and `tests/conftest.py`. All tests live under the `tests/` directory.

High-level layout:

```text
tests/
|-- conftest.py                          # Shared fixtures and configuration
|-- unit/                                # Unit tests by module (core logic)
|-- integration/                         # Integration tests by feature
|-- behavior/                            # Real behavior tests by system
|-- ui/                                  # UI-specific tests
|-- development_tools/                   # Infrastructure tests for development tools
```

### 2.1. Discovery rules

- Pytest is configured to discover tests under `tests/` only.
- The `scripts/` directory is explicitly excluded from test discovery (for example, via `norecursedirs = scripts` or `--ignore=scripts` in `pytest.ini`).
- New tests **must** be added under `tests/`, not under `scripts/` or random locations.

Naming conventions (pytest defaults):

- Files: `test_*.py` or `*_test.py`.
- Test functions: `def test_something():`.
- Test classes (optional): `class TestSomething:` containing test methods that start with `test_`.

### 2.2. Test types

Tests are organized by real-world features and workflows to encourage integration and behavior testing.

**Unit tests (`tests/unit/`)**

- Focus on small, isolated pieces of logic.
- Minimize external dependencies (no real filesystem, network, or external services).
- Use mocks and fixtures heavily.
- Examples:
  - Pure scheduling calculations.
  - Message formatting functions.
  - Utility helpers.

**Integration tests (`tests/integration/`)**

- Cover interactions between multiple modules and services.
- Exercise realistic flows (for example, a message moving from schedule creation through the sending pipeline).
- May use more realistic data and partial integration with actual components.

**Behavior tests (`tests/behavior/`)**

- Exercise end-to-end flows as closely as practical.
- Often follow "user-does-X, system-responds-with-Y" patterns.
- Validate that side effects (messages sent, logs written, tasks scheduled) occur correctly.

**UI tests (`tests/ui/`)**

- Target Qt dialogs, widgets, and UI workflows.
- Verify signals/slots, validation behavior, and critical UI flows.
- Avoid brittle pixel-perfect assertions; focus on behavior.

**Development tools tests (`tests/development_tools/`)**

- Test development tools and infrastructure components.
- Include sanity tests for configuration, exclusions, constants, and CLI runners.
- Integration coverage relies on **mocked CLI smoke tests** (no subprocesses) so the suite stays fast while still exercising `run_development_tools` routing.
- Error-scenario tests simulate `PermissionError`/`OSError` via monkeypatching instead of modifying real filesystem ACLs-keeps results identical on Windows and Linux.
- **Core analysis tools** have comprehensive test coverage (55+ tests):
  - `development_tools/docs/analyze_documentation_sync.py` - 12 tests for doc pairing validation
  - `development_tools/generate_function_registry.py` - 12 tests for function extraction and registry generation
  - `development_tools/imports/generate_module_dependencies.py` - 11 tests for dependency graph generation
  - `development_tools/legacy/fix_legacy_references.py` - 10 tests for legacy pattern detection and cleanup
  - `development_tools/tests/generate_test_coverage.py` - 10 tests for coverage regeneration and reporting
- Tests use a synthetic fixture project at `tests/fixtures/development_tools_demo/` for isolated testing.
- For detailed guidance on development tools testing, see [DEVELOPMENT_TOOLS_TESTING_GUIDE.md](tests/DEVELOPMENT_TOOLS_TESTING_GUIDE.md).
- Examples:
  - Configuration validation.
  - File exclusion patterns.
  - CLI command execution.
  - AST parsing and code analysis.
  - Documentation synchronization checks.

### 2.3. Where to put new tests

When adding a new test:

- If it exercises **pure logic** in one module, put it in `tests/unit/`.
- If it involves **multiple modules** or services, use `tests/integration/` or `tests/behavior/` depending on scope.
- If it tests **dialogs, widgets, or UI flows**, put it in `tests/ui/`.
- If it tests **development tools** (configuration, CLI runners, tooling), put it in `tests/development_tools/`.

If you are unsure, err toward **integration or behavior tests**. Isolated unit tests are useful, but they should support a real-behavior-first strategy instead of replacing it.

---

## 3. Fixtures, Utilities, and Safety

Tests must be safe: they must not pollute real user data, create real Windows scheduled tasks, or write outside controlled directories. This section describes the tools that enforce those constraints.

### 3.1. Shared fixtures and hooks

`tests/conftest.py` is the central place for:

- Global fixtures.
- Pytest hooks.
- Logging setup for test runs.
- Path redirection for user data and configuration during tests.

Typical responsibilities:

- Configure logs for each worker or test run.
- Redirect user data directories to test-specific locations.
- Provide fixtures to create temporary directories and fake data.

Always prefer existing fixtures from `tests/conftest.py` over writing ad-hoc setup logic inside tests.

### 3.2. Test utilities and helpers

Common helpers are usually defined in utility modules such as:

- `tests/test_utilities.py` (or similarly named helpers module).

These helpers typically provide:

- Factories for creating test users, messages, and schedules.
- Helper functions for asserting logs, side effects, or output.
- Utility functions to wrap common patterns (for example, capturing logs or patching environment variables).

**Guideline:** Before adding a new helper function, check whether the pattern already exists in `tests/test_utilities.py` or similar. Centralizing helper logic keeps tests more consistent and reduces duplication.

### 3.3. Filesystem safety

Core rules:

- All test writes must occur under `tests/data/` or temporary directories created by fixtures.
- Tests must **never** write to or delete files in:
  - Real user directories (for example, `%APPDATA%`, `Documents`, home directories).
  - Production data paths.
- Test data and temporary files should be cleaned up automatically by fixtures or explicit teardown logic.

If you need a new directory for test data:

- Place it under `tests/data/`.
- Name it clearly (for example, `tests/data/tmp`, `tests/data/sample_configs`).
- Ensure tests using it do not leave behind unexpected files outside those locations.

### 3.4. Windows Task Scheduler and external systems

Tests must never create or modify real Windows scheduled tasks or other external system resources.

Typical patterns:

- Always mock scheduler integrations that would create or update Task Scheduler entries (for example, patch `scheduler_manager.set_wake_timer` and related methods).
- Do not call `schtasks` or similar Windows commands directly from tests.
- Use isolation utilities (for example, an `IsolationManager` or similar helper in `tests/test_isolation.py`) for tests that interact with system-like APIs.

If the Windows Task Scheduler becomes polluted during development (for example, from manual experiments), use the dedicated cleanup scripts under `scripts/` (see `scripts/SCRIPTS_GUIDE.md` for details, especially `scripts/cleanup_windows_tasks.py`).

### 3.5. Logging in tests

Tests should integrate cleanly with the logging system described in [LOGGING_GUIDE.md](logs/LOGGING_GUIDE.md) (see section 2. "Logging Architecture" in that guide).

Patterns:

- Use test fixtures to configure log handlers that write to test-specific log files (for example, `test_run.log`, `test_consolidated.log`).
- When debugging a failing test, those test logs are often the first place to look.
- Do not reconfigure logging in each test module unless absolutely necessary; prefer centralized configuration via `tests/conftest.py`.

---

## 4. Running Automated Tests

This section covers how to run automated tests in standard scenarios. It intentionally focuses on a few blessed entry points.

### 4.1. Quick reference

Common commands:

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

- Run all tests without parallel execution:

  ```bash
  python run_tests.py --no-parallel
  ```

- Run with coverage:

  ```bash
  python run_tests.py --coverage
  ```

- Run a specific test file or function with pytest:

  ```bash
  pytest tests/unit/test_example.py
  pytest tests/unit/test_example.py::TestExample::test_case
  ```

### 4.2. Using run_tests.py (recommended entry point)

`run_tests.py` provides a standardized, safer entry point that:

- Applies default markers and options (including parallel execution if available).
- Integrates coverage flags.
- Can be extended to handle CI-specific behavior.

Typical options:

- `--mode unit` / `--mode integration` / (any future modes).
- `--no-parallel` (force serial execution).
- `--workers N` (explicit worker count).
- `--coverage` (enable coverage collection).

Prefer `python run_tests.py` over calling pytest directly when you want "normal" local or CI runs.

### 4.3. Using pytest directly

You can still invoke pytest directly when you need fine-grained control:

```bash
# Run a single test file
pytest tests/unit/test_example.py

# Run tests marked as "unit"
pytest -m "unit"

# Run tests matching multiple markers
pytest -m "integration and not slow"
```

Direct pytest usage is useful when:

- Iterating on a specific failing test.
- Running a subset of tests by markers.
- Debugging marker behavior.

If you add new markers or special options, ensure `pytest.ini` is updated accordingly and that those markers are documented in section 6 ("Writing and Extending Tests") below.

---

## 5. Parallel Execution and Coverage

Parallel execution can greatly speed up tests, but it also introduces new failure modes. Coverage helps you understand which parts of the codebase are tested.

### 5.1. Parallel execution

Parallel execution is typically handled via `pytest-xdist`:

- `run_tests.py` will add `-n auto` (or `-n <workers>`) when parallel execution is enabled.
- By default, tests are expected to be **parallel-safe**, unless explicitly marked otherwise.

Reasons a test might fail only under parallel execution:

- Shared files or directories are not isolated.
- Global mutable state is not reset between tests.
- External services cannot handle concurrent calls correctly.

When debugging parallel issues:

1. Re-run the failing tests with `--no-parallel`:

   ```bash
   python run_tests.py --no-parallel
   ```

2. If the tests pass serially, investigate:
   - Shared directories or files.
   - Global state or singletons.
   - External system limits.

3. Decide whether:
   - The test can be refactored to be parallel-safe, or
   - It should be marked with `@pytest.mark.no_parallel` and documented.

### 5.2. The `no_parallel` marker

Use `@pytest.mark.no_parallel` **sparingly** and only when necessary.

Example:

```python
import pytest

@pytest.mark.integration
@pytest.mark.no_parallel
def test_task_migration_against_real_backup():
    ...
```

Guidelines:

- Document in comments *why* the test cannot be parallelized.
- Keep the number of `no_parallel` tests as small as possible.
- Consider refactoring or adding isolation fixtures before resorting to this marker.

`run_tests.py` can be configured (now or later) to run `no_parallel` tests in a separate serial phase if needed.

### 5.3. Coverage

Coverage is used to understand how much of the codebase is exercised by tests, not as a rigid target.

To run tests with coverage:

```bash
python run_tests.py --coverage
```

This typically integrates with `pytest-cov` and outputs:

- A `.coverage` file in the project root or under `tests/`.
- An optional HTML coverage report directory (such as `coverage_html/`).

Interpretation guidelines:

- Focus coverage on **critical paths**:
  - Scheduling and delivery.
  - Error handling logic.
  - AI pipeline and user data handling.
- A slightly lower coverage percentage is acceptable if the missing lines are low-risk helpers.
- Use coverage to identify fragile areas that need more tests.

---

## 6. Writing and Extending Tests

This section describes how to write new tests and evolve existing ones safely and consistently.

### 6.1. Placement and naming

When creating a new test:

- Choose the correct directory (`unit`, `integration`, `behavior`, `ui`) based on scope (see section 2. "Test Layout and Types").
- Use descriptive file and test names that clearly express behavior:
  - Prefer `test_schedule_creation_valid_input` over `test_schedule`.
  - Group related tests into a class only when you need shared setup/teardown.

### 6.2. Marker standards

Markers are defined in `pytest.ini` and serve as the main mechanism for:

- Selecting subsets of tests.
- Describing test characteristics (feature area, speed, resource needs, quality).

Recommended pattern (subject to alignment with the actual `pytest.ini`):

- **Category markers** (exactly one per test):
  - `unit`, `integration`, `behavior`, `ui`.

- **Feature markers** (zero or more):
  - `tasks`, `scheduler`, `checkins`, `messages`, `analytics`,
    `user_management`, `communication`, `ai`, etc.

- **Speed markers**:
  - `slow` (long-running > 1s, excluded from fast runs).
  - `fast` (optional; for very quick tests).

- **Resource markers**:
  - `asyncio` (async tests).
  - `no_parallel` (cannot be parallelized; see section 5.2).

- **Quality markers**:
  - `critical` (core flows).
  - `regression` (regression tests).
  - `smoke` (basic health checks).

Example:

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

Before adding new markers:

- Update `pytest.ini` to define them.
- Document their intended use in this section.
- Keep the marker set small and purposeful.

### 6.3. Using fixtures and helpers

Follow these guidelines:

- Prefer fixtures from `tests/conftest.py` for:
  - Temporary directories and files.
  - Fake users and configuration.
  - Logging setup and teardown.

- Use helper functions from `tests/test_utilities.py` (or similar) for:
  - Constructing complex payloads (messages, schedules).
  - Common assertions on logs, errors, or outputs.
  - Reusable patterns (for example, "create a user with default settings").

- Do not re-implement the same setup logic in multiple tests; extract it into a fixture or helper.

### 6.4. Quality expectations

- Tests must be **deterministic**:
  - Avoid using real time (or use time-freezing utilities).
  - Avoid using real network calls or external services.
- Make assertions specific and meaningful.
- When known gaps exist:
  - Add TODOs in the tests or issues in your tracker.
  - Reference those gaps when appropriate so they are not forgotten.

---

## 7. Debugging and Troubleshooting

When tests fail, use a consistent process to narrow down the cause.

### 7.1. Logs and artifacts

First, inspect logs and other artifacts produced during the test run:

- Test logs (for example, `test_run.log`, `test_consolidated.log`).
- Component logs under `logs/` if logging is enabled for tests (see `logs/LOGGING_GUIDE.md`, especially section 4. "Component Log Files and Layout").
- Coverage reports (if running with `--coverage`) to see which paths were actually exercised.

Often, test failures will be accompanied by logged exceptions or warnings that make root cause obvious.

### 7.2. Re-running failing tests

Re-run failing tests with higher verbosity:

```bash
pytest -vv path/to/test_file.py::test_name
```

Then:

- If the failure is **consistent**, inspect:
  - Recent code changes in the area.
  - Fixtures and helper functions used by the test.
- If the failure only appears in **parallel** runs:
  - Re-run with `--no-parallel`:
    ```bash
    python run_tests.py --no-parallel
    ```
  - If it passes serially, suspect race conditions, shared state, or external resource conflicts (see section 5).

### 7.3. Error handling and logging patterns

For error handling and logging details:

- See section 2. "Architecture Overview" and section 4. "Error Categories and Severity" in [ERROR_HANDLING_GUIDE.md](core/ERROR_HANDLING_GUIDE.md).
- See [LOGGING_GUIDE.md](logs/LOGGING_GUIDE.md) (especially section 2. "Logging Architecture" and section 4. "Component Log Files and Layout").

Align tests with those patterns:

- Ensure critical errors are logged at the correct level.
- Verify expected recovery behavior (for example, retries, fallbacks, user-visible messages).

---

## 8. Manual and Channel-Specific Testing Overview

Automated tests cannot cover everything. Manual testing and channel-specific checks are required for certain changes and before releases.

### 8.1. When manual testing is required

Manual testing is especially important when:

- Making major changes to:
  - Scheduling logic.
  - UI dialogs and flows.
  - Communication channels (Discord, email, future channels).
  - AI behavior that affects user-facing interactions.
- Preparing for tagged releases or deployments to new environments.
- Fixing bugs that are primarily UX or integration issues.

### 8.2. Manual testing hub

The canonical manual testing checklists live in:

- [MANUAL_TESTING_GUIDE.md](tests/MANUAL_TESTING_GUIDE.md)

That guide provides:

- Core manual flows for:
  - Application startup and shutdown.
  - Scheduling and reminders.
  - UI workflows.
  - Email (if configured).
- How to record results and file issues.
- Triggers that indicate when manual testing is required.

### 8.3. Discord-specific manual testing

For Discord-specific manual flows-especially task reminder follow-up flows-use:

- [MANUAL_DISCORD_TEST_GUIDE.md](tests/MANUAL_DISCORD_TEST_GUIDE.md)
  - Section 1. "Prerequisites".
  - Section 2. "Task Reminder Follow-up Flow Testing".
  - Section 7. "Quick Test Checklist".

Run these tests when:

- Changing Discord task parsing.
- Modifying reminder or follow-up phrasing.
- Adjusting how commands are interpreted in task flows.

### 8.4. AI functionality testing

For AI conversation behavior, routing, and functionality tests, use:

- [SYSTEM_AI_FUNCTIONALITY_TEST_GUIDE.md](tests/SYSTEM_AI_FUNCTIONALITY_TEST_GUIDE.md)
  - Section 1. "Quick Start".
  - Section 2. "Test Suite Structure".
  - Section 6. "Test Features".
  - Section 7. "Test Categories".

For a system-level view of the AI behavior these tests exercise, see [SYSTEM_AI_GUIDE.md](ai/SYSTEM_AI_GUIDE.md).

Run these tests when:

- Changing AI interaction flows.
- Modifying how prompts or responses are constructed.
- Adjusting how AI integrates with message scheduling or user data.

### 8.5. Development tools testing

For development tools testing (analysis tools, CLI runners, infrastructure), use:

- [DEVELOPMENT_TOOLS_TESTING_GUIDE.md](tests/DEVELOPMENT_TOOLS_TESTING_GUIDE.md)
  - Section 1. "Quick Start".
  - Section 4. "Test Fixtures and Isolation".
  - Section 5. "Critical Safety Rules".
  - Section 6. "Portability Considerations".

Run development tools tests when:

- Modifying development tools behavior (analysis, reporting, CLI routing).
- Adding or changing tool functionality.
- Investigating issues with the development tools infrastructure.

Run development tools tests when:

- Modifying development tools behavior (analysis, reporting, CLI routing).
- Adding or changing tool functionality.
- Investigating issues with the development tools infrastructure.

### 8.6. Relationship to this guide

This guide (TESTING_GUIDE.md) defines **how testing works overall** and how automated tests are structured and executed.

The manual guides:

- Provide **concrete step-by-step flows** for manual checks.
- Are **subordinate** to this guide and should remain consistent with its standards and terminology.
- May evolve more frequently as new manual flows are discovered.

When in doubt:

1. Start here to understand the overall framework.
2. Follow routing in this section to pick the correct manual guide.
3. Update both sides (automated and manual tests) when you make significant changes to behavior.
