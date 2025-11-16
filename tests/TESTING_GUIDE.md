# MHM Testing Framework

> **File**: `tests/TESTING_GUIDE.md`
> **Audience**: Developers and AI assistants working on MHM  
> **Purpose**: Comprehensive testing framework focused on real behavior, integration scenarios, and side-effect verification  
> **Style**: Technical, comprehensive, actionable  
> **Status**: ACTIVE - Real behavior testing implemented, expanding coverage


## Quick Reference

This section lists the most common testing tasks and where to look.

- How do I run all tests quickly?  
  - Use `python run_tests.py` (defaults to parallel execution with pytest-xdist if installed).
- How do I run only unit or integration tests?  
  - Use `python run_tests.py --type unit` or `python run_tests.py --type integration`.
- How do I disable parallel execution?  
  - Add `--no-parallel` to the command: `python run_tests.py --no-parallel`.
- How do I run tests with coverage?  
  - Use `python run_tests.py --coverage`.
- How do I run a specific test file or test function?  
  - Use pytest directly, for example:  
    - `pytest tests/unit/test_example.py`  
    - `pytest tests/unit/test_example.py::TestExample::test_case`
- Where do I find manual testing steps?  
  - See the "Manual Testing Procedures" section in this guide.
- Where do I find AI-optimized testing guidance?  
  - See `ai_development_docs/AI_TESTING_GUIDE.md`.


## Testing Philosophy and Priorities

The testing strategy for MHM focuses on real-world behavior and resilience:

- Behavior and integration first  
  - Prefer tests that exercise realistic flows across modules (for example, sending a scheduled message through Discord) rather than isolated unit checks only.
- Verify side effects  
  - Tests should confirm that side effects (messages sent, files written, logs generated) occur correctly and safely.
- Guard critical paths  
  - Critical flows (scheduling, message delivery, AI interactions, user data handling) should be covered by a mix of automatic and manual tests.
- Keep tests maintainable  
  - Favor clear fixtures, stable test data, and predictable setup/teardown over clever but fragile patterns.
- Parallel-safe by default  
  - New tests should be written to work under parallel execution unless there is a strong reason they cannot.

For more context on how testing fits into the broader development process, see the testing-related sections in `DEVELOPMENT_WORKFLOW.md`.


## Test Types and Structure

Tests are organized by real-world features and workflows to encourage integration testing and real behavior verification.

