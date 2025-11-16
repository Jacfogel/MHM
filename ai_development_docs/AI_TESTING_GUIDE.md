# AI Testing Guide

> **File**: `ai_development_docs/AI_TESTING_GUIDE.md`  
> **Purpose**: Fast reference for testing commands, patterns, and routing  
> **Style**: Minimal, pattern-focused  

For more detailed guidance, examples, and rationale for any topic in this file, use the matching sections in `tests/TESTING_GUIDE.md`.


## Quick Reference

Use this section to decide how to run tests or where to look next.

- Run all tests (parallel by default):  
  - `python run_tests.py`
- Run by type:  
  - Unit: `python run_tests.py --type unit`  
  - Integration: `python run_tests.py --type integration`
- Disable parallel execution:  
  - `python run_tests.py --no-parallel`
- Run with coverage:  
  - `python run_tests.py --coverage`
- Run a specific test with pytest:  
  - `pytest tests/unit/test_example.py`  
  - `pytest tests/unit/test_example.py::TestExample::test_case`

Core safety and quality rules:

- Use helpers in `tests/test_utilities.py` for fixtures, fake data, and shared assertions.  
- Keep all test data and artefacts inside `tests/` (for example, `tests/data/`) and clean up generated files.  
- Prefer deterministic tests with clear names (for example, `test_feature_behavior_expected`); log gaps via TODOs or issues.  
- Always mock scheduler integrations to prevent real Windows scheduled tasks (for example, patch `set_wake_timer` and related methods).  
- Use `@pytest.mark.no_parallel` for tests that modify real files, share resources, or require exclusive access.


## Testing Philosophy and Priorities

- Favor behavior and integration tests when adding coverage.  
- Verify side effects (messages, files, logs), not just return values.  
- Protect critical paths (scheduling, delivery, AI interactions, user data).  
- Aim for parallel-safe tests; use `no_parallel` only when necessary.


## Test Types and Structure

Layout:

- `tests/unit/` – unit tests for individual modules.  
- `tests/integration/` – integration tests for features and flows.  
- `tests/behavior/` – end-to-end behavior tests.  
- `tests/ui/` – Qt UI tests.  
- `tests/conftest.py` – shared fixtures, hooks, and configuration.

Discovery rules:

- Tests must live under `tests/`.  
- The `scripts/` directory is excluded from pytest discovery (for example via `norecursedirs` / `--ignore=scripts`); do not put tests there.

Placement:

- Pure logic → `unit`.  
- Cross-module flows → `integration` or `behavior`.  
- Dialogs and widgets → `ui`.


## Test Utilities and Infrastructure

Key points:

- Shared fixtures and hooks: `tests/conftest.py`.  
- Helpers for fixtures, fake data, and shared assertions: `tests/test_utilities.py`.  
- Use test data and temp paths under `tests/data/`; tests must not leave artefacts outside `tests/`.  
- On Windows, tests must not create real scheduled tasks:
  - Always mock scheduler integrations (for example, `scheduler_manager.set_wake_timer`).  
  - Never call `schtasks` or similar commands directly from tests.

For logging patterns referenced from tests, see `AI_LOGGING_GUIDE.md` and `logs/LOGGING_GUIDE.md`.


## Running Tests

Preferred approach (safe defaults):

- Use `run_tests.py` for most tasks:
  - `python run_tests.py` (parallel, all tests)  
  - `python run_tests.py --type unit`  
  - `python run_tests.py --type integration`  
  - `python run_tests.py --coverage`  
  - `python run_tests.py --no-parallel` when debugging or working with shared resources.

For focused or ad-hoc runs:

- Use pytest directly:
  - `pytest tests/unit/test_example.py`  
  - `pytest -m "integration and not slow"`


## Parallel Execution

Minimal rules:

- `run_tests.py` enables pytest-xdist parallel execution by default (for example, `-n auto` or `-n <workers>`).  
- Use `--no-parallel` when debugging flaky tests or working on tests that touch shared resources.

When failures appear only in parallel runs:

- Suspect shared files, global state, or external services that cannot handle concurrency.  
- Re-run the same tests with `--no-parallel` to confirm.

`@pytest.mark.no_parallel`:

- Use `@pytest.mark.no_parallel` on tests that cannot be made parallel-safe, especially those that modify real files, share resources, or require exclusive access.  
- Keep `no_parallel` usage minimal and document the reason in comments.


## Manual Testing Procedures

When to rely on manual testing:

- Before releases and important deployments.  
- After major UI, scheduling, or integration changes.  
- For UX-heavy features or flows that are hard to automate.

Core flows:

- Application startup and shutdown.  
- Discord integration on a real test server.  
- Email integration (if configured).  
- Scheduling and reminders (creating, sending, cancelling).  
- UI workflows: opening dialogs, editing messages and schedules, error handling.


## Writing and Extending Tests

Placement:

- Put new tests in the appropriate directory (`unit`, `integration`, `behavior`, `ui`).  
- Use pytest markers from `pytest.ini` to describe type and constraints (for example, `unit`, `integration`, `behavior`, `ui`, `slow`, `external`, `manual`, `smoke`, `critical`).  
- Use `@pytest.mark.no_parallel` for tests that must not run in parallel.

Quality rules:

- Prefer deterministic tests with clear naming (for example, `test_feature_behavior_expected`).  
- Use fixtures in `tests/conftest.py` and helpers in `tests/test_utilities.py` instead of custom one-off setups.  
- When you see gaps you cannot fill immediately, suggest adding TODOs or issues.


## Coverage and Reporting

- Use `python run_tests.py --coverage` to collect coverage.  
- Treat coverage as a guide; emphasize behavior and critical-path coverage over hitting a percentage.  
- For CI integration or thresholds, consult the coverage configuration used by the project.


## Debugging and Troubleshooting

When tests fail:

- Suggest checking logs (for example, `test_run.log`, `test_consolidated.log`).  
- Re-run failing tests with:
  - `pytest -vv`  
  - `python run_tests.py --no-parallel` to isolate concurrency issues.

If a failure occurs only in parallel runs:

- Investigate shared file usage, global state, or external service limits.

For error-handling and logging patterns that surface in test failures, see `AI_ERROR_HANDLING_GUIDE.md` and `AI_LOGGING_GUIDE.md`.


## Automation and Channel-Specific Tests

AI view:

- Discord tests:
  - Use markers such as `external`, `communication`, or any Discord-specific markers in `pytest.ini`.  
  - Prefer test or sandbox servers.

- Email tests:
  - Use test accounts and sandbox environments; avoid real recipients.

- AI and service tests:
  - Use `ai`, `service`, or `behavior` markers as appropriate.  
  - Prefer stubs/mocks for external AI calls while still validating integration paths.

- AI functionality tests:
  - Test plan: `tests/AI_FUNCTIONALITY_TEST_PLAN.md`.  
  - Runner: `tests/ai/run_ai_functionality_tests.py`.  
  - Consolidated results: typically under `tests/ai/results/ai_functionality_test_results_latest.md`.


## Maintenance and Roadmap

High-level AI guidance:

- Expand coverage around critical and fragile areas.  
- Reduce `flaky`, `known_issue`, and `manual` tests by improving automation.  
- Keep tests parallel-safe where possible and use `no_parallel` only when necessary.  
- Align testing improvements with `AI_DEVELOPMENT_WORKFLOW.md` and `PROJECT_VISION.md`.

