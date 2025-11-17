# Exception Handling Guide - MHM System

> **File**: `core/ERROR_HANDLING_GUIDE.md`  
> **Audience**: Developers, AI collaborators, and maintainers  
> **Purpose**: Describe the centralized error handling architecture, patterns, and best practices for the MHM system  
> **Style**: Technical, comprehensive, actionable  
> **Status**: ACTIVE – follow these patterns for all new code


## Quick Reference

Use this section when you need a fast reminder of how errors should be handled.

Core rules:

- Use the centralized decorator `@handle_errors` for most public functions and UI/event handlers.  
- Raise structured custom exceptions derived from `MHMError` (not ad-hoc `Exception`).  
- Do not silently swallow exceptions; either handle them meaningfully or let them be managed by a higher-level handler.  
- Use safe defaults via `default_return` in `@handle_errors` only when there is a clear, documented fallback.  
- Log errors once at the appropriate layer; avoid duplicate logs for the same failure.  
- Map low-level library or OS exceptions into meaningful domain errors (`DataError`, `FileOperationError`, `ConfigurationError`, `CommunicationError`, `SchedulerError`, `UserInterfaceError`, `AIError`, `ValidationError`, `RecoveryError`).

Minimal example:

```python
from core.error_handling import handle_errors, DataError

@handle_errors("loading user data", default_return={})
def load_user_data(user_id: str) -> dict:
    try:
        return _load_user_data_from_disk(user_id)
    except OSError as e:
        # Wrap low-level exception
        raise DataError(f"Failed to load user data for {user_id}") from e
```


## Error Handling Architecture

The MHM error handling system is built around:

- A centralized decorator: `handle_errors(operation: str, default_return: Any = None, context: dict | None = None)`  
- A base exception: `MHMError`  
- A structured hierarchy of domain-specific exceptions (see the next section).  
- Standardized logging and recovery behavior:
  - The decorator logs exceptions with context.  
  - It can return a safe fallback value (`default_return`) or re-raise.  
- Integration points:
  - Service and background tasks (core modules).  
  - Communication channels (Discord, email, future channels).  
  - UI event handlers and dialogs.  
  - AI integration flows.

Typical call chain:

1. Low-level function (file IO, network) raises a library/OS exception.  
2. Mid-level function wraps that exception into a domain-specific `MHMError` subclass.  
3. Top-level function or UI handler is decorated with `@handle_errors`, which:
   - Logs the error with context,  
   - Applies a recovery strategy (fallback, user message, or shutdown),  
   - Returns a default value if configured, or re-raises when required.


## Exception Hierarchy

All custom exceptions derive from `MHMError`. A simplified tree:

```text
MHMError (Base Exception)
├── DataError
│   └── FileOperationError
├── ConfigurationError
├── CommunicationError
├── SchedulerError
├── UserInterfaceError
├── AIError
├── ValidationError
└── RecoveryError
```

Usage guidance:

- `MHMError`: base for all system-specific errors. Do not raise raw `Exception` when a more specific type is available.  
- `DataError`: data integrity, missing/invalid user data, JSON issues, etc.  
- `FileOperationError`: failures reading/writing files, permissions, path issues.  
- `ConfigurationError`: invalid or missing configuration (env vars, config files).  
- `CommunicationError`: errors when interacting with Discord, email, or other channels.  
- `SchedulerError`: failures in scheduling, timers, or wake timers.  
- `UserInterfaceError`: UI operations that fail (dialogs, widget actions).  
- `AIError`: AI provider failures, timeouts, or invalid responses.  
- `ValidationError`: invalid user or config input detected during validation.  
- `RecoveryError`: failure of a recovery operation that was intended to fix or compensate for another error.

When introducing a new error type:

- Inherit from `MHMError`.  
- Keep the name and docstring clear and specific.  
- Update this guide and `ai_development_docs/AI_ERROR_HANDLING_GUIDE.md` with usage notes.


## Core Patterns
### Central ErrorHandler and recovery strategies (implementation detail)

The decorator-based pattern is built on a global `ErrorHandler` instance defined in `core/error_handling.py`:

- `ErrorHandler` maintains:
  - A list of `ErrorRecoveryStrategy` implementations (for example `FileNotFoundRecovery`, `JSONDecodeRecovery`, `NetworkRecovery`, `ConfigurationRecovery`).
  - An `error_count` map and `max_retries` guard to avoid infinite retry loops.
  - Centralized logging into both the main component logger and `errors` logger with structured fields (operation, error type, error message, file path, user id).
