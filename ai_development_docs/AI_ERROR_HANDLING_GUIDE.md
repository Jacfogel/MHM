# AI Error Handling Guide

> **File**: `ai_development_docs/AI_ERROR_HANDLING_GUIDE.md`  
> **Pair**: `core/ERROR_HANDLING_GUIDE.md`  
> **Audience**: AI collaborators and tools  
> **Purpose**: Routing & constraints for error handling  
> **Style**: Minimal, routing-first  

> For detailed behavior, examples, and rationale, use matching sections in `core/ERROR_HANDLING_GUIDE.md`.  
> Keep this file’s H2 headings in lockstep with `core/ERROR_HANDLING_GUIDE.md` when making changes.

---

## 1. Purpose and Design Principles

Use the centralized error handling system instead of ad-hoc patterns:

- Default to the shared `ErrorHandler` and `@handle_errors` decorator.  
- Ensure every non-trivial failure path is **logged** and, where possible, **categorized** using the `MHMError` hierarchy.
- Keep **user-facing messages** short and safe; keep **logs** detailed.

When changing error handling, keep behavior consistent with section 1. "Purpose and Design Principles" in `core/ERROR_HANDLING_GUIDE.md`.

---

## 2. Architecture Overview

Key components (see section 2. "Architecture Overview" in `core/ERROR_HANDLING_GUIDE.md`):

- **Exception hierarchy**: `MHMError` and its subclasses (`DataError`, `FileOperationError`, `ConfigurationError`, `CommunicationError`, `SchedulerError`, `UserInterfaceError`, `AIError`, `ValidationError`, `RecoveryError`).  
- **Recovery strategies**: `FileNotFoundRecovery`, `JSONDecodeRecovery`, `NetworkRecovery`, `ConfigurationRecovery`.  
- **`ErrorHandler`**: central object with `handle_error(error, context, operation, user_friendly=True) -> bool`.  
- **Decorator**: `handle_errors(operation=None, context=None, user_friendly=True, default_return=None)` for wrapping entry points.  

Constraints:

- Prefer raising specific `MHMError` subclasses instead of `Exception`.  
- Keep recovery strategies idempotent and side-effect safe.  
- Do not add new global error handlers or decorators; extend `core/error_handling.py` instead.

**Exception Categorization Rules for AI:**
- Replace `ValueError` with `ValidationError` for user input validation, or `DataError` for data processing
- Replace `KeyError` with `ConfigurationError` for config access, or `DataError` for data structure access
- Replace `TypeError` with `ValidationError` for user input type issues, or `DataError` for internal type issues
- Replace generic `Exception` with specific subclass based on context (file operations → `FileOperationError`, network → `CommunicationError`, etc.)

---

## 3. Usage Patterns

When editing or generating code, apply these patterns (see section 3. "Usage Patterns" in `core/ERROR_HANDLING_GUIDE.md`):

- Wrap entry points with `@handle_errors`:
  - Scheduler jobs and long-running loops.  
  - User data load/save operations.  
  - Service and network utilities.  
  - Logger helpers used during startup.

- Use **stable, descriptive `operation` names** (for example `"getting active schedules"`, `"saving user data"`).  
- Provide `default_return` that is safe for the caller (`[]`, `False`, or `None`).  
- Use direct handler/helper calls only when:
  - You are already in a small helper that caught an exception, or  
  - You need to normalize external library exceptions into the shared system.

Never:

- Swallow exceptions silently.  
- Add raw `print`-based error reporting.  
- Introduce new ad-hoc try/except trees without going through `ErrorHandler`.

---

## 4. Error Categories and Severity

Follow the categories in section 4. "Error Categories and Severity" in `core/ERROR_HANDLING_GUIDE.md`:

- Validation / user input errors.  
- Recoverable operational errors.  
- Internal bugs / invariants broken.  
- External dependency failures.  
- Configuration and environment errors.  

Routing rules for AI:

- Map new exceptions into one of these categories.  
- Choose log levels consistent with those categories.  
- Prefer using or extending existing `MHMError` subclasses rather than inventing new category concepts.

---

## 5. Error Message Guidelines