```
tests/
|-- conftest.py                          # Shared fixtures and configuration
|-- unit/                                # Unit tests by module (core logic)
|-- integration/                         # Integration tests by feature
|-- behavior/                            # Real behavior tests by system
`-- ui/                                  # UI-specific tests
```

High-level types:

- Unit tests  
  - Focus on small, isolated pieces of logic with minimal external dependencies.
- Integration tests  
  - Cover multiple modules and the interactions between them.
- Behavior tests  
  - Exercise end-to-end flows as closely as possible to real usage.
- UI tests  
  - Focus on dialogs, widgets, signals/slots, and visual behavior in the Qt UI.

### Test discovery and scripts directory

- Pytest is configured to discover tests under the `tests/` directory.  
- The `scripts/` directory is explicitly excluded from test discovery (for example, via `norecursedirs` or `--ignore=scripts` in `pytest.ini`).  
- New tests should be added under `tests/` and not under `scripts/`.

Test behavior is also controlled using pytest markers defined in `pytest.ini` (for example: `unit`, `integration`, `behavior`, `ui`, `slow`, `external`, `manual`, `smoke`, `critical`). Use markers to describe the intent and constraints of each test.

## Test Utilities and Infrastructure

Several shared utilities support the test suite. Key elements include:

- `tests/conftest.py`  
  - Centralized fixtures and hooks.  
  - Logging configuration for tests, including per-worker logs when running in parallel.  
  - Test data directory management and path safety checks.
- `tests/test_utilities.py`  
  - Shared helpers for fixtures, fake data, and common assertions.  
  - Prefer these helpers over ad-hoc test code when possible.
- Temporary directories  
  - Tests should use the configured temporary directory structure (for example, `tests/data/tmp`) rather than writing into arbitrary locations.
- Logging for tests  
  - Test runs produce log files (for example, `test_run.log`, `test_consolidated.log`) that are useful for debugging, especially under parallel execution.
- Data shims and guards  
  - Fixtures and helpers ensure user data directories are not accidentally modified during tests.
- File system hygiene  
  - Tests must leave no artefacts outside the `tests` directory.  
  - Keep test data under `tests/data/`, and ensure any generated files are cleaned up during teardown or via fixtures.

### Windows Task Prevention (critical)

On Windows, tests must never create or modify real scheduled tasks:

- Always mock scheduler integrations that would create or update tasks (for example, patch `scheduler_manager.set_wake_timer` and related methods).  
- Never call `schtasks` or similar Task Scheduler commands directly from tests.  
- If Task Scheduler becomes polluted during development, use the cleanup script and guidance provided in the repository (for example, a `cleanup_windows_tasks.py` script and associated PowerShell commands).

For detailed infrastructure behavior and configuration, refer to the fixtures and comments in `tests/conftest.py`, `tests/test_utilities.py`, and the logging patterns described in `logs/LOGGING_GUIDE.md` and `AI_LOGGING_GUIDE.md`.

## Running Tests

This section covers the main ways to run tests.

### Using run_tests.py (recommended)

The `run_tests.py` script provides a safer, standardized entry point for running tests.

Common examples:

```bash
# Run all tests (parallel by default)
python run_tests.py

# Run only unit tests
python run_tests.py --type unit

# Run only integration tests
python run_tests.py --type integration

# Run all tests without parallel execution
python run_tests.py --no-parallel

# Run with coverage reporting
python run_tests.py --coverage

# Run with explicit worker count (for example, 2 workers)
python run_tests.py --workers 2
```

Key points:

- Parallel execution is enabled by default (see "Parallel Execution" below).  
- Use `--no-parallel` when debugging test issues or when working on tests that interact with shared resources.  
- Coverage flags collect code coverage metrics during the run.

### Using pytest directly

You can also call pytest directly for targeted runs:

```bash
# Run a single file
pytest tests/unit/test_example.py

# Run a single test
pytest tests/unit/test_example.py::TestExample::test_case

# Run tests with markers
pytest -m "unit and not slow"
```

When using pytest directly, remember that you are bypassing `run_tests.py` safety defaults. Use the same logging and path patterns described in this guide.


## Parallel Execution

Parallel execution uses pytest-xdist to run tests across multiple workers. It is powerful but can expose race conditions and resource conflicts.

### How parallel execution is enabled

- `run_tests.py` adds `-n auto` or `-n <workers>` when parallel execution is enabled.  
- By default, `run_tests.py` runs tests in parallel unless `--no-parallel` is specified.  
- `tests/conftest.py` configures per-worker log files and environment variables to reduce file locking issues.

### Risks and constraints

Parallel runs can fail even when serial runs pass due to:

- Shared files or directories that are not properly isolated per test.  
- Global mutable state or singletons that are not reset between tests.  
- Interactions with external resources (network, Discord, email, filesystem) that cannot safely handle concurrent access.

When a test fails only under parallel execution:

- Re-run the same tests with `--no-parallel`.  
- If the test passes serially, investigate for race conditions, shared state, or resource conflicts.  
- Consider whether the test should be reworked to be parallel-safe.

### `no_parallel` marker

Tests that cannot be made parallel-safe should be marked explicitly:

```python
import pytest

@pytest.mark.no_parallel
def test_critical_singleton_behavior():
    ...
