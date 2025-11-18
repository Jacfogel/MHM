> **File**: core/ERROR_HANDLING_GUIDE.md

# Error Handling Guide

This guide describes the centralized error handling system in MHM, how it integrates with logging, and how to use it safely in new or existing code.

For a compact reference targeted at AI collaborators, see `ai_development_docs/AI_ERROR_HANDLING_GUIDE.md`. That document points back here for deeper explanation and examples.

---

## 1. Purpose and Design Principles

The error handling system exists to:

- Provide a **single, consistent pattern** for capturing and logging errors.
- Distinguish between **expected**, **recoverable**, and **critical** failures.
- Ensure user-facing errors are **clear and actionable**.
- Feed **metrics and coverage** tools so we can see which paths are tested and which are not.
- Support gradual **migration away from ad-hoc try/except** blocks and legacy patterns.

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

---

## 3. Usage Patterns

### 3.1. Decorated functions (preferred)

Use the decorator on entry points where errors should be centrally captured:

```python
from core.error_handling import handle_errors
from core import logger

log = logger.get_component_logger("scheduler")

@handle_errors(component="scheduler", action="run_cycle")
def run_scheduler_cycle():
    log.info("Starting scheduler cycle")
    # ... work ...
```

Common places to use the decorator:

- Background tasks and scheduler jobs
- Command handlers
- UI event handlers (where integration with Qt is appropriate)
- Service entry points (for example, Discord/Email message handlers)

The decorator typically:

- Catches unexpected exceptions.
- Logs structured details (component, action, exception type, traceback).
- Optionally reports or flags the error for metrics.
- Returns a sensible fallback (for example, `None`, a default value, or a standardized error result).

### 3.2. Direct calls to `error_handler`

For certain cases, you may need to call the handler directly:

```python
from core import error_handling

try:
    risky_operation()
except Exception as exc:
    error_handling.error_handler.handle_error(
        exc,
        component="backup_manager",
        action="risky_operation",
        context={"user_id": user_id, "path": path},
    )
```

Direct calls are appropriate when:

- You are inside a narrow helper function where decorating the entire call stack is not practical.
- You are bridging external libraries and want to normalize their exceptions into the shared system.
- You need to report an error that has already been caught but must be recorded consistently.

As the project evolves, most new code should favor `@handle_errors` at appropriate boundaries. Direct calls are permitted, but avoid scattering them widely.

---

## 4. Error Categories and Severity

Internally, the error handler distinguishes between different categories (even if not all are formalized as enums yet). When designing or refactoring error paths, think in terms of:

- **User input / validation errors**  
  Example: invalid schedule time, missing required fields.  
  Expected, should be handled gracefully with user-facing messages.  
  Typically logged at `INFO` or `WARNING` with structured context.

- **Recoverable operational errors**  
  Example: transient network issues, temporary file lock, email send failure.  
  Logged at `WARNING` or `ERROR` depending on impact.  
  Often retried or reported to user with suggestions.

- **Internal bugs / invariants broken**  
  Example: unexpected state, impossible condition reached, coding mistakes.  
  Logged at `ERROR` or `CRITICAL`.  
  Should generally be fixed rather than silently handled.

- **External dependency failures**  
  Example: Discord API outage, email provider issues, AI model endpoint down.  
  Logged with explicit external service identifiers and correlation IDs where possible.

- **Configuration and environment errors**  
  Example: missing tokens, invalid `.env` values, file system permissions.  
  Often detected at startup; may be fatal if core functionality cannot run.

Use these categories to choose log levels and to shape messages for later troubleshooting.

---

## 5. Error Message Guidelines

Separate user-facing messages from log messages.

### 5.1. User-facing messages

- Short, clear, and non-technical.
- Focus on what the user can do (if anything).
- Avoid stack traces, internal names, or raw exception text.

Example:

```text
"Could not send your email right now. Please check your internet connection and try again."
```

### 5.2. Log messages

- Include enough context for developers to understand what failed and why.
- Reference component and action (for example `component="email"`, `action="send_message"`).
- Capture exception details and stack trace (for example `exc_info=True`).
- Avoid secrets (tokens, passwords, full message content unless necessary and safe).

Conceptual example:

```text
2024-09-05 12:34:56 | ERROR | email | Email send failed (user_id=123, message_id=abc) | SMTPTimeoutError ...
```

The error handler should be the primary place that final log messages and structures are composed.

---

## 6. Configuration and Integration

Error handling integrates with:

- **Logging configuration** (see `LOGGING_GUIDE.md`)  
  - Error logs typically flow into `logs/errors.log` and component logs.

- **Environment flags**  
  - For example, test mode (`MHM_TESTING`) may alter how aggressively errors are surfaced or whether certain types of errors abort tests.

If additional error-related environment variables are introduced (for example, toggling specific recovery behaviors or error-coverage settings), they should be documented here and in `config.py` comments.

---

## 7. Testing Error Handling

Error handling is tested in multiple ways:

- **Unit/integration tests**  
  - For example: `tests/test_error_handling_improvements.py`.  
  - Verify decorator behavior, logging, and recovery results.

- **Coverage tooling**  
  - `error_handling_coverage.py` analyzes which error paths have test coverage.  
  - Can be integrated into automated workflows via `ai_development_tools/ai_tools_runner.py` commands to generate reports.

Guidelines:

- When adding new error paths or changing existing ones:
  - Add or update tests to cover both the success path and the failure path.
  - Verify that exceptions are correctly captured by decorators or direct handler calls.
  - Where practical, assert on logs or metrics using helpers in `tests/test_utilities.py`.

For AI-optimized patterns and how this interacts with the broader test workflow, see `ai_development_docs/AI_TESTING_GUIDE.md` and `ai_development_docs/AI_ERROR_HANDLING_GUIDE.md`.

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

If an error is noisy, consider:

- Adjusting log levels (without hiding important problems).
- Introducing a more specific category or message in `error_handling.py`.
- Improving tests so regressions are caught earlier.

---

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

## 11. Cross-References

- Logging implementation guidance -> `logs/LOGGING_GUIDE.md`.
- Testing approaches for error handling -> `tests/TESTING_GUIDE.md`.
- AI-facing summary -> `ai_development_docs/AI_ERROR_HANDLING_GUIDE.md`.

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

For condensed rules and cross-references, see `ai_development_docs/AI_ERROR_HANDLING_GUIDE.md`.