Use section 5. "Error Message Guidelines" in `core/ERROR_HANDLING_GUIDE.md` as the source of truth.

Key constraints:

- User-facing text:
  - Short, clear, non-technical.  
  - No stack traces, internal names, or secrets.  

- Log messages:
  - Include component, operation, and relevant context (IDs, file paths) but never secrets.  
  - Let `ErrorHandler` assemble final log messages where possible.  

Do not embed stack traces or raw exceptions into user-visible strings.

---

## 6. Configuration and Integration

Error handling must integrate cleanly with logging and configuration (see section 6. "Configuration and Integration" in `core/ERROR_HANDLING_GUIDE.md` and section 2. "Logging Architecture" in `logs/LOGGING_GUIDE.md`).

Routing rules:

- Do not create new environment variables for error behavior without:
  - Updating `core/config.py`, and  
  - Documenting them in section 6 of `core/ERROR_HANDLING_GUIDE.md`.  

- Respect `MHM_TESTING` when deciding whether to surface or suppress errors in tests.  

Logging constraints:

- Use component loggers via `core/logger.py`.  
- Do not use raw `logging.getLogger(...)` for new error logging.  

---

## 7. Testing Error Handling

For test coverage of error handling (see section 7. "Testing Error Handling" in `core/ERROR_HANDLING_GUIDE.md` and sections 1 and 3 of `tests/TESTING_GUIDE.md`).

AI routing:

- When adding or changing error handling, also:
  - Add tests in `tests/test_error_handling_improvements.py` or nearby files.  
  - Ensure both success and failure paths are covered.  
  - Use helpers in `tests/test_utilities.py` to assert on logs/metrics where appropriate.  

- Use `error_handling_coverage.py` and related tooling when measuring coverage or generating reports.  
- **Phase 1 and Phase 2 Auditing**: The coverage tool now provides specialized analysis for quality improvements:
  - **Phase 1**: Identifies functions with basic try-except blocks that should use `@handle_errors` decorator, with priority categorization (high/medium/low)
  - **Phase 2**: Audits generic exception raises that should be replaced with specific `MHMError` subclasses
  - Results appear in audit reports (`AI_STATUS.md`, `AI_PRIORITIES.md`, `consolidated_report.txt`) for tracking progress
  - See `development_docs/PLANS.md` for the Error Handling Quality Improvement Plan details

Do not design new error mechanisms that are hard or impossible to test.

---

## 8. Monitoring and Debugging

For debugging guidance, rely on section 8. "Monitoring and Debugging" in `core/ERROR_HANDLING_GUIDE.md` and section 8. "Monitoring and Debugging" in `logs/LOGGING_GUIDE.md`.

AI rules:

- When investigating failures:
  - Start from `logs/errors.log` plus the relevant component log.  
  - Look for repeated failures of the same operation or unhandled exceptions.  

- Prefer improving:
  - Exception types, messages, and contexts in `error_handling.py`.  
  - Tests that reproduce and prevent regressions.  

Avoid adding one-off debug prints; use structured logging and the existing log files.

---

## 9. Legacy and Migration

Follow section 9. "Legacy and Migration" in `core/ERROR_HANDLING_GUIDE.md`.

Migration rules:

- Replace legacy try/except blocks that directly log or print with:
  - `@handle_errors` on entry points, or  
  - Calls into `ErrorHandler` / helper functions.  

- Keep migration changes small and well-tested.  
- Preserve behavior where users rely on it, but route the implementation through the centralized handler.

---

## 10. Examples

Do **not** add new tutorial-style examples here; use examples only when needed for routing.

If you need concrete patterns:

- Use the minimal examples in section 10. "Examples" in `core/ERROR_HANDLING_GUIDE.md`.
- Prefer reusing those examples verbatim rather than inventing new variations.

---

## 11. Cross-References

For related AI-facing routing docs:

- Logging: `ai_development_docs/AI_LOGGING_GUIDE.md`: section 2 & section 4.  
- Testing: `ai_development_docs/AI_TESTING_GUIDE.md`: section 7 for debugging, section 3 for fixtures/safety.  
- Development workflow: `ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md`.

For detailed explanations, always route back to `core/ERROR_HANDLING_GUIDE.md` instead of repeating content here.