```

Intended usage:

- Use `@pytest.mark.no_parallel` for tests that modify real files, use shared resources, or require exclusive access to external systems.  
- Keep the number of `no_parallel` tests as small as possible and document the reason in comments.  
- Prefer making tests parallel-safe where feasible (for example, by isolating state or using per-test temp directories).

In the future, `run_tests.py` and pytest configuration may be updated to:

- Run parallel-safe tests with xdist.  
- Run `no_parallel` tests separately in serial mode.

Even before that is fully wired, the marker is useful for identifying tests that need special attention.

## Manual Testing Procedures

Some behaviors are difficult or impractical to cover through automation alone. This section consolidates the manual testing guidance previously found in `MANUAL_TESTING_GUIDE.md`.

### When to perform manual testing

Manual testing is especially important:

- Before tagging a release or deploying to a new environment.  
- After major changes to the UI, scheduling logic, or communication flows.  
- When fixing bugs that are heavily UX-related or require real integrations.

### Core manual testing flows

At a minimum, perform these flows before releases:

1. **Application startup and shutdown**
   - Start the background service and UI using the standard commands in `HOW_TO_RUN.md`.  
   - Confirm logs are created, and no unexpected errors appear on startup or shutdown.

2. **Discord integration (real server)**
   - Invite the bot to a test server.  
   - Verify that commands (for example, check-ins, cancellations, help) work as expected.  
   - Confirm that messages appear in the correct channels and DMs.  
   - Check error behavior when invalid commands are issued.

3. **Email integration (if configured)**
   - Trigger messages or notifications via email.  
   - Confirm emails are sent and formatted correctly.  
   - Verify that retries, failures, and error logs behave as expected.

4. **Scheduling and reminders**
   - Configure a small set of messages and schedules.  
   - Verify reminders fire at reasonable times and within the intended periods.  
   - Confirm that cancellations, snoozes (if implemented), and rescheduling behave correctly.

5. **UI workflows (Qt)**
   - Open and close main dialogs and common configuration screens.  
   - Perform basic CRUD operations on messages and schedules.  
   - Confirm that validation errors are displayed clearly and that invalid input is rejected gracefully.

### UI-focused checklists

When manually testing the UI:

- Layout and visuals  
  - Dialogs are appropriately sized, aligned, and use consistent styling.  
  - Text is readable and labels are clear.

- Navigation  
  - Users can tab through fields logically.  
  - Keyboard shortcuts and standard keys (Enter, Escape) behave as expected.  
  - Buttons and menu items perform the actions they advertise.

- Feedback and errors  
  - Error messages are clear, specific, and actionable.  
  - Loading or waiting states are clearly indicated.  
  - Validation feedback appears near the relevant fields.

### Reporting manual testing

When documenting manual testing:

- Note which flows were covered and on which environment (local, staging, etc.).  
- Record any unexpected behavior, even if it is not a clear failure.  
- Create or update issues for any bugs or UX concerns discovered.  
- If relevant, extend or adjust automated tests to cover fixed issues.

For more structured or checklist-based manual testing, you can adapt the content of this section into separate documents or issue templates, but this section is the canonical reference.


## Writing and Extending Tests

This section covers how to add and modify tests.

### General guidelines

- Keep tests small and focused on a single concern.  
- Prefer deterministic tests over ones that rely on timing, randomness, or external state.  
- Use descriptive test names that convey behavior and expectation (for example, `test_feature_behavior_expected`).  
- When you discover a missing test, but cannot add it immediately, document the gap clearly via a TODO or issue.  
- Prefer fixtures and shared helpers over ad-hoc setup inside tests.

### Where to put new tests

- New unit tests  
  - Place them in `tests/unit/` alongside tests for the same module or feature.  
- New integration or behavior tests  
  - Place them in `tests/integration/` or `tests/behavior/` depending on scope.  
- New UI tests  
  - Place them in `tests/ui/` and follow existing patterns for dialogs, widgets, and signals/slots.

### Using markers

Add markers to describe intent and constraints:

- `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.behavior`, `@pytest.mark.ui`  
- `@pytest.mark.slow`, `@pytest.mark.external`, `@pytest.mark.file_io`, `@pytest.mark.manual`  
- `@pytest.mark.flaky`, `@pytest.mark.known_issue`, `@pytest.mark.regression`, `@pytest.mark.smoke`, `@pytest.mark.critical`  
- `@pytest.mark.no_parallel` for tests that must not run under parallel execution (for example, tests that modify real files, use shared resources, or require exclusive access).

Markers make it easier to select and filter tests, especially in CI or targeted debugging sessions.

### Test data, fixtures, and helpers

- Use fixtures defined in `tests/conftest.py` and helpers in `tests/test_utilities.py` instead of duplicating setup logic.  
- Keep test data under `tests/data/` and use temporary directories for generated files.  
- Ensure any files created by tests are removed during teardown or via fixtures to avoid artefacts outside `tests/`.

For examples of good patterns, consult existing tests in the repository and the patterns summarized in `AI_TESTING_GUIDE.md`.

## Coverage and Reporting

Coverage helps identify untested or lightly-tested code.

### Running with coverage

Use `run_tests.py` for a standardized coverage run:

```bash
python run_tests.py --coverage
```

This typically integrates with pytest-cov or a similar plugin to produce coverage reports.

### Interpreting coverage

- Coverage percentage is a guide, not a goal by itself.  
- Focus on covering critical behavior paths, error handling, and integration points.  
- Low coverage in low-risk helper modules is less concerning than gaps around critical flows.

Coverage-related configuration and thresholds (if any) live alongside test tooling or CI configuration. For detailed interpretation and tooling integration, see any coverage-specific documentation or CI pipeline configuration files.


## Debugging and Troubleshooting

When tests fail or behave unexpectedly:

- Check the test logs  
  - Inspect `test_run.log` and `test_consolidated.log` for errors and tracebacks.
- Re-run failing tests with more detail  
  - Use `pytest -vv` or add `--no-parallel` to isolate concurrency issues.
- Compare serial vs parallel behavior  
  - If a test passes with `--no-parallel` but fails with parallel execution, investigate for shared state, file conflicts, or external resource limits.
- Use markers to focus runs  
  - For example, `pytest -m "integration and not slow"` to narrow down failures.
- Watch for flakes  
  - If a test sometimes passes and sometimes fails, mark it as `flaky` and investigate timing, ordering, or dependency issues.

For additional error handling and logging strategies, see `core/ERROR_HANDLING_GUIDE.md` and `logs/LOGGING_GUIDE.md`.


## Automation and Channel-Specific Tests

Some tests focus on specific communication channels or automation flows:

- Discord tests  
  - Use markers such as `external`, `communication`, or any Discord-specific markers defined in `pytest.ini`.  
  - Prefer using test or sandbox servers to avoid polluting real channels.

- Email tests  
  - Use test accounts or sandbox environments.  
  - Avoid sending email to real users during automated runs.

- AI and service tests  
  - Use markers like `ai`, `service`, `behavior` as appropriate.  
  - Where possible, stub or mock external AI APIs while still validating integration behavior.

Channel-specific automation patterns and examples may also be described in `AI_TESTING_GUIDE.md` for faster reference.


## Maintenance and Roadmap

Keeping the test suite healthy is an ongoing task.

- Expand coverage where behavior is critical or fragile.  
- Refactor tests periodically to remove duplication and improve clarity.  
- Reduce the number of `flaky`, `known_issue`, and `manual` tests over time by improving automation and stability.  
- Keep parallel execution safe by:
  - Identifying and fixing race conditions.  
  - Using `no_parallel` only where necessary and documenting why.  
- Align testing improvements with the priorities described in `PROJECT_VISION.md` and `DEVELOPMENT_WORKFLOW.md`.

When in doubt about how to extend or adjust the testing framework, start with this guide, then consult `AI_TESTING_GUIDE.md` for AI-optimized hints and patterns.
