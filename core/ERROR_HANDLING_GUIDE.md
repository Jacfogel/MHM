# Error Handling Guide

> **File**: `core/ERROR_HANDLING_GUIDE.md`  
> **Audience**: Developers and AI assistants working on MHM  
> **Purpose**: Centralized error handling patterns, categories, and integration rules  
> **Style**: Technical, comprehensive, actionable  
> **Pair**: [AI_ERROR_HANDLING_GUIDE.md](ai_development_docs/AI_ERROR_HANDLING_GUIDE.md)  
> This document is paired with [AI_ERROR_HANDLING_GUIDE.md](ai_development_docs/AI_ERROR_HANDLING_GUIDE.md) and any changes must consider both docs.

---

## 1. Purpose and Design Principles

The error handling system exists to:

- Provide a **single, consistent pattern** for capturing and logging errors.  
- Distinguish between **expected**, **recoverable**, and **critical** failures.  
- Ensure user-facing errors are **clear and actionable** while logs contain technical detail.  
- Feed **metrics and coverage** tools so we can see which paths are tested and which are not.  
- Support gradual **migration away from ad-hoc try/except** blocks and legacy patterns.

Key principles:

- Prefer the shared **`ErrorHandler`** and **`@handle_errors` decorator** over scattered manual try/except.
- Ensure every non-trivial error path is **logged via the central error handler and component logger**.
- Keep **user messages and log messages separate** (logs are for operators and developers).
- Prefer **MHM-specific exception types** over bare `Exception` so failures are easier to categorize.

---

## 2. Architecture Overview

### 2.1. Core types and hierarchy

The core implementation lives in `core/error_handling.py`.

Central exception hierarchy:

- `MHMError` (base for all MHM-specific errors).  
- `DataError` and `FileOperationError` for data and file-related failures.  
- `ConfigurationError` for invalid or missing configuration.  
- `CommunicationError` for external services (network, Discord, email, AI endpoints).  
- `SchedulerError` for scheduling-related issues.  
- `UserInterfaceError` for UI problems.  
- `AIError` for model calls and AI integration.  
- `ValidationError` for user or data validation problems.  
- `RecoveryError` when a recovery strategy itself fails.

Where practical, modules should raise one of these types instead of bare `Exception`. Some modules (for example `service_utilities.py`) still expose local exceptions such as `InvalidTimeFormatError`; these are acceptable where strongly tied to a single domain, but new shared exceptions should prefer the `MHMError` tree.

**Exception Categorization Decision Tree:**
- **User input validation issues** -> `ValidationError`
  - Invalid format, missing required fields, type mismatches in user-provided data
  - Example: Invalid time format, invalid categories, duplicate period names
  
- **Data processing/validation issues** -> `DataError` or `FileOperationError`
  - Data integrity problems, file operations, data structure issues
  - Example: Corrupted data, invalid data format in processing
  
- **Configuration problems** -> `ConfigurationError`
  - Missing or invalid configuration values, config file issues
  - Example: Missing API key, invalid config setting
  
- **Network/communication issues** -> `CommunicationError`
  - Discord, email, or other communication channel failures
  - Example: Connection timeout, API rate limiting
  
- **AI-related failures** -> `AIError`
  - LM Studio API errors, prompt processing failures, AI model issues
  - Example: Model unavailable, prompt generation failed
  
- **Scheduling issues** -> `SchedulerError`
  - Task scheduling, period management failures
  - Example: Schedule conflict, invalid schedule data

### 2.2. Recovery strategies

The `ErrorHandler` maintains a list of `ErrorRecoveryStrategy` instances to automatically recover from common problems:

- `FileNotFoundRecovery` - creates missing files with default data when safe.  
- `JSONDecodeRecovery` - backs up corrupted JSON to a timestamped `.corrupted_YYYYMMDD_HHMMSS` file and rewrites a default version.
- `NetworkRecovery` - handles transient connectivity problems.  
- `ConfigurationRecovery` - attempts to fall back to safe defaults when configuration is broken.