- `handle_errors(...)` delegates to this global `error_handler` and, on successful recovery, retries the operation once before returning `default_return`.

Recommended usage:

- For new or refactored code, prefer:
  - Decorating boundary functions with `@handle_errors`, and
  - Using the convenience helpers (`safe_file_operation`, `handle_file_error`, `handle_communication_error`, etc.) rather than calling `error_handler.handle_error(...)` directly.
- Direct calls to `error_handler.handle_error(...)` should be treated as an internal mechanism for error-handling infrastructure and existing legacy paths, not a primary pattern for new features.
- When extending recovery behaviour, add or refine `ErrorRecoveryStrategy` classes carefully and document changes in this guide and `ai_development_docs/AI_ERROR_HANDLING_GUIDE.md`.


### Decorator usage: `@handle_errors`

Use `@handle_errors` for most entry-point functions, especially those that:

- Are called from UI event handlers.  
- Trigger scheduled tasks or background jobs.  
- Interact with external services (Discord, email, AI).  
- Manipulate user data or configuration.

Example:

```python
from core.error_handling import handle_errors, SchedulerError

@handle_errors("initializing scheduler", default_return=False)
def init_scheduler() -> bool:
    try:
        scheduler.setup()
        return True
    except Exception as e:
        raise SchedulerError("Failed to initialize scheduler") from e
```

Key parameters:

- `operation` – short description of what this function is doing.  
- `default_return` – safe fallback result when recovery is possible.  
- `context` – dict of additional context (user id, schedule id, message id, etc.) useful for logging.

### Where to catch vs where to raise

- Catch exceptions at boundaries:
  - UI event handlers.  
  - API or channel entry points.  
  - Scheduler entry points.  
- Raise structured exceptions in lower-level functions:
  - Wrap library/OS exceptions in domain-specific `MHMError` subclasses.  
- Avoid catching exceptions just to log and re-raise without adding context; either:
  - Add meaningful context then re-raise, or  
  - Let `@handle_errors` perform the logging at the boundary.

### Validation first

Before performing side effects:

- Validate inputs and configuration; raise `ValidationError` or `ConfigurationError` early.  
- Use clear messages so logs and UIs can surface actionable information.


## Data and File Operations

Data and file handling is a common source of errors; use consistent patterns.

### Safe file operations

- Use helper functions that encapsulate reading/writing JSON or other formats.  
- Wrap low-level exceptions (`OSError`, `JSONDecodeError`, etc.) in `FileOperationError` or `DataError`.  
- Always validate that paths point to expected directories and files.

Example:

```python
from core.error_handling import FileOperationError

def load_json_file(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise FileOperationError(f"Failed to load JSON file: {path}") from e
```

### User data handling

- Errors reading or writing user-specific data should be raised as `DataError` or `FileOperationError`.  
- When falling back to default user data, document the behavior and ensure it is safe (for example, does not silently discard important settings).  
- Avoid partial writes; use atomic writes or temporary files where applicable.


## Configuration and External Services

Configuration and external dependencies are frequent failure points.

### Configuration errors

- When environment variables or config entries are missing or invalid, raise `ConfigurationError`.  
- Do not guess defaults that can hide misconfiguration; require explicit configuration for critical values.  
- Validate configuration early on app startup and fail fast with clear messages.

### Communication and external services

- Map errors from Discord, email, and other services into `CommunicationError`.  
- For AI provider issues (timeouts, invalid responses, connection failures), use `AIError`.  
- For scheduler or timer operations (including OS-level wake timers), use `SchedulerError`.

Example:

```python
from core.error_handling import CommunicationError

def send_discord_message(channel, content: str) -> None:
    try:
        channel.send(content)
    except Exception as e:
        raise CommunicationError("Failed to send Discord message") from e
```


## Recovery Strategies

Recovery is about safely continuing when something goes wrong.

### Default returns and fallbacks

Use `default_return` in `@handle_errors` when:

- There is a safe, well-understood fallback.  
- The caller can behave correctly with that default.  
- The fallback and its implications are documented in code comments and, where relevant, in human-facing docs.

### Retries

- Consider retries for transient failures (network, external services).  
- Keep retry counts low; avoid endless loops.  
- If a retry fails, escalate to a structured error (`RecoveryError` or a more specific type) and log clearly.

### Graceful degradation

Examples:

- If AI responses are unavailable, fall back to pre-defined messages (raising/logging `AIError` but continuing).  
- If a single user’s data is corrupted, log a `DataError` and fall back to defaults for that user while preserving logs for investigation.  
- If scheduling fails, log a `SchedulerError` and avoid partial or incorrect scheduling state.

