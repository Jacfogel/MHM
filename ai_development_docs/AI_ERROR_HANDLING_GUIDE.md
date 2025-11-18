> **File**: ai_development_docs/AI_ERROR_HANDLING_GUIDE.md

# AI Error Handling Guide

This document is a compact reference for how to use MHM's centralized error handling when editing code or tests.

For detailed explanation, rationale, and extended examples, see matching sections in `core/ERROR_HANDLING_GUIDE.md`.

---

## 1. Purpose and Design Principles

- Use a **single shared `ErrorHandler`** instead of ad-hoc try/except.
- Ensure errors are consistently **logged**, **categorized**, and **observable**.
- Keep user-facing messages clean while **logs remain detailed**.
- Support error-coverage analysis and audits.

Core implementation: `core/error_handling.py`.

Key principles:

- Prefer **declarative decorators** over scattered manual try/except.
- Ensure every non-trivial error path is **logged via the central error handler**.
- Keep **user messages and log messages separate** (logs are for operators and developers).

---

## 2. Architecture Overview

Core components are implemented in `core/error_handling.py`:

- **`ErrorHandler` class**  
  - Central orchestration for logging, categorization, and optional recovery behavior.
  - Manages context, severity, and integration with logging.

- **Global instance `error_handler`**  
  - Shared singleton used by decorators and direct calls.

- **Decorator(s) (for example `@handle_errors`)**  
  - Wrap callable entry points (functions, methods, async functions, UI callbacks).
  - Capture exceptions, log them via `error_handler`, and apply standardized recovery logic.

- **Integration with logging**  
  - Errors are logged to the appropriate component logger (see `LOGGING_GUIDE.md`).
  - Critical paths may also be reflected in `logs/errors.log`.

- **Coverage and metrics (`error_handling_coverage.py`)**  
  - Provides tools to measure which error paths are tested.
  - Intended to support audits, CI checks, and quality dashboards.

If you are unsure how to route a new error path, prefer using the decorator and let the global `error_handler` perform the heavy lifting.

## 3. Usage Patterns

### 3.1. Prefer decorators at entry points

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

### 3.2. Direct handler calls when needed

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

## 4. Error Categories and Severity

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

## 5. Error Message Guidelines

When you add or modify error handling:

- Keep user messages short and clear. Do not leak stack traces or sensitive information.
- Use log messages to store technical details:
  - Component (for example `"email"`)
  - Action (for example `"send_message"`)
  - Context (IDs, paths, counts - no secrets)
  - Exception type and message

Where possible, let `ErrorHandler` construct and log the final message, and only supply structured context.

For a deeper explanation, see **"Error Message Guidelines"** in `core/ERROR_HANDLING_GUIDE.md`.

## 6. Configuration and Integration

Error handling integrates with:

- **Logging configuration** (see `LOGGING_GUIDE.md`)  
  - Error logs typically flow into `logs/errors.log` and component logs.

- **Environment flags**  
  - For example, test mode (`MHM_TESTING`) may alter how aggressively errors are surfaced or whether certain types of errors abort tests.

### 6.1. Logging integration

- Errors are emitted via component loggers (see `ai_development_docs/AI_LOGGING_GUIDE.md`).
- Critical or cross-cutting failures typically appear in:
  - `logs/errors.log`
  - The relevant component log (for example `logs/scheduler.log`).
- Do **not** introduce raw `print` or ad-hoc `logging.getLogger()` for error reporting.
- Route everything through the decorators or the global handler.

## 7. Testing Error Handling

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

## 8. Monitoring and Debugging

Intent of the error handling system is to support:

- Identification of frequent error sources (components, actions, exception types).
- Differentiation between expected and unexpected failures.
- Future integration with dashboards or reports built on:
  - `logs/errors.log`
  - Error-coverage and metrics outputs

When debugging:

- Start from `logs/errors.log` and the relevant component log.
- Look for:
  - Repeated failures of the same action.
  - Unhandled exceptions that escaped decorators.
  - Legacy paths still in use.

### 8.1. Metrics and audits

- Track which components fail most frequently, which error types recur, and how many paths are covered by tests.
- Keep log structure (component, action, context) intact so audit tooling can map failures accurately.
- Ensure new error types are logged through the central handler and covered by tests.

## 9. Legacy and Migration

There may still be:

- Older, ad-hoc try/except blocks that:
  - Log directly to a logger.
  - Print errors or swallow exceptions.

The long-term goal is to migrate these to use `ErrorHandler` and the `@handle_errors` decorator.

Migration guidelines:

- Replace raw `print` and unstructured logging with calls routed through error handling.
- When refactoring legacy entry points:
  - Add `@handle_errors` at the top of the stack where control enters that flow.
- Consolidate repeated error handling logic into the shared error handler.

Legacy compatibility should follow the `LEGACY COMPATIBILITY` logging pattern described in `LOGGING_GUIDE.md` when retaining old entry points or behaviors.

---

## 10. Examples

### 10.1. Decorated background task

```python
from core.error_handling import handle_errors
from core import logger

log = logger.get_component_logger("scheduler")

@handle_errors(component="scheduler", action="run_cycle")
def run_cycle():
    log.info("Starting scheduler cycle")
    # ... work ...
```

### 10.2. Explicit error handling in a low-level helper

```python
from core import error_handling

def read_user_file(path, user_id):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError as exc:
        error_handling.error_handler.handle_error(
            exc,
            component="file_ops",
            action="read_user_file",
            context={"user_id": user_id, "path": path},
        )
        return None
```

## 11. Cross-References

When in doubt about a related topic:

- Logging details -> `ai_development_docs/AI_LOGGING_GUIDE.md`
- Testing behavior -> `ai_development_docs/AI_TESTING_GUIDE.md`
- Development workflow -> `ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md`

For full detail, rationale, and extended examples, refer to `core/ERROR_HANDLING_GUIDE.md`.
