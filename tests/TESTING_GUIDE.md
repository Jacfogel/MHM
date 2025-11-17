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
  - Use `python run_tests.py --mode unit` or `python run_tests.py --mode integration`.
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
  - Prefer tests that exercise realistic flows across modules (for example, a message moving from schedule creation to actual delivery through Discord) rather than isolated unit checks only.
- Verify side effects  
  - Tests should confirm that side effects (messages sent, files written, logs generated) occur correctly and safely.
- Guard critical paths  
  - Prioritize coverage for core scheduling, communication, user data handling, and error handling paths.
- Safety and isolation  
  - Tests must not create real Windows scheduled tasks, must not write outside the `tests` directory, and must not corrupt user data.
- Parallel-friendly by default  
  - Treat pytest-xdist parallel execution as the default path; mark truly non-parallel-safe tests explicitly with `no_parallel`.

Where deeper technical detail is needed, see `ai_development_docs/AI_TESTING_GUIDE.md` for a compact view and use this document for full patterns and rationale.


## Test Layout and Discovery

Pytest configuration is defined in `pytest.ini` and `tests/conftest.py`.

Key points:

- Pytest is configured to discover tests under the `tests/` directory.  
- The `scripts/` directory is explicitly excluded from test discovery (for example, via `norecursedirs` or `--ignore=scripts` in `pytest.ini`).  
- New tests should be added under `tests/` and not under `scripts/`.

Test behavior is also controlled using pytest markers defined in `pytest.ini`. These include markers such as:

- `unit`, `integration`, `behavior`, `ui`  
- `slow`, `external`, `manual`, `smoke`, `critical`  
- `no_parallel`, `no_data_shim`, and other constraints

Use markers to describe the intent and constraints of each test.


## Test Utilities and Infrastructure

Several shared utilities support the test suite. Key elements include:

- `tests/conftest.py`  
  - Centralized fixtures and hooks.  
  - Logging configuration for tests, including per-worker logs when running in parallel.  
  - Test data directory management and path safety checks.
- `tests/test_utilities.py`  
  - Shared helpers for fixtures, fake data, and common assertions.  
  - Prefer these helpers over ad-hoc test code when possible.
- `tests/test_isolation.py`  
  - Helpers for isolating Windows Task Scheduler and other system calls (for example, `IsolationManager`, `mock_system_calls`, `verify_no_real_tasks_created`).  
  - Use these utilities for tests that might otherwise create real Windows tasks or other system resources.  
- Temporary directories  
  - Tests should use the configured temporary directory structure under `tests/data/` (for example, `tests/data/tmp`) rather than writing into arbitrary locations.
- Logging for tests  
  - Test runs produce log files (for example, `test_run.log`, `test_consolidated.log`) that are useful for debugging, especially under parallel execution.
- Data shims and guards  
  - Fixtures and helpers ensure user data directories are not accidentally modified during tests.
- File system hygiene  
  - Tests must leave no artefacts outside the `tests` directory.  
  - Keep test data under `tests/data/`, and ensure any generated files are cleaned up during teardown or via fixtures.


## Test Types and Structure

Tests are organized by real-world features and workflows to encourage integration testing and real behavior verification.