### When to fail fast

- When configuration is invalid or missing for critical functionality.  
- When continuing may corrupt user data or cause repeated spam/abuse (for example, repeated messages to the same channel).  
- When invariants about user data or schedules are violated.


## Logging and Context

Error handling and logging must work together.

### Logging strategy

- Errors should be logged with:
  - The operation name.  
  - The exception type and message.  
  - Relevant context (user id, schedule id, channel, etc.).  
- Prefer structured logging where possible (dict-like context payloads).  
- Avoid logging secrets, tokens, or sensitive PII.

### Which logs to use

- See `logs/LOGGING_GUIDE.md` and `ai_development_docs/AI_LOGGING_GUIDE.md` for details.  
- As a rule:
  - Component logs (for example, `discord.log`, `scheduler.log`, `ui.log`) capture subsystem activity.  
  - `errors.log` collects consolidated error information.  
  - `app.log` provides high-level flow.

### Error metrics and audit integration

The structured entries written by `ErrorHandler` to the `errors` logger are used by the AI development tools to analyse error handling quality and coverage.

- Each logged error includes operation, error type, message, file path (if applicable), and user id (when available).
- AI audit tools (see `ai_development_tools/README.md`) aggregate these logs to:
  - Track error counts by type and operation.
  - Identify hot spots where recovery fails or is missing.
  - Feed into coverage and quality reports such as error handling coverage analysis.
- When changing error logging structure, ensure that `errors` log entries still include these fields so metrics remain meaningful.

### Legacy compatibility markers

When introducing temporary compatibility paths:

```python
# LEGACY COMPATIBILITY: [Brief description]
# TODO: Remove after [specific condition]
# REMOVAL PLAN:
# 1. [Step 1]
# 2. [Step 2]
# 3. [Step 3]
logger.warning("LEGACY COMPATIBILITY: <what was called>; use <new path> instead")
```

Guidelines:

- Only add legacy paths when necessary to prevent breakage.  
- Always log usage at WARNING level to track and plan removal.  
- Add a clear removal condition and steps.  
- Coordinate with `ai_development_docs/AI_LEGACY_REMOVAL_GUIDE.md` when planning removal.  


## Testing and Troubleshooting

### Testing error handling

- Add tests that verify:
  - Specific exceptions are raised for specific failures.  
  - `@handle_errors` returns the expected `default_return` when configured.  
  - Logs are written for key error scenarios (where practical).  
  - Recovery paths behave as expected (retries, fallbacks, degradation).

- Use pytest patterns and markers described in:
  - `ai_development_docs/AI_TESTING_GUIDE.md`  
  - `tests/TESTING_GUIDE.md`

Examples:

- Unit tests that simulate file IO failures and assert `FileOperationError`.  
- Integration tests that simulate communication failures and assert `CommunicationError` or recovery behavior.  
- Tests for scheduler failures that assert `SchedulerError` and safe shutdown or fallback.

### Troubleshooting production issues

When something goes wrong:

1. Check `logs/errors.log` for stack traces and structured error entries.  
2. Check the relevant component log (for example, `discord.log`, `scheduler.log`, `ui.log`).  
3. Identify the exception type and operation.  
4. See where the exception originates and whether it is being handled correctly.  
5. If a recovery path is failing, consider introducing or refining `RecoveryError` handling.  


### Error handling coverage and metrics

In addition to individual tests, the AI development tools provide automated error handling coverage analysis:

- See `ai_development_tools/README.md` for how to run `ai_tools_runner.py` commands (for example `audit` in fast or full mode).
- The error handling coverage tooling scans functions for patterns such as:
  - Presence of `@handle_errors` on boundary functions.
  - Use of domain-specific `MHMError` subclasses.
  - Missing or incomplete error handling in critical operations.
- Use these reports to prioritise improvements to exception mapping, recovery paths, and logging context.

## Resources

For related topics and further detail:

- `ai_development_docs/AI_ERROR_HANDLING_GUIDE.md` – condensed patterns and AI-optimized view.  
- `logs/LOGGING_GUIDE.md` and `ai_development_docs/AI_LOGGING_GUIDE.md` – logging structure, component loggers, and triage.  
- `DEVELOPMENT_WORKFLOW.md` and `ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md` – safe development and deployment patterns.  
- `tests/TESTING_GUIDE.md` and `ai_development_docs/AI_TESTING_GUIDE.md` – testing patterns, including error-path testing.  
- `ai_development_docs/AI_LEGACY_REMOVAL_GUIDE.md` – broader strategy for managing legacy code and planned removal.