These strategies are applied inside `ErrorHandler.handle_error` before control is returned to the caller, and they should be kept **idempotent and side-effect safe** (for example, do not silently drop data).

### 2.3. Error handler and helpers

`ErrorHandler` is the central orchestrator:

- Constructor sets up default recovery strategies, maintains `error_count`, and defines `max_retries` for repeated failures.
- `handle_error(error, context, operation, user_friendly=True) -> bool`:
  - Logs the error with structured context.  
  - Tracks how often a particular `(error_type, operation)` has failed.  
  - Tries recovery strategies in order.  
  - Returns `True` if recovery succeeded and the operation can be safely retried, `False` otherwise.

Helper functions in `core/error_handling.py` normalize usage for common domains (file, communication, configuration, network, validation, AI) and delegate into `error_handler.handle_error` with standardized context payloads.

### 2.4. Decorators and utilities

The primary entry point is the `handle_errors` decorator:

```python
def handle_errors(
    operation: str = None,
    context: Dict[str, Any] = None,
    user_friendly: bool = True,
    default_return=None,
)
```

Key behavior:

- Wraps sync and async functions.
- On exception:
  - Builds a context dict (merging decorator-level and call-time data where applicable).  
  - Invokes `error_handler.handle_error(...)`.  
  - If recovery succeeds, retries the operation once (up to `max_retries`).  
  - If recovery fails, logs final details and returns `default_return`.

Use this decorator instead of manual try/except at **module entry points** (scheduler jobs, user-data operations, service utilities, logger helpers). See section 3 for usage patterns.

### 2.5. Integration with logging

Error handling integrates tightly with `core/logger.py`:

- The logger module imports `handle_errors` and decorates internal helpers such as `_is_testing_environment` to ensure logging initialization cannot crash the process.
- All logging for errors uses `get_component_logger(...)` rather than direct `logging.getLogger(...)`.
- Error logs typically flow into `logs/errors.log` and the appropriate component log (for example `logs/scheduler.log`), as described in:
  - Section 2. "Logging Architecture" and  
  - Section 4. "Component Log Files and Layout"  
  in `logs/LOGGING_GUIDE.md`.

File-related recovery behavior (such as backing up corrupted JSON and recreating files with default data) is logged via the `main` component logger so operators can see when auto-recovery occurs.

---

## 3. Usage Patterns

### 3.1. Decorated functions (preferred)

Use `@handle_errors` on **entry points** where an unhandled exception should never crash the whole service:

- Scheduler jobs and background loops in `scheduler.py`.
- Shared scheduling utilities (for example `get_active_schedules` in `schedule_utilities.py`).
- User data load/save operations and channel-preference changes in `user_data_handlers.py`.
- Service and network utilities in `service_utilities.py` (for example throttler checks, service status, network wait loops).
- Logging utilities in `logger.py` that are needed early during startup.

General pattern:

- Choose a short, stable `operation` string (for example `"getting active schedules"`, `"saving user data"`, `"checking if service is running"`).
- Use `default_return` so callers have a safe fallback (`[]`, `False`, or `None`) if recovery fails.  
- Avoid business logic in the decorator arguments; keep them descriptive, not dynamic.

### 3.2. Direct handler and helper calls

Direct calls to `error_handler.handle_error(...)` or domain-specific helpers (for example `handle_file_error`) are appropriate when:

- You are inside a narrow helper where decorating the whole call stack is not practical.  
- You have already caught an exception but need to **record it consistently** and optionally attempt recovery.
- You are bridging external libraries and normalizing their exceptions into the shared system.

Example patterns in the codebase include:

- `file_operations.py` raising `FileOperationError` and then using `handle_file_error` when a low-level file operation fails.
- Higher-level wrappers around AI or network calls that package user IDs and operation names into the context before delegating to `ErrorHandler`.