```text
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

Placement guidelines:

- Place pure logic tests under `unit`.  
- Place cross-module flows under `integration` or `behavior`.  
- Place dialog and widget interaction tests under `ui` (for example, verifying signals, slots, and validation behavior).

### Where to put new tests

- New unit tests  
  - Place them in `tests/unit/` alongside tests for the same module or feature.  
- New integration or behavior tests  
  - Place them in `tests/integration/` or `tests/behavior/` depending on scope.  
- New UI tests  
  - Place them in `tests/ui/` and follow existing patterns for dialogs, widgets, and signals/slots.

## File System Safety and Isolation

The tests must not corrupt real user data or create uncontrolled artefacts.

Key rules:

- All test writes go into `tests/data/` or subdirectories created under it.  
- Paths for user data and configuration are redirected to test-specific directories via `tests/conftest.py`.  
- Tests should not read from or write to real user directories (for example, directories under `%APPDATA%`, `Documents`, or production data paths).

### Windows Task Prevention (critical)

On Windows, tests must never create or modify real scheduled tasks:

- Always mock scheduler integrations that would create or update Task Scheduler entries (for example, patch `scheduler_manager.set_wake_timer` and related methods).  
- Never call `schtasks` or similar Task Scheduler commands directly from tests.  
- If Task Scheduler becomes polluted during development, use the dedicated cleanup mechanisms (for example, `scripts/cleanup_windows_tasks.py` and associated PowerShell commands).

For advanced isolation during tests that might trigger scheduler or other system calls, use `tests/test_isolation.py` (for example, wrap code in `IsolationManager`).  

For detailed infrastructure behavior and configuration, refer to the logging patterns described in `logs/LOGGING_GUIDE.md` and `AI_LOGGING_GUIDE.md`.


## Running Tests

This section covers the main ways to run tests.


### Using run_tests.py (recommended)

The `run_tests.py` script provides a safer, standardized entry point for running tests.

Common examples:

```bash
# Run all tests (parallel by default)
python run_tests.py

# Run only unit tests
python run_tests.py --mode unit

# Run only integration tests
python run_tests.py --mode integration

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

This is useful during focused development or when inspecting specific failures.


## Parallel Execution

Parallel execution is handled via pytest-xdist and is enabled by default when using `run_tests.py`.

### How parallel execution is enabled

- `run_tests.py` adds `-n auto` or `-n <workers>` when parallel execution is enabled.  
- By default, `run_tests.py` runs tests in parallel unless `--no-parallel` is specified.  
- `tests/conftest.py` configures per-worker log files and environment variables to reduce file locking issues.

### Risks and constraints

Parallel runs can fail even when serial runs pass due to:

- Shared files or directories that are not properly isolated per test.  
- Global mutable state or singletons that are not reset between tests.  
- Interactions with external resources (network, Discord, email, filesystem) that cannot safely handle concurrent access.

### no_parallel marker

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
- `run_tests.py` will run `no_parallel` tests separately in serial mode, after the parallel batch, combining both into a single run.

This marker prevents unstable behavior in parallel runs while keeping the default path fast.

### When a test fails only under parallel execution

- Re-run the same tests with `--no-parallel`.  
- If the test passes serially, investigate for race conditions, shared state, or resource conflicts.  
- Consider whether the test should be reworked to be parallel-safe, or explicitly marked with `@pytest.mark.no_parallel` with a clear comment.

## Coverage and Reporting

Coverage helps identify untested or lightly-tested code and is integrated into the test runner.

### Running with coverage

Use `run_tests.py` for a standardized coverage run:

```bash
python run_tests.py --coverage
```

This integrates with pytest-cov (or a similar plugin) to produce coverage reports.

Typical outputs:

- A `.coverage` data file in the project root or under `tests/`.  
- Optionally, an HTML report (for example, `coverage_html/`) showing per-file and per-line coverage.

### Interpreting coverage

- Coverage percentage is a guide, not a goal by itself.  
- Focus on covering critical behavior paths, error handling, and integration points.  
- Low coverage in low-risk helper modules is less concerning than gaps around critical flows.  
- Use coverage reports to identify fragile or complex areas that need more tests rather than chasing a single global target.

Coverage-related configuration and thresholds (if any) live alongside test tooling or CI configuration. For detailed interpretation and tooling integration, see any coverage-specific documentation or CI pipeline configuration files.

## Manual Testing Procedures

Some behaviors are difficult or impractical to cover through automated tests alone. Manual checks complement the automated suite and are required for certain changes.

This section consolidates manual testing guidance previously found in `MANUAL_TESTING_GUIDE.md`.

### When to perform manual testing

Manual testing is especially important:

- Before tagging a release or deploying to a new environment.  
- After major changes to the UI, scheduling logic, or communication flows.  
- When fixing bugs that are heavily UX-related or require real integrations.

### Core manual testing flows

At a minimum, perform these flows before releases:

1. Application startup and shutdown  
   - Start the app via the normal entry point and ensure it loads without errors.  
   - Confirm clean shutdown (no lingering processes, no critical errors in logs).

