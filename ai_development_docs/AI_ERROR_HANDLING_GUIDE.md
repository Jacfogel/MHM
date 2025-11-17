# AI Error Handling Guide

> **File**: `ai_development_docs/AI_ERROR_HANDLING_GUIDE.md`  
> **Purpose**: Fast patterns and troubleshooting guidance for error handling  
> **Style**: Concise, pattern-focused, actionable  

For more detailed guidance, examples, and rationale for any topic in this file, use the matching sections in `core/ERROR_HANDLING_GUIDE.md`.


## Quick Reference

Minimal rules for AI suggestions:

- Use `@handle_errors` for most entry-point functions: UI handlers, scheduler entry points, communication and AI integration.  
- Raise structured exceptions that inherit from `MHMError` instead of raw `Exception`.  
- Wrap low-level library/OS exceptions into domain-specific errors (`DataError`, `FileOperationError`, `ConfigurationError`, etc.).  
- Use `default_return` only when there is a clearly safe fallback.  
- Log once at the appropriate layer; avoid duplicate logging of the same failure.  
- For logging details, route to `AI_LOGGING_GUIDE.md` and `logs/LOGGING_GUIDE.md`.


## Error Handling Architecture


Internally, a global `ErrorHandler` instance in `core/error_handling.py` applies recovery strategies (for example `FileNotFoundRecovery`, `JSONDecodeRecovery`, `NetworkRecovery`, `ConfigurationRecovery`), logs structured entries to component loggers and the `errors` logger, and enforces a simple retry limit. Most new code should still use `@handle_errors` and the convenience helpers rather than calling `error_handler.handle_error(...)` directly.


AI view of the architecture:

- Centralized decorator: `handle_errors(operation, default_return=None, context=None)` is the main entry-point pattern.  
- Base exception: `MHMError`, with a hierarchy for data, configuration, communication, scheduler, UI, AI, validation, and recovery errors.  
- Boundary functions (UI, scheduler, communication, AI entry points) are typically decorated; deeper helpers raise domain-specific errors.  
- Logging and error handling are coordinated:
  - `@handle_errors` logs the error with context and either returns a fallback or re-raises.  
  - Component loggers are used according to `AI_LOGGING_GUIDE.md`.


## Exception Hierarchy

Use and extend this hierarchy rather than inventing new ad-hoc types:

```python
from core.error_handling import (
    MHMError,
    DataError,
    FileOperationError,
    ConfigurationError,
    CommunicationError,
    SchedulerError,
    UserInterfaceError,
    AIError,
    ValidationError,
    RecoveryError,
)
```

Guidance:

- Map data/JSON/user data problems → `DataError` or `FileOperationError`.  
- Map misconfiguration → `ConfigurationError`.  
- Map channel/Discord/email problems → `CommunicationError`.  
- Map scheduler/wake-timer failures → `SchedulerError`.  
- Map UI failures → `UserInterfaceError`.  
- Map AI provider issues → `AIError`.  
- Map invalid input/config → `ValidationError`.  
- Map failures in retry/fallback logic → `RecoveryError`.  


## Core Patterns

### Decorator usage

Basic pattern:

```python
from core.error_handling import handle_errors, DataError

@handle_errors("loading user data", default_return={})
def load_user_data(user_id: str) -> dict:
    try:
        return _load_user_data_from_disk(user_id)
    except OSError as e:
        raise DataError(f"Failed to load user data for {user_id}") from e
```

AI rules:

- Use `@handle_errors` at boundaries (UI handlers, scheduler entry points, service entry points).  
- Avoid using the decorator deep in low-level helpers; those should raise specific exceptions.  
- Do not catch exceptions just to log and re-raise without adding context; let `@handle_errors` do that at the boundary.

### Validation first

- Suggest validating configuration and input early and raising `ValidationError` or `ConfigurationError`.  
- Avoid guessing defaults that mask real misconfiguration or invalid data.


## Data and File Operations

Minimal patterns:

- Wrap file IO/JSON parsing issues in `FileOperationError` or `DataError`.  
- Keep file and user-data helpers small and focused, with clear error messages.  
- Avoid silent failures when reading or writing user data; log and raise.

Example template:

```python
from core.error_handling import FileOperationError

def load_json_file(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise FileOperationError(f"Failed to load JSON file: {path}") from e
```


## Configuration and External Services

AI suggestions should:

- Use `ConfigurationError` for missing/invalid env vars or config values.  
- Use `CommunicationError` for Discord/email/network issues.  
- Use `AIError` for AI provider failures (timeouts, invalid responses, connection errors).  
- Use `SchedulerError` for scheduler and wake-timer issues.

Keep patterns simple and explicit; avoid mixing multiple concerns in a single exception message.  


## Recovery Strategies

AI view of recovery:

- Use `default_return` in `@handle_errors` when:
  - There is a safe, defined fallback, and  
  - The caller can behave correctly with that fallback.  
- Consider limited retries for transient external failures; avoid unbounded retries.  
- For deeper failures in recovery logic, raise `RecoveryError` with clear context.

Graceful degradation patterns:

- AI failures → fall back to predefined messages or static content.  
- Corrupted user data → log and fall back to defaults for that user, preserving logs for analysis.  
- Scheduler failures → log, avoid half-applied schedules, and require explicit user intervention where needed.  


## Logging and Context

AI rules for logging:

- Use component loggers (see `AI_LOGGING_GUIDE.md`) and avoid creating new ad-hoc log files.  
- Ensure error logs include:
  - Operation name.  
  - Exception type and message.  
  - Relevant context (user id, schedule id, channel id).  
- Never log secrets, tokens, or sensitive personal data.

Legacy compatibility:

- For temporary legacy paths, use `LEGACY COMPATIBILITY` comments and a WARNING-level log entry with a clear TODO and removal plan (see `AI_LEGACY_REMOVAL_GUIDE.md`).  


## Testing and Troubleshooting

AI guidance for tests:

- Add tests that assert:
  - The right exception type is raised (`DataError`, `FileOperationError`, etc.).  
  - `@handle_errors` returns the correct `default_return` when configured.  
  - Recovery paths behave as expected (for example, fallback to defaults).  
- Use patterns and markers from:
  - `AI_TESTING_GUIDE.md` → `tests/TESTING_GUIDE.md`.

When troubleshooting:

1. Suggest checking `logs/errors.log` for stack traces and error context.  
2. Suggest checking relevant component logs (`discord.log`, `scheduler.log`, `ui.log`, etc.).  
3. Identify which exception type was raised and whether it is appropriate.  
4. Recommend fixes that:
   - Improve validation,  
   - Tighten mappings from low-level to domain-specific errors, or  
   - Refine recovery behavior.




For broader coverage and metrics:
- Suggest running the AI development tools (see `ai_development_tools/README.md`) to inspect error handling coverage and quality signals derived from the `errors` log and code patterns.

## Resources

For related topics:

- Detailed patterns and rationale: `core/ERROR_HANDLING_GUIDE.md`.  
- Logging structure and triage: `AI_LOGGING_GUIDE.md` and `logs/LOGGING_GUIDE.md`.  
- Development workflow and safe changes: `AI_DEVELOPMENT_WORKFLOW.md`.  
- Testing patterns and error-path coverage: `AI_TESTING_GUIDE.md`.  
- Legacy removal strategy and markers: `AI_LEGACY_REMOVAL_GUIDE.md`.
