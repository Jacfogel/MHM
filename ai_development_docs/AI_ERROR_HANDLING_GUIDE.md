# AI Error Handling Guide

> **File**: `ai_development_docs/AI_ERROR_HANDLING_GUIDE.md`  
> **Pair**: [ERROR_HANDLING_GUIDE.md](../core/ERROR_HANDLING_GUIDE.md)  
> **Audience**: AI collaborators and tools  
> **Purpose**: Routing & constraints for error handling  
> **Style**: Minimal, routing-first  

> For detailed behavior, examples, and rationale, use matching sections in ERROR_HANDLING_GUIDE.md.  
> Keep this file's H2 headings in lockstep with ERROR_HANDLING_GUIDE.md when making changes.

---

## 1. Purpose and Design Principles

Use the centralized error handling system instead of ad-hoc patterns:

- Default to the shared `ErrorHandler` and `@handle_errors` decorator.  
- Ensure every non-trivial failure path is **logged** and, where possible, **categorized** using the `MHMError` hierarchy.
- Keep **user-facing messages** short and safe; keep **logs** detailed.

When changing error handling, keep behavior consistent with section 1. "Purpose and Design Principles" in [ERROR_HANDLING_GUIDE.md](../core/ERROR_HANDLING_GUIDE.md#1-purpose-and-design-principles).

---

## 2. Architecture Overview

Key components (see section 2. "Architecture Overview" in [ERROR_HANDLING_GUIDE.md](../core/ERROR_HANDLING_GUIDE.md#2-architecture-overview)):

- **Exception hierarchy**: `MHMError` and its subclasses (`DataError`, `FileOperationError`, `ConfigurationError`, `CommunicationError`, `SchedulerError`, `UserInterfaceError`, `AIError`, `ValidationError`, `RecoveryError`).  
- **Recovery strategies**: `FileNotFoundRecovery`, `JSONDecodeRecovery`, `NetworkRecovery`, `ConfigurationRecovery`.  
- **`ErrorHandler`**: central object with `handle_error(error, context, operation, user_friendly=True) -> bool`.  
- **Decorator**: `handle_errors(operation=None, context=None, user_friendly=True, default_return=None, re_raise=False)` for wrapping entry points. Use `re_raise=True` when there is no safe default (e.g. lazy import helpers); the error is logged/handled then re-raised.  
- **Service startup (`MHMService`)**: Bootstrap raises `CommunicationError` or `SchedulerError` with structured `details` (including `stage`) for subsystem failures. `MHMService.start()` treats `CommunicationError`, `SchedulerError`, `ConfigurationError`, and `core.config.ConfigValidationError` as fatal startup failures (CRITICAL logging before shutdown). Do not expect a `core.InitializationError` export; see section 2.6. "Service startup (`MHMService`)" in [ERROR_HANDLING_GUIDE.md](../core/ERROR_HANDLING_GUIDE.md#26-service-startup-mhmservice).

Constraints:

- Prefer raising specific `MHMError` subclasses instead of `Exception`.  
- Keep recovery strategies idempotent and side-effect safe.  
- Do not add new global error handlers or decorators; extend `core/error_handling.py` instead.

**Exception Categorization Rules for AI:**
- Replace `ValueError` with `ValidationError` for user input validation, or `DataError` for data processing
- Replace `KeyError` with `ConfigurationError` for config access, or `DataError` for data structure access
- Replace `TypeError` with `ValidationError` for user input type issues, or `DataError` for internal type issues
- Replace generic `Exception` with specific subclass based on context (file operations -> `FileOperationError`, network -> `CommunicationError`, etc.)

---

## 3. Usage Patterns

When editing or generating code, apply these patterns (see section 3. "Usage Patterns" in [ERROR_HANDLING_GUIDE.md](../core/ERROR_HANDLING_GUIDE.md#3-usage-patterns)):

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

Follow the categories in section 4. "Error Categories and Severity" in [ERROR_HANDLING_GUIDE.md](../core/ERROR_HANDLING_GUIDE.md#4-error-categories-and-severity):

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

Use section 5. "Error Message Guidelines" in [ERROR_HANDLING_GUIDE.md](../core/ERROR_HANDLING_GUIDE.md#5-error-message-guidelines) as the source of truth.

Key constraints:

- User-facing text:
  - Short, clear, non-technical.  
  - No stack traces, internal names, or secrets.  

- Log messages:
  - Include component, operation, and relevant context (IDs, file paths) but never secrets.  
  - Let `ErrorHandler` assemble final log messages where possible.  

Do not embed stack traces or raw exceptions into user-visible strings.

Task mutation failures should describe an unconfirmed outcome and direct users to check `list tasks` / task details before retrying. Preserve note/URL recovery guidance, return an `InteractionResponse` at command exception boundaries, and log operation/user/task context without content. A missing reminder read-back must not be dereferenced or reported as a confirmed save; see the paired guide, section 5.1.

Notebook commands also return safe recovery replies for unconfirmed saves. Preserve structured missing/ambiguous-reference guidance rather than claiming every mutation failure is a missing entry. Use notebook check commands and text-copy guidance; log operation/user context without entry references or content. Pin/archive wrappers own their helper's exception reporting; see the paired guide, section 5.1.

Notebook creation preflights normalized titles with the existing validator and returns an invalid-title result before persistence. Surface the canonical title limit and body-text guidance without raw validation errors.

Schedule add/edit must check persistence results, avoid raw exceptions in replies, and copy loaded dictionaries before editing. Explicit inactive flags are changes. Unavailable check-in read commands retain the flow and give recovery guidance; empty/malformed messages responses must not produce blank replies or object representations.

Check-in storage returns a confirmed-save boolean; completion retains answers on failure and reuses a persisted submission ID/time for idempotent retries. Do not claim partial recording or trigger notebook copies after a rejected primary save. Notebook flows retain drafts/items until saving succeeds or the user cancels; preserve copy/check-before-resubmit guidance. Profile update failures may be partial and must direct users to inspect their profile before retrying.

Bulk schedule enable/disable checks writes and copies loaded period dictionaries; empty categories do not report success. Notebook list mutations preserve reference errors and return check-before-retry replies, especially after removal shifts numbering. Reject nonpositive, fractional, and boolean chat item numbers before mutation.

List-item services preflight a strict zero-based range against the resolved list; do not let the data-manager's mixed-index normalization reinterpret a past-end command as the last item. Preserve distinct wrong-kind and invalid-index results.

Health pause/delete checks boolean results and gives status-before-retry guidance for uncertain/partial outcomes. Linking fails closed on code-generation failure, registers pending codes only after delivery, binds verification to account/channel, rejects unsupported channels, and points invalid-code recovery to email. Delivery logs exclude addresses/codes; link-save failures suggest checking account status.

Snooze/skip/simplify exceptions return usable task recovery replies. Phrase-setting write failures suggest inspecting saved settings while preserving validation guidance. Creation failures suggest checking account status before duplicating an account; reject blank preferred names. Google Health connect needs a nonempty URL before starting the background flow and uses nontechnical recovery replies.

Notebook query results distinguish failures (`success=False`) from successful empty views. Six read services now use a strict validated snapshot plus shared selectors, so storage failures reach the flag instead of becoming `[]`. Missing files/valid empty collections remain empty; invalid or partly invalid files are preserved and rejected. Reuse `load_json_data(..., recover=False)` for non-repairing reads. Other tolerant-loader callers retain their separate limits.

---

## 6. Configuration and Integration

Error handling must integrate cleanly with logging and configuration (see section 6. "Configuration and Integration" in [ERROR_HANDLING_GUIDE.md](../core/ERROR_HANDLING_GUIDE.md#6-configuration-and-integration) and section 2. "Logging Architecture" in [LOGGING_GUIDE.md](../logs/LOGGING_GUIDE.md#2-logging-architecture)).

Routing rules:

- Do not create new environment variables for error behavior without:
  - Updating `core/config.py`, and  
  - Documenting them in section 6 of [ERROR_HANDLING_GUIDE.md](../core/ERROR_HANDLING_GUIDE.md#6-configuration-and-integration).

- Respect `MHM_TESTING` when deciding whether to surface or suppress errors in tests.  

Logging constraints:

- Prefer component loggers via `core/logger.py` for call-site / domain logging.  
- Do not introduce new raw `logging.getLogger(...)` paths for application errors.  
- Exception: `@handle_errors` uses the dedicated `mhm.error_handler` safe logger (wired to `errors.log` by `setup_error_handler_logging()`). Do not replace that with ComponentLogger inside `core/error_handling.py`.  
- Soft delivery failures that matter operationally (failed check-in / message send) should log at `ERROR` so they appear in `errors.log`.

---

## 7. Testing Error Handling

For test coverage of error handling (see section 7. "Testing Error Handling" in [ERROR_HANDLING_GUIDE.md](../core/ERROR_HANDLING_GUIDE.md#7-testing-error-handling) and section 3. "Fixtures, Utilities, and Safety" in [TESTING_GUIDE.md](../tests/TESTING_GUIDE.md#3-fixtures-utilities-and-safety)).

**Audit exclusions:** When a function intentionally has no or simpler error handling (e.g. pure default-data factories called only from a decorated caller, or a small try/except that must not return a default), add `# error_handling_exclude` or `# error handling exclude` (optionally with a reason). The error-handling analyzer then skips that function and does not flag it as missing error handling or as a Phase 1 candidate.

AI routing:

- When adding or changing error handling, also:
  - Add tests in `tests/integration/test_error_handling_improvements.py` or nearby files.  
  - Ensure both success and failure paths are covered.  
  - Use helpers in `tests\test_helpers\test_utilities` to assert on logs/metrics where appropriate.  

- Use `development_tools/error_handling/analyze_error_handling.py` and related tooling when measuring coverage or generating reports.  
- **Phase 1 and Phase 2 Auditing**: The coverage tool now provides specialized analysis for quality improvements:
  - **Phase 1**: Identifies functions with basic try-except blocks that should use `@handle_errors` decorator, with priority categorization (high/medium/low)
  - **Phase 2**: Audits generic exception raises that should be replaced with specific `MHMError` subclasses
  - Results appear in audit reports ([AI_STATUS.md](../development_tools/AI_STATUS.md), [AI_PRIORITIES.md](../development_tools/AI_PRIORITIES.md), `development_tools/CONSOLIDATED_REPORT.md`) for tracking progress
  - See [PLANS.md](../development_docs/PLANS.md) for the Error Handling Quality Improvement Plan details

Do not design new error mechanisms that are hard or impossible to test.

---

## 8. Monitoring and Debugging

For debugging guidance, rely on section 8. "Monitoring and Debugging" in [ERROR_HANDLING_GUIDE.md](../core/ERROR_HANDLING_GUIDE.md#8-monitoring-and-debugging) and section 3.4. "ERROR" in [LOGGING_GUIDE.md](../logs/LOGGING_GUIDE.md#34-error).

AI rules:

- When investigating failures:
  - Start from `logs/errors.log` plus the relevant component log.  
  - Look for repeated failures of the same operation or unhandled exceptions.  

- Prefer improving:
  - Exception types, messages, and contexts in `core/error_handling.py`.  
  - Tests that reproduce and prevent regressions.  

Avoid adding one-off debug prints; use structured logging and the existing log files.

---

## 9. Legacy and Migration

Follow section 9. "Legacy and Migration" in [ERROR_HANDLING_GUIDE.md](../core/ERROR_HANDLING_GUIDE.md#9-legacy-and-migration).

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

- Use the minimal examples in section 10. "Examples" in [ERROR_HANDLING_GUIDE.md](../core/ERROR_HANDLING_GUIDE.md#10-examples).
- Prefer reusing those examples verbatim rather than inventing new variations.

---

## 11. Cross-References

For related AI-facing routing docs:

- Logging: [AI_LOGGING_GUIDE.md](AI_LOGGING_GUIDE.md#2-logging-architecture), section 2. "Logging Architecture", and [AI_LOGGING_GUIDE.md](AI_LOGGING_GUIDE.md#4-component-log-files-and-layout), section 4. "Component Log Files and Layout".
- Testing: [AI_TESTING_GUIDE.md](AI_TESTING_GUIDE.md#7-debugging-and-troubleshooting), section 7. "Debugging and Troubleshooting", and [AI_TESTING_GUIDE.md](AI_TESTING_GUIDE.md#3-fixtures-utilities-and-safety), section 3. "Fixtures, Utilities, and Safety".
- Development workflow: [AI_DEVELOPMENT_WORKFLOW.md](AI_DEVELOPMENT_WORKFLOW.md).

For detailed explanations, always route back to [ERROR_HANDLING_GUIDE.md](../core/ERROR_HANDLING_GUIDE.md) instead of repeating content here.