Keep direct handler usage centralized in a small number of helpers rather than scattered throughout business logic.

### 3.3. Module-specific guidance

- **User data handlers**: Wrap public read/write operations with `@handle_errors` and include enough context (user ID, data types) for troubleshooting. Prefer `FileOperationError` or `DataError` when propagating failures.
- **File operations**: Use `FileOperationError` for file system issues and rely on the recovery strategies to handle missing or corrupted files where safe.
- **Service utilities**: Keep service management and time parsing robust by wrapping operations that touch the OS, processes, or the network with `@handle_errors`. Local exceptions like `InvalidTimeFormatError` should be reserved for explicit validation failures and not used as general error signals.

---

## 4. Error Categories and Severity

Internally, the error handler distinguishes between different categories (even if not all are formalized as enums yet). When designing or refactoring error paths, think in terms of:

- **User input / validation errors**  
  - Example: invalid schedule time, missing required fields.  
  - Expected, should be handled gracefully with user-facing messages.  
  - Typically logged at `INFO` or `WARNING` with structured context.  

- **Recoverable operational errors**  
  - Example: transient network issues, temporary file lock, email send failure.  
  - Logged at `WARNING` or `ERROR` depending on impact.  
  - Often retried or reported to user with suggestions.  

- **Internal bugs / invariants broken**  
  - Example: unexpected state, impossible condition reached, coding mistakes.  
  - Logged at `ERROR` or `CRITICAL`.  
  - Should generally be fixed rather than silently handled.  

- **External dependency failures**  
  - Example: Discord API outage, email provider issues, AI model endpoint down.  
  - Logged with explicit external service identifiers and any available correlation IDs.  

- **Configuration and environment errors**  
  - Example: missing tokens, invalid `.env` values, file system permissions.  
  - Often detected at startup; may be fatal if core functionality cannot run.

Use these categories to choose log levels and to shape messages for later troubleshooting.

---

## 5. Error Message Guidelines

Separate user-facing messages from log messages.

### 5.1. User-facing messages

- Short, clear, and non-technical.  
- Focus on what the user can do (if anything).  
- Avoid stack traces, internal names, or raw exception text.  
- Avoid leaking file paths, tokens, or sensitive IDs.

Example user message:

```text
"Could not send your email right now. Please check your internet connection and try again."
```

When user-visible recovery occurs (for example, recreating a corrupted config file), consider whether to surface a gentle notice to the user so they understand any loss of custom settings.

### 5.2. Log messages

- Include enough context for developers to understand what failed and why.  
- Reference component and operation in the context payload passed to `ErrorHandler`.  
- Capture exception details and stack trace (for example `exc_info=True` in the logger).  
- Avoid secrets (tokens, passwords, full message content unless necessary and safe).

The error handler should be the primary place that final log messages and structures are composed.

---

## 6. Configuration and Integration

Error handling integrates with:

- **Logging configuration**  
  - See section 2. "Logging Architecture" and section 4. "Component Log Files and Layout" in [LOGGING_GUIDE.md](logs/LOGGING_GUIDE.md) for how errors flow into `logs/errors.log` and component logs.

- **Environment flags**  
  - Test mode (`MHM_TESTING`) can change how aggressively errors are surfaced during tests versus production, and is evaluated inside logging utilities wrapped with `@handle_errors`.

If additional error-related environment variables are introduced (for example toggling specific recovery behaviors or error-coverage settings), they should be documented in:

- `core/config.py` (inline comments), and  
- This section, with a clear description of their intended impact.

---

## 7. Testing Error Handling

Error handling is tested in multiple ways:

- **Unit/integration tests**  
  - For example: `tests/test_error_handling_improvements.py`.  
  - Verify decorator behavior, logging, and recovery results.  

