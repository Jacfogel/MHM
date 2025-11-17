> **File**: ai_development_docs/AI_ERROR_HANDLING_GUIDE.md

# AI Error Handling Guide

This document is a compact reference for how to use MHM’s centralized error handling when editing code or tests.

For detailed explanation, rationale, and extended examples, see matching sections in `core/ERROR_HANDLING_GUIDE.md`.

---

## 1. Purpose

- Use a **single shared `ErrorHandler`** instead of ad-hoc try/except.
- Ensure errors are consistently **logged**, **categorized**, and **observable**.
- Keep user-facing messages clean while **logs remain detailed**.
- Support error-coverage analysis and audits.

Core implementation: `core/error_handling.py`.

---

## 2. Core Patterns

### 2.1 Prefer decorators at entry points

Use the decorator on functions that form clear entry points:

```python
from core.error_handling import handle_errors
from core import logger

log = logger.get_component_logger("scheduler")

@handle_errors(component="scheduler", action="run_cycle")
def run_scheduler_cycle():
    log.info("Starting scheduler cycle")
    # ... implementation ...
```

Use this for:

- Scheduler tasks
- Command handlers
- UI event handlers (where applicable)
- Service entry points (Discord/Email/AI calls)

Let the decorator route exceptions into `ErrorHandler` and logging.

### 2.2 Direct handler calls when needed

Use direct calls only where a decorator is not practical:

```python
from core import error_handling

try:
    risky_operation()
except Exception as exc:
    error_handling.error_handler.handle_error(
        exc,
        component="backup_manager",
        action="risky_operation",
        context={"user_id": user_id},
    )
```

Use sparingly; favor decorating higher-level entry points when possible.

---

## 3. Categories and Levels (Mental Model)

When choosing how to log and handle an error, think in categories:

- **Validation / user input**  
  - Expected, recoverable; usually `INFO` or `WARNING`.

- **Recoverable operational error** (network, file lock, temporary resource issue)  
  - Usually `WARNING` or `ERROR`.

- **Internal bug / invariant broken**  
  - Unexpected; usually `ERROR` or `CRITICAL`; should be fixed.

- **External dependency failure** (Discord, email server, AI endpoint)  
  - Log with component and dependency identifiers.

- **Configuration/environment** (missing tokens, invalid settings)  
  - Often discovered at startup; may be fatal.

Actual levels are set by the error handler and logging configuration, but this model should guide your implementation.

For detailed human examples, see **"Error Categories and Severity"** in `core/ERROR_HANDLING_GUIDE.md`.

---

## 4. Logging Integration

The error handler integrates directly with the logging system:

- Errors are emitted via component loggers (see `ai_development_docs/AI_LOGGING_GUIDE.md`).
- Critical or cross-cutting failures typically appear in:
  - `logs/errors.log`
  - The relevant component log (for example `logs/scheduler.log`).

When editing error handling:

- Do **not** introduce raw `print` or ad-hoc `logging.getLogger()` for error reporting.
- Route everything through the decorators or the global handler.

---

## 5. Message Guidelines

When you add or modify error handling:

- Keep user messages short and clear. Do not leak stack traces or sensitive information.
- Use log messages to store technical details:
  - Component (for example `"email"`)
  - Action (for example `"send_message"`)
  - Context (IDs, paths, counts – no secrets)
  - Exception type and message

Where possible, let `ErrorHandler` construct and log the final message, and only supply structured context.

For a deeper explanation, see **"Error Message Guidelines"** in `core/ERROR_HANDLING_GUIDE.md`.

---

## 6. Testing Error Handling

Related pieces:

- Tests (for example `tests/test_error_handling_improvements.py`) validate:
  - Decorator behavior
  - Logging and recovery

- `error_handling_coverage.py` and related tools:
  - Analyze which error paths have tests.
  - Can be run via `ai_development_tools/ai_tools_runner.py` commands.

When modifying or adding error handling:

- Add tests that:
  - Exercise success and failure paths.
  - Assert that exceptions are captured by the decorator or handler.
- Use fixtures and helpers in `tests/test_utilities.py` where possible.

Coordinate with:

- `ai_development_docs/AI_TESTING_GUIDE.md` for testing patterns.
- `ai_development_docs/AI_LOGGING_GUIDE.md` for logging expectations.

---

## 7. Monitoring and Metrics

The long-term goal is for error handling to feed:

- Metrics on:
  - Which components fail most frequently
  - Which error types recur
  - How many paths are covered by tests
- Audit and coverage reports (for example, via `error_handling_coverage.py` and AI tooling commands).

When editing error handling, avoid breaking:

- Log structure (component, action, context)
- Integration points relied on by coverage or audit tools

If you introduce new error types or categories, ensure they:

- Are logged through the central handler.
- Are covered by at least basic tests.

---

## 8. Legacy and Migration

You may still find:

- Direct try/except blocks that:
  - Log errors manually
  - Swallow exceptions
  - Use inconsistent messages

Migration guidance:

- Prefer wrapping the relevant function with `@handle_errors`.
- Where manual try/except is required:
  - Normalize behavior via `error_handler.handle_error`.
- Reduce scattered, one-off patterns over time.

Use the `LEGACY COMPATIBILITY` logging pattern (see `ai_development_docs/AI_LOGGING_GUIDE.md` and `logs/LOGGING_GUIDE.md`) when you must keep older entry points or behaviors temporarily.

---

## 9. Cross-References

When in doubt about a related topic:

- Logging details → `ai_development_docs/AI_LOGGING_GUIDE.md`
- Testing behavior → `ai_development_docs/AI_TESTING_GUIDE.md`
- Development workflow → `ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md`

For full detail, rationale, and extended examples, refer to `core/ERROR_HANDLING_GUIDE.md`.