2. Scheduling and reminders  
   - Create, edit, and delete schedule periods.  
   - Create reminders and ensure they are sent within the configured windows.  
   - Test snoozing, cancelling, and rescheduling where applicable.

3. Discord integration  
   - Verify the bot connects to the correct server and channels.  
   - Send commands and confirm expected responses and logging.  
   - Validate error handling when Discord is unavailable or misconfigured.

4. Email integration (if enabled)  
   - Verify outbound emails are sent to the correct addresses.  
   - Check for correct handling of failures (for example, SMTP issues).

5. UI workflows (Qt)  
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

This section covers guidelines for writing new tests or improving existing ones.

### Placement and naming

- Place tests in the appropriate directory (`unit`, `integration`, `behavior`, `ui`).  
- Use descriptive names that convey the behavior under test (for example, `test_schedule_creation_valid_input` instead of `test_schedule`).  
- Group related tests into classes only when shared setup or teardown is needed.

### Using markers

Use markers from `pytest.ini` to describe test characteristics:

- `unit`, `integration`, `behavior`, `ui`  
- `slow`, `external`, `manual`, `smoke`, `critical`  
- `no_parallel`, `no_data_shim`, and other constraints

Markers help the runner select appropriate subsets (for example, fast-only tests or behavior tests).

### Using shared fixtures and helpers

- Prefer fixtures from `tests/conftest.py` over ad-hoc setup logic.  
- Use helpers in `tests/test_utilities.py` for creating mock data, users, or configuration.  
- Use `tests/test_isolation.py` utilities when tests might touch scheduler or system-level calls.

### Quality expectations

- Tests should be deterministic and not rely on wall-clock timing or external services unless clearly marked (for example, `slow` or `external`).  
- Prefer clear, assertive expectations and avoid overly broad assertions.  
- Where behavior is intentionally not covered, document the gap (for example, TODOs or issues) rather than silently ignoring it.

## Debugging and Troubleshooting

When tests fail:

- Inspect logs (`test_run.log`, `test_consolidated.log`) for stack traces, warnings, and error context.  
- Rerun failing tests with increased verbosity:

```bash
pytest -vv path/to/test_file.py::test_name
```

- If failures occur only under parallel execution, rerun with `--no-parallel` to isolate concurrency issues.  
- Use diagnostic tests such as `tests/debug_file_paths.py` when dealing with complex path or data-location issues.

For error-handling and logging patterns that frequently appear in failures, see:

- `core/ERROR_HANDLING_GUIDE.md` and `ai_development_docs/AI_ERROR_HANDLING_GUIDE.md`  
- `logs/LOGGING_GUIDE.md` and `ai_development_docs/AI_LOGGING_GUIDE.md`


## Automation and Channel-Specific Tests

Some tests focus on specific communication channels or automation flows.

- Discord tests  
  - Use markers such as `external`, `communication`, or any Discord-specific markers defined in `pytest.ini`.  
  - Prefer using test or sandbox servers to avoid polluting real channels.  
  - Validate both successful paths and error handling (for example, missing permissions or network issues).

- Email tests  
  - Use test accounts or sandbox environments.  
  - Avoid sending email to real users during automated runs.  
  - Where possible, mock or stub the email transport while verifying that messages are constructed correctly.

- AI and service tests  
  - Use markers like `ai`, `service`, `behavior` as appropriate.  
  - Where possible, stub or mock external AI APIs while still validating integration behavior.  
  - Ensure error handling paths are covered for timeouts, bad responses, or configuration errors.

Channel-specific automation patterns and examples may also be described in `AI_TESTING_GUIDE.md` for faster reference.

## Maintenance and Roadmap

The testing framework will continue to evolve. Priorities include:

- Expanding coverage around critical and fragile areas (scheduling, messaging, error handling).  
- Reducing reliance on manual tests by adding automation where feasible.  
- Improving parallel-safety by fixing shared state issues and minimizing `no_parallel` usage.

Align testing improvements with the overall project vision described in `PROJECT_VISION.md` and the development process described in `DEVELOPMENT_WORKFLOW.md`.