- **Coverage tooling**  
  - `development_tools/error_handling/analyze_error_handling.py` analyzes which error paths have test coverage.  
  - Can be integrated into automated workflows via `development_tools/run_development_tools.py` commands to generate reports.
  - **Phase 1 and Phase 2 Analysis**: The tool now includes specialized auditing for quality improvements:
    - **Phase 1**: Identifies functions with basic try-except blocks that should use `@handle_errors` decorator, prioritized by entry points and operation types
    - **Phase 2**: Audits generic exception raises (ValueError, Exception, KeyError, TypeError) that should be replaced with specific `MHMError` subclasses
    - Results are integrated into [AI_STATUS.md](development_tools/AI_STATUS.md), [AI_PRIORITIES.md](development_tools/AI_PRIORITIES.md), and `development_tools/consolidated_report.txt` for tracking progress on the Error Handling Quality Improvement Plan

Guidelines when adding or changing error handling:

- Add or update tests for both the success path and the failure path.  
- Verify that exceptions are correctly captured by decorators or direct handler calls.
- Where practical, assert on logs or metrics using helpers in `tests/test_utilities.py`.  

For broader testing patterns, see:

- Section 1. "Testing Philosophy and Priorities" and  
- Section 3. "Test Types and Structure"  

in [TESTING_GUIDE.md](tests/TESTING_GUIDE.md).

---

## 8. Monitoring and Debugging

The error handling system is designed to support:

- Identification of frequent error sources (components, operations, exception types).  
- Differentiation between expected and unexpected failures.  
- Future integration with dashboards or reports built on:
  - `logs/errors.log` and  
  - Error-coverage and metrics outputs.  

When debugging:

- Start from `logs/errors.log` and the relevant component log.  
- Look for:
  - Repeated failures of the same operation.  
  - Unhandled exceptions that escaped decorators.  
  - Legacy paths still using ad-hoc try/except or `print`.

If an error is noisy without being actionable, consider:

- Adjusting log levels (without hiding important problems).  
- Introducing a more specific exception type or message in `error_handling.py`.  
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
- Consolidate repeated error handling logic into the shared error handler and helper functions.

Legacy compatibility should follow the logging patterns described in section 5. "Error Message Guidelines" and section 8. "Monitoring and Debugging" in [LOGGING_GUIDE.md](logs/LOGGING_GUIDE.md) when retaining old entry points or behaviors.

---

## 10. Examples

This section illustrates typical patterns. When in doubt, mirror these and adjust component/operation names only.

### 10.1. Decorated background task

A scheduler job that must never crash the whole service:

```python
from core.error_handling import handle_errors
from core.logger import get_component_logger

logger = get_component_logger("scheduler")

@handle_errors(operation="running scheduler cycle", default_return=None)
def run_cycle():
    logger.info("Starting scheduler cycle")
    # ... work ...
```

### 10.2. Explicit error handling in a low-level helper

A helper that reads a file and reports failures via the centralized handler:

```python
from core import error_handling

def read_user_file(path, user_id):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError as exc:
        error_handling.error_handler.handle_error(
            exc,
            context={"component": "file_ops", "operation": "read_user_file", "user_id": user_id, "path": path},
            operation="read_user_file",
        )
        return None
```

These examples are intentionally simple; real code should use the shared helpers (for example `handle_file_error`) where available.

---

## 11. Cross-References

For related topics:

- Logging implementation guidance  
  - See section 2. "Logging Architecture" and section 4. "Component Log Files and Layout" in [LOGGING_GUIDE.md](logs/LOGGING_GUIDE.md).

- Testing patterns and expectations  
  - See section 1. "Testing Philosophy and Priorities" and section 3. "Test Types and Structure" in [TESTING_GUIDE.md](tests/TESTING_GUIDE.md).

- Development workflow and emergency procedures  
  - See section 6. "Emergency Procedures" in [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md).

- AI system behavior and LM Studio fallbacks  
  - See [SYSTEM_AI_GUIDE.md](ai/SYSTEM_AI_GUIDE.md).
