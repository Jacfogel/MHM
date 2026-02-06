# CHANGELOG_DETAIL.md - Complete Detailed Changelog History

> **File**: `development_docs/CHANGELOG_DETAIL.md`
> **Audience**: Developers and contributors  
> **Purpose**: Full historical record of project changes  
> **Style**: Chronological, detailed, reference-oriented

> **See [AI_CHANGELOG.md](../ai_development_docs/AI_CHANGELOG.md) for the AI-friendly summary**

## Overview
This file is the authoritative source for every meaningful change to the project. Entries appear in reverse chronological order and include background, goals, technical changes, documentation updates, testing steps, and outcomes.

## How to Update This File

### How to Add Changes

When adding new changes, follow this format:

```markdown
### YYYY-MM-DD - Brief Title
- **Feature**: What was added/changed, include context, technical changes, documentation updates, and testing evidence. Reference affected files or directories explicitly so future readers can trace history.
- **Impact**: the problem being solved, what this improves or fixes
```

**Important Notes:**
- **Outstanding tasks** should be documented in TODO.md, not in changelog entries
- Entries should generally be limited to a maximum of 1 per session, if an entry already exists for the current session you can edit it to include additional updates. Exceptions may be made for multiple unrelated changes
- **Always add a corresponding entry** to AI_CHANGELOG.md when adding to this detailed changelog
- **Paired document maintenance**: When updating human-facing documents, check if corresponding AI-facing documents need updates:
  - **../DEVELOPMENT_WORKFLOW.md** <-> **../ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md**
  - **../ARCHITECTURE.md** <->**../ai_development_docs/AI_ARCHITECTURE.md**
  - **../DOCUMENTATION_GUIDE.md** <->**../ai_development_docs/AI_DOCUMENTATION_GUIDE.md**
  - **CHANGELOG_DETAIL.md** <->**../ai_development_docs/AI_CHANGELOG.md**
- Keep entries **concise** and **action-oriented**
- Maintain **chronological order** (most recent first)

------------------------------------------------------------------------------------------
## Recent Changes (Most Recent First)

### 2026-02-06 - Duplicate-functions investigation, tool improvements, and planning doc
- **Feature**: (1) **Investigation**: Reviewed duplicate groups from AI_PRIORITIES and analyze_duplicate_functions results; documented verdicts for all groups (format_message, remove_period_row, add_new_period, and 26 others). Created and maintained `development_docs/DUPLICATE_FUNCTIONS_INVESTIGATION.md` as a **temporary planning file** (summary table, verdicts, recommendations; to be archived or removed once refactors are done). (2) **Tool (analyze_duplicate_functions.py)**: Deduplicate records by (file_path, line, full_name) with path normalization; filter out single-function groups before applying max_groups (pipeline fix: report top N real duplicate groups, not "top N then drop singles"); add `--max-groups N` CLI; output and JSON include records_deduplicated, groups_filtered_single_function, groups_capped. (3) **Config**: default `max_groups` 25 to 50 in config.py; user synced development_tools_config.json. After sync, full audit reports 29 groups across 26 files. (4) **TODO.md**: Refactor tasks added for period row add/remove/find_lowest (Groups 2–3, 25), _get_user_data__load_* shared loader (Group 20), find_task_by_identifier wrappers (Group 16), _is_valid_intent helper (Group 14), command parsing prompt merge (Group 18).
- **Impact**: Fewer false positives; correct pipeline (filter then cap); 29 duplicate groups documented with verdicts; refactor work tracked in TODO; investigation doc explicitly temporary.

### 2026-02-06 - Scheduler wake timer Register-ScheduledTask fix (0x80070057); custom-question test fix
- **Feature**: (1) **Wake timer**: Fixed repeated `Register-ScheduledTask : The parameter is incorrect` (HRESULT 0x80070057) when the daily scheduler sets Windows wake timers. Root cause: Windows task names cannot contain colons; the wake task name used `HH:MM` from `format_timestamp(..., TIME_ONLY_MINUTE)`. Changes in `core/scheduler.py` `set_wake_timer`: use `HHMM` (e.g. `0056`) in the task name; sanitize task name (invalid chars `\ / * ? " < > | : '` -> underscore); cap length at 200; build trigger with PowerShell `[DateTime]::ParseExact(..., 'yyyy-MM-ddTHH:mm:ss', $null)`. Cleanup (matching `Wake_` and user_id) unchanged. (2) **Custom-question tests**: In `tests/behavior/test_checkin_questions_enhancement.py`, `TestCustomQuestions` tests that were failing (save_custom_question / get_custom_questions path mismatch under parallel runs) now patch `core.config.BASE_DATA_DIR` to the test temp dir instead of setting `TEST_DATA_DIR` via monkeypatch, matching the pattern used by config coverage tests; no changes to `core/config.py`.
- **Impact**: Wake-from-sleep tasks register successfully; errors.log no longer fills with wake timer errors after 01:00. Behavior suite (1733 tests) passes; custom-question and config coverage tests stable.

### 2026-02-06 - Log rotation fix, logging noise reduction, backup/archive docs, dev-tools log isolation
- **Feature**: (1) **Log backup rotation**: Fixed `BackupDirectoryRotatingFileHandler` in `core/logger.py` so backup filenames match rotated content and older backups are no longer overwritten. When rotation was skipped on previous midnights (file under 5KB or under 1hr old), `rolloverAt` was never updated; a later rollover used a stale date and overwrote that backup. Backup names now use actual rotation time (`current_time - 1` for period-end date); `rolloverAt` is updated after every rollover and when skipping. (2) **Reduce logging noise**: Logging init and "Loaded custom system prompt" at DEBUG when run from development tools (argv); FLOW_STATE_LOAD with 0 user states at DEBUG; scheduler "Scheduler running: N total jobs" heartbeat at DEBUG (`core/logger.py`, `ai/prompt_manager.py`, `communication/message_processing/conversation_flow_manager.py`, `core/scheduler.py`). (3) **Backup vs archive docs**: LOGGING_GUIDE.md Section 6.1 "Backup vs archive" and AI_LOGGING_GUIDE.md pointer added; confirmed message.log uses same rotating handler and is included in rotation. (4) **Development-tools log isolation**: When the run is from development tools (entry point under `development_tools/` or `MHM_DEV_TOOLS_RUN=1`), all logging that would go to `app.log` is routed to `logs/ai_dev_tools.log` so the main project log is untouched. Added `_is_dev_tools_run()` and main_file override in `_get_log_paths_for_environment()` (`core/logger.py`). Subprocesses spawned by tool_wrappers and run_test_coverage set `MHM_DEV_TOOLS_RUN=1` so child processes also use ai_dev_tools.log. LOGGING_GUIDE.md Section 5.5 and AI_LOGGING_GUIDE.md updated.
- **Impact**: Restores correct backup semantics and prevents rotation data loss; keeps production logs readable; clarifies backup vs archive. **Dev-tools isolation**: Audit and other development-tool runs (including all spawned subprocesses) now write only to `logs/ai_dev_tools.log` and `tests/logs`; `app.log` is no longer written to by development tools, so the main project log stays clean.

### 2026-01-29 - Documentation drift cleanup (changelog archive alignment)
- **Feature**: Corrected changelog archive metadata paths to point at `development_docs/changelog_history/*` and added an AI changelog "Archive Notes" section to restore paired H2 heading lockstep. (See `development_docs/changelog_history/CHANGELOG_DETAIL_2025_08.md`, `development_docs/changelog_history/CHANGELOG_DETAIL_2025_09.md`, `development_docs/changelog_history/CHANGELOG_DETAIL_2025_10.md`, `development_docs/changelog_history/CHANGELOG_DETAIL_2025_11.md`, `development_docs/changelog_history/CHANGELOG_DETAIL_2025_12.md`, `ai_development_docs/AI_CHANGELOG.md`)
- **Impact**: Eliminates doc-sync pairing drift and fixes broken metadata for archived changelog files.
- **Maintenance**: Updated README to reference the canonical user data doc path and excluded `development_docs/changelog_history/` from doc path-drift scans to stop historical references from flagging as current drift. (See `README.md`, `development_tools/config/development_tools_config.json`)
### 2026-01-29 Documentation normalization groundwork (reference alignment, process hardening)
**Summary:**  
Began a repo-wide documentation normalization effort focused on eliminating duplication, clarifying canonical references, and updating AI testing guide naming. The session established a conservative, loss-averse workflow for documentation edits and clarified rules to prevent accidental content removal while working from combined documentation snapshots.
**Key outcomes:**
- Established and locked **strict documentation editing rules**, including:
  - Always start from the *full original document*.
  - Never replace documents with stubs or summaries.
  - Treat rewritten docs as strict supersets of originals.
  - Strip snapshot wrapper headers and code fences when reconstructing files.
- Identified and documented snapshot-specific formatting artifacts:
  - `## \`path/to/file.md\`` headers and ```md fences are injected by `export_docs_snapshot.py`.
  - These must be removed when producing in-repo documentation files.
- Standardized the **AI functionality testing guide rename**:
  - `SYSTEM_AI_FUNCTIONALITY_TEST_GUIDE.md`  
    -> [SYSTEM_AI_FUNCTIONALITY_TESTING_GUIDE.md](tests/ai/SYSTEM_AI_FUNCTIONALITY_TESTING_GUIDE.md)
- Updated [TESTING_GUIDE.md](tests/TESTING_GUIDE.md) to reference the new AI testing guide name while preserving all existing content.
- Confirmed that [MANUAL_TESTING_GUIDE.md](tests/MANUAL_TESTING_GUIDE.md) required only reference updates and no deduplication.
- Formalized a **"flag, don't move" rule** for documentation:
  - Content that appears better suited for [CONFIGURATION_REFERENCE.md](CONFIGURATION_REFERENCE.md) or [USER_DATA_MODEL.md](core/USER_DATA_MODEL.md) should be identified and proposed for relocation, not moved automatically.
- Added a documentation snapshot-based workflow to safely review and normalize large doc sets within tooling and upload constraints.

### 2026-01-28 - Dev Tools Format Hardening and Account Defaults
- **Feature**: Enforced strict dev-tools result shapes during load/aggregation/reporting so only standard `summary`/`details` JSON is accepted; legacy output parsing is removed outside the dedicated legacy cleanup tool paths. (See `development_tools/shared/service/{audit_orchestration,commands,data_loading,report_generation,tool_wrappers,utilities}.py`)
- **Feature**: Standardized system-signals output consumption to rely solely on the current tool result format, eliminating the legacy `system_signals_results.json` artifact from aggregation. (See `development_tools/reports/*` and report generation paths)
- **Feature**: Account schema validation now backfills required defaults and preserves normalized `features` even when validation reports errors, ensuring configuration flows remain stable. (See `core/schemas.py`, `core/user_data_handlers.py`)
- **Maintenance**: Refreshed generated audit outputs and docs after the tooling changes (function/module registries, directory tree, legacy report, coverage report, unused imports, consolidated report, AI status/priorities). (See `development_docs/*`, `development_tools/*`, `ai_development_docs/*`)
- **Tests/fixtures**: Updated coverage/behavior/dev-tools tests and helpers to align with the stricter format and compatibility cleanup workflow. (See `tests/conftest.py`, `tests/development_tools/*`, `tests/behavior/*`, `tests/unit/test_schema_validation_helpers.py`, `tests/test_utilities.py`)
- **Maintenance**: Pruned completed checklist items from TODO and refreshed plan metadata for the session wrap-up. (See [TODO.md](TODO.md), [PLANS.md](development_docs/PLANS.md))
- **Testing**: `python run_tests.py`, `python development_tools/run_development_tools.py audit --full --clear-cache`

### 2026-01-26 - Check-in Analytics and Command Handling Overhaul
- **Feature**: Rebuilt check-in analytics to be question-asked scoped with transparent category summaries, updated completion rules (all asked questions answered; skipped allowed; legacy check-ins counted as complete), and added habit/sleep/energy/mood analyses. (See `core/checkin_analytics.py`, `communication/command_handlers/analytics_handler.py`, `ui/dialogs/user_analytics_dialog.py`)
- **Feature**: Expanded analytics command recognition and slash/bang registry with hyphen/no-hyphen and show-* variants for check-in, habit, sleep, energy, mood, trends, history, and graphs; added time-window parsing for days/weeks/months plus "last N check-ins". (See `communication/message_processing/command_parser.py`, `communication/message_processing/interaction_manager.py`)
- **Feature**: Improved check-in history rendering to show all responses in original order with cleaned labels and missing-date fallback, plus decimal-safe response handling and numeric response fallbacks for check-in prompts. (See `communication/command_handlers/analytics_handler.py`, `communication/command_handlers/checkin_handler.py`, `core/checkin_dynamic_manager.py`)
- **Feature**: Preserved same-day check-in question order across expirations by caching and reusing order on restart. (See `communication/message_processing/conversation_flow_manager.py`)
- **Maintenance**: Refreshed AI/dev tooling reports and registries after analytics/command updates (function registry, module dependencies, test coverage, unused imports, audit outputs). (See `ai_development_docs/AI_FUNCTION_REGISTRY.md`, `ai_development_docs/AI_MODULE_DEPENDENCIES.md`, `development_docs/*`, `development_tools/*`)
- **Feature**: Stabilized test cleanup teardown and reduced UI test startup work when `MHM_TESTING=1`. (See `tests/conftest.py`, `ui/ui_app_qt.py`)
- **Testing**: `python -m pytest tests/behavior/test_welcome_manager_behavior.py::TestWelcomeManagerBehavior::test_mark_as_welcomed_persists_across_calls -q`

### 2026-01-24 - Strengthened tests and flaky fixes
- **Feature**: Added regression suites for `core.tags`, `core.auto_cleanup`, `communication.command_handlers.analytics_handler`, `communication.command_handlers.profile_handler`, and the reschedule-request behavior utility so the moderate-coverage modules now have targeted coverage and the failing flag-file test hits the real file semantics instead of a mock.
- **Feature**: Hardened the auto-cleanup logic helpers (tracker timestamps + interval gating) and created a deterministic `SchedulerManager.is_job_for_category` test plus auto-cleanup path isolation tests to support accurate coverage reporting under parallel runs.
- **Feature**: Fixed the intermittent `test_create_reschedule_request_creates_actual_file` failure by writing through the actual flag directory, and reran the focused behavior test; recorded the known flaky UI/task-management failure in TODO.md while noting the other recent parallel-only failures still under investigation.
- **Impact**: Coverage now exercises previously light modules, the audit `json.dump` expectation no longer fails, and clarified intermittent issues for future tracking.
- **Testing**: `pytest tests/unit/test_tags.py`, `pytest tests/unit/test_auto_cleanup_paths.py`, `pytest tests/unit/test_auto_cleanup_logic.py`, `pytest tests/unit/test_analytics_handler.py`, `pytest tests/unit/test_profile_handler.py`, `pytest tests/behavior/test_service_utilities_behavior.py -k create_reschedule_request`, `python development_tools/tests/fix_test_markers.py` (checks markers).

### 2026-01-21 - Test suite datetime canonicalization & unused import hygiene
- **Feature**: Completed the focused `datetime.now()` audit for the test suite so production-sensitive tests (scheduling, reminders, analytics, cleanup, retries, channel behavior) now go through the canonical helpers in `core/time_utilities.py`, with deterministic patching (including new fixed anchor `TEST_NOW_DT`) for relative-date assertions and inline `datetime` limited to metadata/debug-only values. The audit also cleaned up a mis-indented pytest method to prevent collection errors.
- **Impact**: Eliminates wall-clock dependence, removes the last bursts of unpredictable `datetime.now()` usage, and gives tests deterministic anchors; the hardened helpers can now be patched before logic under test runs, reducing midnight-rollover flakiness.
- **Feature**: Strengthened the unused-import hygiene workflow-`run_generate_unused_imports_report` now reruns `analyze_unused_imports` (so the markdown report always refreshes), and the cleanup touched command handlers plus communication modules to keep only necessary typing imports while preserving intentional `Any` usage.
- **Impact**: Keeps the "Obvious Unused" audit priority under control, prevents stale report data from misleading reviewers, and makes the code clearer until the remaining entries reach zero.
- **Testing**: `python run_tests.py` (rerun now that the Discord API client import includes `Any` again so the suite can collect successfully; previous run failed before we restored the typing import).

### 2026-01-21 - Datetime Canonicalization Audit (Session Update)
- **Feature**: Completed the datetime.now() audit across the test suite, replacing every production-sensitive `datetime.now()` call in tests with `core/time_utilities` helpers, patching the helpers when determinism is required, and fixing the dedented pytest method that was causing `self` to be interpreted as a fixture.
- **Impact**: Removed all remaining wall-clock-dependent imports, ensured canonical helpers are used or mocked across scheduling, analytics, cleanup, and relative-date tests, and proved the fixes by rerunning the full `python run_tests.py` suite plus the Tier-3 `development_tools/run_development_tools.py audit --full --clear-cache`.
- **Status**: [OK] datetime.now() audit complete (tests); follow-up in progress for the two coverage-audit failures (`tests/ui/test_category_management_dialog.py::TestCategoryManagementDialogRealBehavior::test_save_category_settings_updates_account_features` and `tests/behavior/test_user_data_flow_architecture.py::TestAtomicOperations::test_atomic_operation_all_types_succeed`). Up next: explicit `datetime(` construction audit.

### 2026-01-20 - Documented canonical test-time sweep and doc/test hygiene

#### Objective
Summarize the latest session's work: documenting the deterministic time helper adoption in tests and noting the command-run/doc updates that accompanied the investigation.

### 2026-01-20 - Test suite datetime canonicalization report

#### Objective
Record the broader test suite datetime canonicalization effort and reinforce the guarantees achieved by routing tests through `core/time_utilities.py`.

#### Changes Made
- Continued the project-wide sweep replacing the remaining `datetime.now()` usages in tests with canonical helpers (`now_datetime_full`, `now_datetime_minute`, strict parse helpers/format constants) especially where timestamps feed into production logic (scheduling, analytics, cleanup, conflict detection, test artifacts).
- Patched canonical helpers to provide deterministic time control where tests need repeatable behavior; left inline `datetime` only for metadata/debug states and documented the rationale in-place.
- Covered a large subset (~80%) of test files, including AI integration/validation, analytics behavior, scheduler behavior/coverage, task management behavior, check-in analytics/expiry/retry, notebook handler behavior, cleanup, and backup tests.
- Guaranteed tests no longer rely on real-time clocks for production-sensitive assertions and noted the remaining ~20 files that still need canonicalization in upcoming sessions.

#### Impact
- Confirms the test suite now aligns with production's single source of time truth and avoids flakiness from wall-clock drift.
- Makes the continuing plan explicit so future contributors know the remaining coverage targets.

#### Testing
- `python run_tests.py` (full suite run earlier in this session; 4,082 passes, 1 skip)

#### Changes Made
- Captured the ongoing "Datetime Canonicalization & Test Alignment" narrative that replaced `datetime.now()` in production-sensitive tests with canonical helpers and patches for determinism.
- Logged the intermittent UI failure (`tests/ui/test_account_creation_ui.py::TestAccountManagementRealBehavior::test_feature_enablement_persistence_real_behavior`) in [TODO.md](TODO.md) so the flake list reflects the current blocker.
- Noted the cleanup/docs/test commands (`development_tools/run_development_tools.py cleanup --full`, `development_tools/run_development_tools.py docs`, `python run_tests.py`) executed as part of this session.

#### Impact
- Provides traceability for the deterministic time work and the new intermittent test warning.
- Ensures the documentation set reflects the commands used for validation.

#### Testing
- `python run_tests.py` (complete suite run recorded earlier: 4,082 passes, 1 skip)

### 2026-01-20 - Harden error handling and timestamp helpers

#### Objective
Reduce uncategorized exception exposure and guard all time helpers so downstream callers never crash on unexpected formatting issues.

#### Changes Made
- **`core/time_utilities.py`**: Decorated the canonical timestamp helpers (`now_timestamp_*`, `format_timestamp*`, and the bridge helpers in `core/error_handling.py`) so they log failures via `handle_errors` and return safe defaults while avoiding circular imports.
- **`core/scheduler.py`**: Added `@handle_errors` to `_select_task_for_reminder__calculate_due_date_weight` to centralize recovery instead of inline try/except logic.
- **`core/checkin_analytics.py`, `core/user_data_validation.py`, `ui/ui_app_qt.py`**: Replaced the remaining `ValueError` raises with `ValidationError`/`DataError` so the analyzer now sees domain-specific exceptions and the surrounding logic catches them explicitly.
- **`core/error_handling.py`**: Redirected internal timestamp helpers to import the decorated time utilities lazily to avoid circular import issues, keeping error reports stable.

#### Impact
- **More consistent recovery**: Core helpers now follow the centralized `handle_errors` path, so logging, recovery, and retries remain uniform and test coverage can reason about failures.
- **Stronger exception taxonomy**: Using `ValidationError` and `DataError` makes the analyzer's Phase 2 recommendations go away while making caller code more explicit about why a timestamp was invalid.

#### Testing
- `python run_tests.py` (complete suite, 4 082 passes / 1 skip)
- `python development_tools/run_development_tools.py cleanup --full`
- `python development_tools/run_development_tools.py audit --full`

#### Documentation Impact
- Regenerated `development_tools/AI_PRIORITIES.md`, `AI_STATUS.md`, `consolidated_report.txt`, and the various generated reports during the Tier 3 audit run.

### 2026-01-20 Datetime Canonicalization & Test Alignment
Scope: Project-wide refactor and audit of datetime.now() usage
Status: Mostly complete (all non-test instances addressed)
Summary
Completed a comprehensive audit and refactor of all remaining non-test usages of datetime.now() across the MHM codebase. All runtime datetime acquisition is now routed through canonical helpers in core/time_utilities.py, ensuring consistent formatting, precision, and behavior across persistence, scheduling, UI logic, and internal state handling.
This work progresses the transition to core/time_utilities.py as the single source of truth for datetime handling.
Key Changes
1. Canonical "now" helpers added
- Added:
   - now_datetime_full()
   - now_datetime_minute()
- Purpose:
   - Provide canonical, local-naive datetime objects for arithmetic and comparison
   - Eliminate repeated strftime -> strptime round-trips
   - Resolve Optional (datetime | None) propagation issues flagged by type checkers
   - These helpers derive strictly from existing canonical formats; no new formats introduced.
2. All non-test datetime.now() usages removed
- Replaced every remaining instance of datetime.now() outside of tests with:
   - now_datetime_full() where a datetime object was required
   - now_timestamp_full() where a persisted or serialized string was required
- Applied across:
   - Scheduling logic
   - Task management
   - Message handling
   - Conversation/context builders
   - Cleanup routines
   - UI state handling
   - Notebook and user data management
- No behavioral changes were introduced beyond enforcing canonical time sources.
3. Verification
- Full test suite executed:
   - 4083 tests total
   - 0 failures
   - Confirms correctness and completeness of the migration
- Design Principles Maintained
   - No new datetime formats introduced
   - No redesign of core/time_utilities.py
   - Display-only and debug-only formats remain non-persistent
   - Strict helpers preferred for internal state
   - Behavioral changes limited to correctness fixes only

### 2026-01-20 - Duplicate function analyzer tool + reporting tweaks
- **Feature**: Added `development_tools/functions/analyze_duplicate_functions.py` to flag similar functions using weighted similarity (name/args/locals/imports), tokenized name matching, pair caps, and clustering for grouped output.
- **Tooling integration**: Wired config defaults in `development_tools/config/config.py`, added tool metadata/guide entries, and hooked into CLI + service wrappers + audit orchestration + report generation so it runs with audits and emits structured JSON.
- **Reporting tweak**: Removed the consolidated report "Cache Usage" line for duplicate-function analysis to keep output focused on results.
- **Impact**: Audits now surface likely duplicate clusters with deterministic scoring and cached scanning to reduce repeat run cost.
- **Files**: `development_tools/config/config.py`, `development_tools/config/development_tools_config.json`, `development_tools/config/development_tools_config.json.example`, `development_tools/shared/service/audit_orchestration.py`, `development_tools/shared/service/report_generation.py`, `development_tools/shared/service/tool_wrappers.py`, `development_tools/shared/cli_interface.py`, `development_tools/shared/tool_guide.py`, `development_tools/shared/tool_metadata.py`, [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md), [AI_DEVELOPMENT_TOOLS_GUIDE.md](development_tools/AI_DEVELOPMENT_TOOLS_GUIDE.md), [DEVELOPMENT_TOOLS_GUIDE.md](development_tools/DEVELOPMENT_TOOLS_GUIDE.md).

### 2026-01-19 - Standardized all datetime parsing and formatting across the codebase to route exclusively through core/time_utilities.py.
Removed all remaining direct uses of:
- datetime.strptime
- datetime.fromisoformat
- inline datetime format strings
- Replaced remaining strftime usages with canonical helpers and format constants.
- Updated scheduler, UI, service, validation, notebook, and test modules to use:
- strict parsers (parse_timestamp_full, parse_timestamp_minute, parse_date_only, parse_time_only_minute)
- canonical now_* helpers for timestamp generation.
- Explicitly marked and instrumented legacy compatibility parsing for historical persisted message timestamps:
- Added clear legacy annotations.
- Added logging when the legacy path is exercised.
- Preserved existing sentinel and UTC-normalization behavior.
- Updated tests to reflect canonical parsing helpers and clarified intent where legacy behavior is explicitly asserted.
- Fixed static logging violations introduced during the legacy instrumentation pass.
Notes
- This was an adoption-only change; no new datetime formats or helpers were introduced.
- Behavior is preserved unless strict parsing was required for correctness or policy compliance.
- The codebase now enforces a single source of truth for datetime handling.

### 2026-01-18 - ## Introduce core/time_utilities.py with canonical datetime formats and helpers
- Added new core/time_utilities.py as the single source of truth for all timestamp, date, and time formats in MHM.
- Defined a clear, descriptive canonical format set covering:
   - full internal timestamps (seconds)
   - minute-level timestamps (scheduler / UI)
   - date-only and time-only values
   - filename-safe timestamps
   - display-only formats
   - debug-only microsecond precision
- Introduced strict parsing helpers for critical state (parse_timestamp_full, parse_timestamp_minute, etc.) that fail safely.
- Added explicitly-scoped flexible parsing via parse_timestamp(...) for cases where multiple external timestamp shapes are legitimately expected.
- Centralized handling of external timestamp variants (ISO-like inputs) as parse-only, never emitted by the system.
- Added lightweight "now" helpers (now_timestamp_full, now_timestamp_minute, now_timestamp_filename) to eliminate scattered datetime.now().strftime(...) usage.
- Enforced design constraints:
   - no logging, config, or timezone dependencies
   - no inline datetime format strings outside this module
   - no import-time side effects
- This change is foundational and precedes a full codebase sweep to replace legacy datetime handling.
Notes:
- No behavioral changes intended yet; follow-up commits will migrate call sites incrementally.
- Tests may require updates where mocking assumptions depended on inline strftime usage.


### 2016-01-17 - Standardize datetime formatting usage and audit datetime.now() calls

- Completed sweep replacing hardcoded strftime/strptime format strings with
  canonical constants from core/service_utilities.py
- Adopted now_readable_timestamp() and now_filename_timestamp() for metadata
  and filename-safe timestamp generation where appropriate
- Audited datetime.now() usages across core, communication, and scheduler code
  and intentionally preserved datetime objects used for time arithmetic,
  comparisons, and flow logic
- Aligned cleanup metadata to use canonical readable timestamps
- Left ISO-based persistence and logger rotation behavior unchanged by design

No behavioral changes intended beyond timestamp formatting consistency.

### 2026-01-15 - Ruff rollout, selective fixes, and report generator diagnostics **IN PROGRESS**
- **Feature**: Brought Ruff into the workspace, exercised `ruff check . --fix` on a subset of safe rules, and documented the current failure mode inside the report generation step.
- **Changes**:
  1. **New formatting tool**: Added Ruff to the repository tooling suite and captured the current `ruff check . --statistics` result so we can prioritize the remaining offenses (see AI changelog entry for the full count summary).
  2. **Selective fixes**: Applied `ruff check . --fix --select` for the safe non-pep585/PEP604 annotations and sanitized suppressible-exception handling; but the large `development_tools` folder triggered a TypeError in the status generator, so we rolled back those fixes and now run the audit without touching that folder until we guard the offending `|` usage.
  3. **Audit health**: Tier 3 audits still finish, but the AI_STATUS/AI_PRIORITIES/consolidated reports currently log "unsupported operand type(s) for |..." and drop placeholder content until the report generator is fixed.
  4. **Current Ruff state**: `ruff check . --statistics` reports 5,842 findings (1,259 `F401`, 938 `UP025`, 779 `UP006`, 347 `E402`, etc.) with 3,777 fixable. We'll keep the remaining work tracked and revisit once the report generator stops crashing.
- **Impact**: Ruff is now in place and partially applied; the remaining lint backlog is known, and the Tier 3-generated documents remain blocked by the report-generation TypeError until that expression is defended.
- **Testing**: `ruff check . --statistics` (see counts below); Tier 3 audit now runs without the Ruff-induced break.

### 2026-01-15 - Test Flags Isolation, Logging Doc Fix, and Domain Mapping Refresh
- **Feature**: Routed shutdown/test flag files through `core.service_utilities.get_flags_dir()` (used by `core/service.py`, `core/headless_service.py`, and `ui/ui_app_qt.py`) and set `MHM_FLAGS_DIR` to `tests/data/flags` in `tests/conftest.py` to prevent test runs from touching live service flags. Added a small behavior test for flag routing. Aligned `TEST_VERBOSE_LOGS` documentation in [LOGGING_GUIDE.md](logs/LOGGING_GUIDE.md) with actual test logging levels. Added path-based domain inference and development-tools mapping for test-file coverage caching and regenerated the cache.
- **Impact**: Running tests no longer stops a live service, logging docs match real behavior, and the test-file cache no longer leaves unmapped tests.
- **Testing**: `python run_tests.py`, `python -m pytest tests/ui/test_task_management_dialog.py::TestTaskManagementDialogRealBehavior::test_save_task_settings_persists_after_reload -v`, `python development_tools/run_development_tools.py audit --full` (one intermittent UI test failure during coverage run).

### 2026-01-14 - User Management Retirement Finalized and Dev Tools Cache Cleanup
- **Feature**: Removed the `core/user_management.py` shim and finalized the user data handler migration by cleaning legacy references in `core/user_data_handlers.py`, `core/user_data_validation.py`, `core/user_data_manager.py`, and `core/__init__.py`. Updated development tools generators to stop emitting `core/user_management` in AI function registries and module dependency summaries, and improved dev tools audit aggregation to prefer the newest tool result when duplicate JSONs exist. Cleared a stale `development_tools/reports/jsons/analyze_package_exports_results.json` and regenerated the AI function registry and consolidated audit outputs. Removed the completed retirement task from [TODO.md](TODO.md).
- **Impact**: Fully retires the legacy user management module, keeps generated docs clean, and prevents stale dev tool results from reintroducing removed file references.
- **Testing**: `python development_tools/run_development_tools.py docs`, `python development_tools/run_development_tools.py audit --full`

### 2026-01-14 - Legacy Cleanup Progress, Doc Tooling Fix, and Test Repairs
- **Feature**: Continued legacy retirement by moving identifier/category/preset/timezone helpers into `core/user_data_handlers.py`, delegating legacy accessors in `core/user_management.py`, and updating production imports (communication/core/ui) to use the centralized handlers. Removed legacy logger aliases in `core/service.py` and `core/message_management.py`. Fixed development tools reporting guidance to remove the invalid `doc-sync --fix` instruction in `development_tools/shared/service/report_generation.py`. Updated `tests/behavior/test_schedule_handler_behavior.py` mocks to patch `core.user_data_handlers.get_user_categories` after the import migration and refreshed the `core.user_management` retirement task status in [TODO.md](TODO.md).
- **Impact**: Reduced reliance on legacy user management paths, clarified documentation tool guidance, and restored test stability for schedule handler behavior.
- **Testing**: `python -m pytest tests/behavior/test_schedule_handler_behavior.py::TestScheduleHandlerBehavior::test_schedule_handler_schedule_status tests/unit/test_user_management.py::TestUserManagementEdgeCases::test_get_user_preferences_corrupted_file -vv`

### 2026-01-14 - Pyright Optional Fixes, Coverage Cache Mapping Fix, and UI Test Stabilization **COMPLETED**
- **Feature**: Reduced pyright noise with optional-safe updates in core/communication, fixed test-file coverage cache mapping persistence, and stabilized account creation UI integration tests under parallel runs.
- **Changes**:
  1. **Pyright configuration + type safety**:
     - Updated `pyrightconfig.json` exclusions (temporary: `development_tools/**`, `tests/**`; permanent: generated UI).
     - Added optional/None-safe guards and stricter typing in core and communication modules to address `reportOptionalMemberAccess` and `reportArgumentType` findings.
  2. **Error handling**:
     - Added error handling to email bot `_get_email_config` and propagated safe handling for missing config.
  3. **Coverage cache fix**:
     - Fixed test-file coverage cache updates by batching cache loads/saves to prevent mapping wipes.
  4. **UI test stability**:
     - Marked account creation integration tests as `no_parallel` to avoid shared test-data/index races.
- **Impact**: Pyright warnings reduced, cache mappings persist across runs, and UI integration tests avoid parallel data contention.
- **Files**: `pyrightconfig.json`, `core/*`, `communication/*`, `development_tools/tests/run_test_coverage.py`, `development_tools/tests/test_file_coverage_cache.py`, `tests/ui/test_account_creation_ui.py`.
- **Testing**:
  - Observed full test/audit runs via `python run_tests.py` and `python development_tools/run_development_tools.py audit --full` (one logger behavior test failed during a full coverage run).

### 2026-01-13 - Pyright Cleanup, Dev Tools Exclusions, and Test/Script Fixes **COMPLETED**
- **Feature**: Eliminated pyright errors with minimal type-safe fixes, tightened dev tools exclusion matching on Windows, and repaired supporting scripts/tests.
- **Changes**:
  1. **Pyright cleanup**:
     - Resolved pyright errors across dev tools, tests, and scripts by adding precise typing, fixing duplicates, and correcting imports.
     - Standardized discord send kwargs typing to satisfy overloads and avoid invalid call signatures.
  2. **Dev tools exclusions**:
     - Normalized paths in `development_tools/shared/standard_exclusions.py` to ensure `tests\data\...` paths are excluded on Windows.
  3. **Scripts and utilities**:
     - Restored `scripts/testing/script_test_utils_functions.py` with current module imports.
     - Updated script imports for shared dev tools modules and user data lookups.
  4. **Testing**:
     - Fixed duplicate test names and minor test-only typing/fixture issues.
     - Recorded test results from full test run and full audit.
- **Impact**: Type checking is clean, legacy scans avoid temp test data on Windows, and scripts/tests align with current module layout.
- **Files**: `development_tools/shared/standard_exclusions.py`, `development_tools/shared/service/*.py`, `development_tools/docs/analyze_documentation.py`, `development_tools/error_handling/analyze_error_handling.py`, `development_tools/functions/*.py`, `communication/communication_channels/discord/*.py`, `scripts/*`, `tests/*`, `requirements.txt`.
- **Testing**:
  - `python run_tests.py` (parallel + no_parallel; 4081 passed, 1 skipped)
  - `python development_tools/run_development_tools.py audit --full`

### 2026-01-13 - Documentation Routing, Planning Cleanup, and Legacy Tracking Updates **COMPLETED**
- **Feature**: Standardized planning docs, expanded AI routing guidance, clarified UI/test patterns, and updated legacy tracking patterns in development tools.
- **Changes**:
  1. **Documentation routing fixes**:
     - Added missing routing links in [AI_DEVELOPMENT_WORKFLOW.md](ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md) for run commands, emergency procedures, and learning resources.
     - Clarified configuration routing in [AI_ARCHITECTURE.md](ai_development_docs/AI_ARCHITECTURE.md) to point to workflow/run docs instead of logging.
     - Fixed duplicated "section 2." wording in [ARCHITECTURE.md](ARCHITECTURE.md).
  2. **UI & testing guidance**:
     - Added explicit UI flow + signal-based update patterns in [UI_GUIDE.md](ui/UI_GUIDE.md).
     - Promoted "Test logging isolation" to a headline rule in [TESTING_GUIDE.md](tests/TESTING_GUIDE.md) and [AI_TESTING_GUIDE.md](ai_development_docs/AI_TESTING_GUIDE.md).
  3. **Planning cleanup and task organization**:
     - Reorganized [TODO.md](TODO.md) by priority, removed completed/overlapping items, updated the channel command registry follow-ups, and refreshed `core.user_management` retirement subtasks.
     - Refined [PLANS.md](development_docs/PLANS.md) content (removed stale sections, consolidated UI testing into UI migration, updated Testing Strategy plan), and extracted the Task System plan into [TASKS_PLAN.md](development_docs/TASKS_PLAN.md).
     - Added plan metadata/parent relationships for [PLANS.md](development_docs/PLANS.md), [NOTES_PLAN.md](development_docs/NOTES_PLAN.md), and [TASKS_PLAN.md](development_docs/TASKS_PLAN.md), and normalized `.md` links in [PLANS.md](development_docs/PLANS.md).
  4. **Documentation guide cleanup**:
     - Fixed link/path drift and unconverted link references in [DOCUMENTATION_GUIDE.md](DOCUMENTATION_GUIDE.md) and [AI_DOCUMENTATION_GUIDE.md](ai_development_docs/AI_DOCUMENTATION_GUIDE.md).
  5. **Legacy tracking updates**:
     - Added legacy inventory tracking patterns in `development_tools/config/development_tools_config.json` and regenerated legacy reporting outputs.
     - Added a dev tools plan item for the example marking standards checker in `development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V3.md`.
- **Impact**: Documentation routing and testing guidance are clearer, plan ownership is explicit, TODO/plan scope is tighter, and legacy reporting now tracks additional compatibility markers.
- **Files**: [AI_DEVELOPMENT_WORKFLOW.md](ai_development_docs/AI_DEVELOPMENT_WORKFLOW.md), [AI_ARCHITECTURE.md](ai_development_docs/AI_ARCHITECTURE.md), [AI_DOCUMENTATION_GUIDE.md](ai_development_docs/AI_DOCUMENTATION_GUIDE.md), [DOCUMENTATION_GUIDE.md](DOCUMENTATION_GUIDE.md), [UI_GUIDE.md](ui/UI_GUIDE.md), [TESTING_GUIDE.md](tests/TESTING_GUIDE.md), [AI_TESTING_GUIDE.md](ai_development_docs/AI_TESTING_GUIDE.md), [ARCHITECTURE.md](ARCHITECTURE.md), [TODO.md](TODO.md), [PLANS.md](development_docs/PLANS.md), [NOTES_PLAN.md](development_docs/NOTES_PLAN.md), [TASKS_PLAN.md](development_docs/TASKS_PLAN.md), `development_tools/config/development_tools_config.json`, `development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V3.md`, `development_docs/LEGACY_REFERENCE_REPORT.md`
- **Testing**: Not run (documentation/config updates only).

### 2026-01-13 - Coverage Caching Overhaul and Dev Tools Cache **COMPLETED**
- **Feature**: Reworked test coverage caching to use test-file selection + merge, preserved merged coverage outputs, and added a dedicated dev tools coverage cache.
- **Changes**:
  1. **Test Coverage Caching (Main Suite)**:
     - Implemented test-file-based caching and selective test execution by domain mappings
     - Added full-coverage cache reuse when no domains changed
     - Filtered fresh coverage to changed domains before merging; merged line coverage to avoid drops
     - Preserved merged `coverage.json` during HTML generation to prevent overwrites
  2. **Dev Tools Coverage Caching**:
     - Added `development_tools/tests/dev_tools_coverage_cache.py` to store dev tools coverage JSON and source mtimes
     - Dev tools coverage now reuses cached data when unchanged
     - Cache location: `development_tools/tests/jsons/dev_tools_coverage_cache.json`
  3. **Cache Storage and Cleanup**:
     - Moved coverage cache files into `development_tools/tests/jsons/` alongside other JSON artifacts
     - Updated `--clear-cache` and cleanup logic to clear test-file + dev tools caches
     - Removed legacy domain-aware cache (`development_tools/tests/coverage_cache.py`)
  4. **Test Discovery and Logging Improvements**:
     - Excluded `tests/data/` from test discovery and unmapped-test reporting
     - Clearer cache logging (run counts, unmapped test file warnings)
     - Added human-readable timestamps/metadata to coverage JSON outputs
  5. **Documentation Updates**:
     - Updated AI and human dev tools guides plus improvement plan to reflect test-file + dev tools caching
- **Impact**: Selective runs remain accurate (~72% coverage), no longer overwritten by regenerated JSON, dev tools coverage skips pytest when unchanged, and cache cleanup is consistent.
- **Files**: `development_tools/tests/run_test_coverage.py`, `development_tools/tests/test_file_coverage_cache.py`, `development_tools/tests/dev_tools_coverage_cache.py`, `development_tools/tests/domain_mapper.py`, `development_tools/run_development_tools.py`, `development_tools/shared/fix_project_cleanup.py`, [AI_DEVELOPMENT_TOOLS_GUIDE.md](development_tools/AI_DEVELOPMENT_TOOLS_GUIDE.md), [DEVELOPMENT_TOOLS_GUIDE.md](development_tools/DEVELOPMENT_TOOLS_GUIDE.md), `development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V3.md`
- **Testing**: Verified via repeated `audit --full` runs (cached/uncached behavior) and selective runs after domain/dev tools changes; one selective run reported a failing behavior test (`tests/behavior/test_discord_task_reminder_followup.py::TestDiscordTaskReminderFollowup::test_discord_reminder_followup_no_reminders`) while coverage still merged.

### 2026-01-12 - Quick Note Feature, Command Parsing Improvements, and Documentation Updates **COMPLETED**
- **Feature**: Added quick note command with automatic grouping, improved command parsing, fixed short ID formatting, and condensed manual testing guide
- **Changes**:
  1. **Quick Note Command Implementation**:
     - Added `create_quick_note` intent with aliases: `!qn`, `!qnote`, `!quickn`, `!quicknote`, `!q note`, `quick note`
     - Quick notes automatically placed in "Quick Notes" group, no body text required
     - If no title provided, uses timestamp as default title (e.g., "Quick Note - 2024-01-15 14:30")
     - Added handler method `_handle_create_quick_note()` in `communication/command_handlers/notebook_handler.py`
     - Registered intent in `notebook_handler.py` and `interaction_manager.py`
     - Added early pattern checking in `command_parser.py` to ensure quick note patterns match before task patterns
  2. **Command Parsing Improvements**:
     - Fixed "create note titled 'X' with body 'Y'" natural language format - split into separate patterns for better matching
     - Added early priority checking for `create_quick_note` patterns to prevent misinterpretation as task creation
     - Fixed entity extraction for "titled with body" format to properly extract both title and body
  3. **Short ID Formatting Fix**:
     - Updated `_format_entry_id()` in `notebook_handler.py` to use `format_short_id()` from `notebook_validation.py`
     - Ensures consistent format without dashes (`n123abc` instead of `n-123abc`) for easier mobile typing
  4. **AI Command List Updates**:
     - Added `create_quick_note` to available actions list in `ai/prompt_manager.py` (line 121)
     - Added `create_quick_note` and full notebook command list to `ai/chatbot.py` fallback prompt (line 979)
  5. **Documentation Updates**:
     - Condensed [MANUAL_DISCORD_TEST_GUIDE.md](tests/MANUAL_DISCORD_TEST_GUIDE.md) from 1352 lines to ~396 lines - removed verbose step-by-step instructions, made command-focused with clear separation between test cases
     - Added comprehensive quick note test section to manual testing guide with all aliases and verification steps
     - Updated [NOTES_PLAN.md](development_docs/NOTES_PLAN.md) to document quick note command in V0 section and update implementation status
  6. **Task Creation**:
     - Added task to [TODO.md](TODO.md) to investigate why there are two separate AI command lists and explore dynamic generation from handlers/parser
- **Files Changed**:
  - `communication/message_processing/command_parser.py` - Added quick note patterns, fixed "titled with body" pattern, added early quick note checking
  - `communication/command_handlers/notebook_handler.py` - Added `_handle_create_quick_note()` method, updated to use `format_short_id()`
  - `communication/message_processing/interaction_manager.py` - Added `create_quick_note` to intent list
  - `ai/prompt_manager.py` - Added `create_quick_note` to available actions list
  - `ai/chatbot.py` - Added `create_quick_note` and full notebook commands to fallback prompt
  - [MANUAL_DISCORD_TEST_GUIDE.md](tests/MANUAL_DISCORD_TEST_GUIDE.md) - Condensed format, added quick note test section
  - [NOTES_PLAN.md](development_docs/NOTES_PLAN.md) - Added quick note to command set and implementation status
  - [TODO.md](TODO.md) - Added task for investigating dynamic command list generation
- **Impact**: Users can now create quick notes without body text that are automatically organized in "Quick Notes" group. Fixed issue where quick note commands were being misinterpreted as task creation (defaulting to "buy groceries"). Improved command parsing for natural language note creation. Documentation is now more concise and easier to use for manual testing.

### 2026-01-12 - Domain-Aware Caching Fixes and Cleanup Command Improvements **COMPLETED**
- **Feature**: Fixed domain-aware caching implementation issues and improved cleanup command to mirror audit structure
- **Changes**:
  1. **Domain-Aware Caching Fixes**:
     - Fixed main coverage incorrectly detecting `development_tools` domain as changed - now filters to only main coverage domains (core, communication, ui, tasks, ai, user, notebook)
     - Fixed duplicate log messages by changing "Domain-aware coverage caching enabled" to debug level
     - Ensured only `.py` files are tracked for changes (ignores .md, .txt, .json, .log files) with explicit filtering in `get_source_file_mtimes()`
     - Improved domain isolation: main coverage and dev tools coverage use separate domain keys and don't interfere with each other
     - Fixed cache merging logic to properly handle parallel execution scenarios with domain filtering
  2. **Cache Management Integration**:
     - Updated `_clear_all_caches()` in `run_development_tools.py` to include domain-aware coverage cache cleanup
     - Updated `cleanup_coverage_files()` in `fix_project_cleanup.py` to include domain-aware cache cleanup
     - Cache location: `development_tools/tests/.coverage_cache/domain_coverage_cache.json`
  3. **Cleanup Command Fixes and Improvements**:
     - Fixed `run_cleanup()` method in `commands.py` to properly return result dictionary (was returning None, causing `'NoneType' object has no attribute 'get'` error)
     - Implemented proper `ProjectCleanup` integration with error handling
     - Added `--full` flag to cleanup command to mirror audit structure
     - Changed default behavior: `cleanup` (no flags) now only cleans `__pycache__` directories and temp test files (conservative default)
     - `cleanup --full` cleans everything including tool caches, coverage files, and domain-aware cache
     - Tool caches are only cleaned when `--full` is specified (prevents accidental cache clearing during normal cleanup)
     - Updated help text to reflect new behavior and clarify default vs full cleanup
  4. **Code Quality**:
     - Added `include_tool_caches` parameter to `cleanup_cache_directories()` and `cleanup_all()` methods
     - Improved error handling in cleanup command with try/except blocks
     - Updated documentation to reflect new cleanup command structure
- **Impact**: 
  - Domain-aware caching now works correctly with proper domain isolation, preventing unnecessary test runs
  - Cleanup command is functional and follows consistent pattern with audit command (default = conservative, --full = everything)
  - Tool caches are protected from accidental clearing during normal cleanup operations
  - Cache management is now comprehensive and consistent across all tools
- **Files**: `development_tools/tests/run_test_coverage.py`, `development_tools/tests/coverage_cache.py`, `development_tools/run_development_tools.py`, `development_tools/shared/fix_project_cleanup.py`, `development_tools/shared/service/commands.py`, `development_tools/shared/cli_interface.py`
- **Testing**: Domain-aware caching verified working correctly with proper domain filtering. Cleanup command tested and working with both default and --full modes.

### 2026-01-11 - Test Coverage Caching Implementation and Domain-Aware Cache POC **COMPLETED**
- **Feature**: Implemented coverage analysis caching and domain-aware coverage cache proof-of-concept to accelerate test coverage generation workflow. Moved test-specific caching modules to appropriate directory and fixed related test failures and documentation issues.
- **Changes**:
  1. **Coverage Analysis Caching**:
     - Added caching support to `development_tools/tests/analyze_test_coverage.py` using `MtimeFileCache`
     - Caches analysis results based on coverage JSON file modification time
     - Saves ~2s per run when coverage data hasn't changed (analysis phase only)
     - Cache location: `development_tools/tests/jsons/.analyze_test_coverage_cache.json`
     - Added `use_cache` parameter to `TestCoverageAnalyzer.__init__()` and `analyze_coverage()` method
  2. **Domain-Aware Coverage Cache POC**:
     - Created `development_tools/tests/domain_mapper.py` (`DomainMapper` class) to map source code directories to test directories and pytest markers
     - Maps source domains (core/, communication/, ui/, tasks/, ai/, user/, notebook/) to test directories and markers
     - Extracts pytest markers from test files using regex parsing
     - Provides utilities for generating pytest marker filters and test path lists for changed domains
     - Created `development_tools/tests/coverage_cache.py` (`DomainAwareCoverageCache` class) for domain-aware caching
     - Tracks source file modification times per domain
     - Detects changed domains by comparing current mtimes with cached mtimes
     - Enables granular cache invalidation: when source files in a domain change, only that domain's cache is invalidated
     - Cache location: `development_tools/tests/.coverage_cache/domain_coverage_cache.json`
     - **Status**: Infrastructure complete (POC), ready for integration with `run_test_coverage.py` (future work)
  3. **File Organization**:
     - Moved `domain_mapper.py` and `coverage_cache.py` from `development_tools/shared/` to `development_tools/tests/` (test-specific tools)
     - Updated all imports and documentation references to reflect new locations
  4. **Documentation Updates**:
     - Updated [AI_DEVELOPMENT_TOOLS_GUIDE.md](development_tools/AI_DEVELOPMENT_TOOLS_GUIDE.md) with caching documentation:
       - Coverage Analysis Caching section with implementation details
       - Domain-Aware Coverage Cache POC section with status and usage notes
       - Updated tool catalog entries for new caching modules
     - Updated [DEVELOPMENT_TOOLS_GUIDE.md](development_tools/DEVELOPMENT_TOOLS_GUIDE.md) with matching caching documentation
     - Updated `development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V3.md` section 2.10 to mark POC as complete
     - Fixed path drift issues: updated 4 references to `run_test_coverage.py` to include `tests/` prefix
  5. **Test Fixes**:
     - Fixed `test_view_log_file_opens_log_file` in `tests/ui/test_ui_app_qt_main.py`:
       - Added missing `qapp` fixture (required for Qt UI tests)
       - Fixed `webbrowser.open` patching to use `MagicMock` and patch at module level
  6. **Code Quality**:
     - Removed unused `List` import from `coverage_cache.py`
     - Fixed ASCII compliance issues in documentation
- **Impact**: 
  - Coverage analysis now caches results, saving ~2s per run when coverage data unchanged
  - Domain-aware caching infrastructure ready for future integration, enabling potential 80%+ time savings when only one domain changes
  - Foundation laid for intelligent test selection and partial test execution
  - Test suite: 3917 passed, 0 failed (test failure fixed), 2 skipped
- **What's Complete**:
  - [OK] Coverage analysis caching (implemented and working)
  - [OK] Domain mapping infrastructure (complete)
  - [OK] Domain-aware coverage cache POC (infrastructure complete)
  - [OK] Documentation updated (both human and AI guides)
  - [OK] File organization (moved to `tests/` directory)
- **What Remains** (Future Enhancements):
  - [OK] **Integrate domain-aware caching with test execution**: COMPLETED - `run_test_coverage.py` now uses `DomainAwareCoverageCache` for intelligent test selection
    - Uses `get_changed_domains()` to detect which domains need re-testing
    - Uses `get_pytest_marker_filter()` to generate pytest marker filters
    - Uses `get_test_directories_for_domains()` to limit test discovery to changed domains
    - Only runs tests for changed domains, merges cached coverage data from unchanged domains
    - Enabled by default - disable with `--no-domain-cache` flag
    - Supports both serial and parallel test execution modes
    - Integrated with dev tools coverage for complete caching coverage
  - [OK] **Domain isolation and filtering**: COMPLETED - Main coverage now filters out `development_tools` domain to prevent cross-contamination
    - Main coverage checks only main coverage domains (core, communication, ui, tasks, ai, user, notebook)
    - Dev tools coverage uses separate domain key and doesn't interfere with main coverage
    - Fixed duplicate log messages (changed to debug level)
    - Only tracks `.py` files (ignores .md, .txt, .json, .log files)
  - [OK] **Cache management integration**: COMPLETED - Domain-aware cache now included in `--clear-cache` flag and cleanup command
    - `--clear-cache` flag now clears domain-aware coverage cache
    - `cleanup --coverage` command now includes domain-aware cache cleanup
    - Cache location: `development_tools/tests/.coverage_cache/domain_coverage_cache.json`
  - [OK] **Domain-aware caching fixes and improvements**: COMPLETED - Fixed several issues with domain-aware caching implementation
    - Fixed main coverage incorrectly detecting `development_tools` domain as changed (now filters to only main coverage domains)
    - Fixed duplicate log messages (changed "Domain-aware coverage caching enabled" to debug level)
    - Ensured only `.py` files are tracked for changes (ignores .md, .txt, .json, .log files)
    - Improved domain isolation: main coverage and dev tools coverage use separate domain keys
    - Fixed cache merging logic to properly handle parallel execution scenarios
  - [OK] **Cleanup command improvements**: COMPLETED - Fixed broken cleanup command and updated to mirror audit structure
    - Fixed `run_cleanup()` method to properly return result dictionary (was returning None)
    - Added `--full` flag to cleanup command (mirrors audit structure)
    - Default cleanup (`cleanup` with no flags) now only cleans `__pycache__` and temp test files (conservative default)
    - `cleanup --full` cleans everything including tool caches, coverage files, and domain-aware cache
    - Tool caches are only cleaned when `--full` is specified (prevents accidental cache clearing)
    - Updated help text to reflect new behavior
- **Files**: `development_tools/tests/analyze_test_coverage.py`, `development_tools/tests/domain_mapper.py`, `development_tools/tests/coverage_cache.py`, `development_tools/tests/run_test_coverage.py`, `development_tools/run_development_tools.py`, `development_tools/shared/fix_project_cleanup.py`, `development_tools/shared/service/commands.py`, `development_tools/shared/cli_interface.py`, [AI_DEVELOPMENT_TOOLS_GUIDE.md](development_tools/AI_DEVELOPMENT_TOOLS_GUIDE.md), [DEVELOPMENT_TOOLS_GUIDE.md](development_tools/DEVELOPMENT_TOOLS_GUIDE.md), `tests/ui/test_ui_app_qt_main.py`
- **Testing**: Coverage analysis caching verified working (saves ~2s when coverage JSON unchanged). Domain-aware cache POC infrastructure tested and ready. Test suite: 3917 passed, 0 failed, 2 skipped.

### 2026-01-11 - Development Tools Cache Management Improvements **COMPLETED**
- **Feature**: Added `--clear-cache` flag to development tools CLI and removed all legacy `cache_file` parameter references, simplifying cache management and ensuring all tools use standardized storage exclusively.
- **Changes**:
  1. **Cache Clearing Command**:
     - Added `--clear-cache` global argument to `run_development_tools.py` that clears all cache files before running commands
     - Implemented `_clear_all_caches()` function that finds and deletes cache files from standardized storage locations (`development_tools/{domain}/jsons/.{tool}_cache.json`)
     - Removed legacy cache file checks (no longer needed - all tools use standardized storage)
     - Cache clearing happens before service initialization, ensuring tools start with clean cache when requested
  2. **Removed Legacy `cache_file` Parameter**:
     - Removed `cache_file` parameter from `MtimeFileCache.__init__()` - now requires `tool_name` and `domain` for standardized storage
     - Updated all 7 tools using `MtimeFileCache` to remove `cache_file` variable definitions and parameter passing:
       - `analyze_ascii_compliance.py`, `analyze_missing_addresses.py`, `analyze_heading_numbering.py`, `analyze_unconverted_links.py`, `analyze_path_drift.py`, `analyze_unused_imports.py`, `analyze_legacy_references.py`
     - Removed `# Legacy fallback` comments from all tools
     - Updated `_load_mtime_cached_tool_results()` in `data_loading.py` to use `load_tool_cache()` instead of direct file access
     - Updated all 6 callers in `commands.py` and `tool_wrappers.py` to remove `cache_file` argument
     - Updated `report_generation.py` to use `load_tool_cache()` instead of direct file access
     - Updated `get_cache_stats()` to return `tool_name` and `domain` instead of `cache_file` path
     - Updated docstring example in `mtime_cache.py` to show standardized storage usage
  3. **Caching Exploration Plan**:
     - Created comprehensive plan for exploring caching strategies for test coverage and other development tools
     - Plan includes domain-aware caching approach using test directory structure and pytest markers (user insight)
     - Plan documents investigation, evaluation, and implementation phases for caching improvements
- **Impact**: 
  - Users can now easily clear all caches with `--clear-cache` flag for fresh runs when needed
  - All tools now exclusively use standardized storage - no legacy code paths remain
  - Codebase is cleaner with removed unused `cache_file` parameter and legacy comments
  - Foundation laid for future caching improvements (test coverage, domain-aware caching)
- **Files**: `development_tools/run_development_tools.py`, `development_tools/shared/mtime_cache.py`, `development_tools/docs/analyze_*.py` (5 files), `development_tools/imports/analyze_unused_imports.py`, `development_tools/legacy/analyze_legacy_references.py`, `development_tools/shared/service/data_loading.py`, `development_tools/shared/service/commands.py`, `development_tools/shared/service/tool_wrappers.py`, `development_tools/shared/service/report_generation.py`, `.cursor/plans/caching_exploration_for_development_tools_fb102ab8.plan.md`
- **Testing**: Verified `--clear-cache` flag works correctly (clears 6-7 cache files), quick audit runs successfully after changes, no linter errors

### 2026-01-11 - Legacy Code Cleanup and Cache Invalidation Enhancement **COMPLETED**
- **Feature**: Completed comprehensive legacy code cleanup, reducing legacy markers from 25 to 0 across 8 files, and enhanced cache invalidation to handle config-based pattern changes in development tools.
- **Changes**:
  1. **Legacy Code Removal**:
     - Removed `development_tools/reports/system_signals.py` (legacy file, replaced by `analyze_system_signals.py`)
     - Removed `run_system_signals()` wrapper method from `development_tools/shared/service/commands.py`
     - Updated all references from `system_signals` to `analyze_system_signals` across CLI interface, test files, and tool metadata
     - Removed legacy `all_cleanup` parameter from `run_cleanup()` method
     - Updated test files to remove commented-out legacy compatibility code
     - Fixed documentation path drift: updated 3 references in `AI_DEVELOPMENT_TOOLS_GUIDE.md` from `system_signals.py` to `analyze_system_signals.py`
  2. **Cache Invalidation Enhancement**:
     - Enhanced `MtimeFileCache` in `development_tools/shared/mtime_cache.py` to track config file mtime and automatically invalidate cache when `development_tools_config.json` changes
     - Added `_check_config_staleness()` method to compare config mtime with cached mtime and clear cache if stale
     - Added `_update_config_mtime_in_cache()` to store current config mtime in cache metadata
     - Modified `__init__` to call `_check_config_staleness()` after loading cache
     - Modified `save_cache()` to update config mtime before saving
  3. **Legacy Analyzer Cache Filtering**:
     - Fixed `analyze_legacy_references.py` to filter cached results to only include pattern types currently in config
     - Added validation: `if pattern_type in self.legacy_patterns` before using cached results
     - Prevents stale cached results from showing removed patterns (e.g., `dry_run`, `coverage`) after config updates
  4. **Documentation Fixes**:
     - Fixed unconverted links in `AI_CHANGELOG.md` (automated via `doc-fix --convert-links`)
     - Fixed documentation path drift in `AI_DEVELOPMENT_TOOLS_GUIDE.md` (3 references updated)
- **Impact**: 
  - **Legacy markers reduced from 25 to 0** across 8 files -> **0 files with issues**
  - Cache invalidation now works correctly when config changes, preventing stale analysis results
  - Legacy analyzer properly filters cached results against current config patterns
  - All development tools now automatically invalidate cache when `development_tools_config.json` changes
- **Files**: `development_tools/shared/mtime_cache.py`, `development_tools/legacy/analyze_legacy_references.py`, `development_tools/shared/service/commands.py`, `development_tools/shared/cli_interface.py`, `development_tools/shared/tool_metadata.py`, [AI_DEVELOPMENT_TOOLS_GUIDE.md](development_tools/AI_DEVELOPMENT_TOOLS_GUIDE.md), test files, `development_tools/config/development_tools_config.json`
- **Testing**: Legacy reference report now shows 0 issues (previously 25 markers in 8 files). Cache invalidation verified working via mtime comparison tests.

### 2026-01-10 - Notebook Short ID Format Update: Removed Dash for Mobile-Friendly Typing **COMPLETED**
- **Feature**: Updated notebook short ID format from `n-123abc` to `n123abc` (removed dash) for easier mobile typing. Updated all implementation code, tests, and documentation to use the new format. Removed backward compatibility as requested by user.
- **Changes**:
  1. **Implementation Code Updates**:
     - Updated `notebook/notebook_validation.py`: `format_short_id()` now returns `f"{prefix}{fragment}"` (no dash), `parse_short_id()` parses no-dash format, `is_valid_entry_reference()` validates no-dash format, updated docstrings to reflect new format
     - Updated `communication/command_handlers/notebook_handler.py`: `_format_entry_id()` formats as `f"{kind_prefix}{short_id}"` (no dash), updated help examples
     - Updated `notebook/notebook_data_manager.py`: `_find_entry_by_ref()` parses no-dash format with comment noting "no dash - mobile-friendly format"
  2. **Test Code Updates**:
     - Updated `tests/behavior/test_notebook_handler_behavior.py`: Changed all short ID formats from `n-123abc` to `n123abc`, updated test assertions, fixed all test cases that create short IDs manually
     - Updated `tests/unit/test_notebook_validation.py`: Updated validation tests to use new format, fixed `test_format_short_id()` to check for prefix without dash, updated `test_is_valid_entry_reference_with_title()` with improved validation logic
     - Updated `tests/integration/test_notebook_validation_integration.py`: Fixed all short ID creation to use new format (no dash)
  3. **Validation Logic Improvements**:
     - Updated `is_valid_entry_reference()` to only check invalid prefix pattern for strings <= 9 chars (short IDs are max 9: prefix + 8 hex), allowing long title strings like `'a' * 100` to be valid as title references
  4. **Documentation Updates**:
     - Updated [NOTES_PLAN.md](development_docs/NOTES_PLAN.md): Documented new format, noted backward compatibility removed, updated examples
     - Updated docstrings in validation functions to reflect new format
- **Impact**: Short IDs are now easier to type on mobile devices (no dash required). All code, tests, and documentation consistently use the new format. Test suite: 4074 passed, 1 failed (unrelated account creation UI test), 1 skipped. All notebook-related tests passing.
- **Files**: `notebook/notebook_validation.py`, `communication/command_handlers/notebook_handler.py`, `notebook/notebook_data_manager.py`, `tests/behavior/test_notebook_handler_behavior.py`, `tests/unit/test_notebook_validation.py`, `tests/integration/test_notebook_validation_integration.py`, [NOTES_PLAN.md](development_docs/NOTES_PLAN.md)

### 2026-01-09 - Notebook Validation System Implementation and Testing **COMPLETED**
- **Feature**: Implemented comprehensive validation system for notebook feature with proper separation of concerns, error handling compliance, and extensive test coverage. Refactored validation architecture to use shared general validators while keeping notebook-specific validation separate.
- **Changes**:
  1. **Validation Architecture Refactoring**:
     - Created general validation helpers in `core/user_data_validation.py`: `is_valid_string_length()` and `is_valid_category_name()` for reusable validation across features
     - Refactored `notebook/notebook_validation.py` to use general validators for title, body, and group validation while keeping notebook-specific validation (entry references, short IDs, entry kinds, list indices) separate
     - All validation functions use `@handle_errors` decorator and return safe defaults (False/None) instead of raising exceptions
  2. **Enhanced Data Manager Validation**:
     - Added validation to `notebook_data_manager.py` functions: `append_to_entry_body()` validates text length and combined length, `set_entry_body()` validates body length, `add_list_item()` validates item text (non-empty), `search_entries()` validates query (non-empty)
     - All data manager functions now validate user_id presence and use entry reference validation
  3. **Error Handling Compliance**:
     - All validation functions follow MHM error handling guidelines: use `@handle_errors` decorator, return safe defaults, log errors appropriately, provide user-friendly error messages (< 200 chars, no technical details)
     - Error messages are concise, actionable, and user-friendly
  4. **Comprehensive Test Coverage**:
     - Created `tests/unit/test_notebook_validation_error_handling.py` (10 tests): error handling decorator usage, error logging verification, safe default return values, user-friendly error messages, error recovery scenarios, type safety validation, integration with error handling system
     - Created `tests/integration/test_notebook_validation_integration.py` (13 tests): validation integration with data manager, length validation in append/set operations, group validation, list item validation, error logging verification, data persistence prevention, Unicode content handling, boundary length testing, empty string vs None handling
     - Updated existing behavior tests to work with new validation
  5. **Handler Improvements**:
     - Fixed `_handle_create_note()` in `notebook_handler.py` to handle missing entities gracefully by prompting for title when both title and body are missing, preventing validation errors
- **Impact**: Validation system is now properly architected with separation of concerns (general vs notebook-specific), fully compliant with MHM error handling and testing guidelines, and comprehensively tested (105 total tests: 28 unit validation, 10 unit error handling, 13 integration, 54 behavior). All validation prevents invalid data from being persisted and provides user-friendly error messages. General validators can be reused by tasks and other features.
- **Files**: `core/user_data_validation.py` (modified), `notebook/notebook_validation.py` (refactored), `notebook/notebook_data_manager.py` (enhanced validation), `communication/command_handlers/notebook_handler.py` (improved missing entity handling), `tests/unit/test_notebook_validation_error_handling.py` (created), `tests/integration/test_notebook_validation_integration.py` (created)

### 2026-01-09 - Comprehensive Notebook Test Suite Creation **COMPLETED**
- **Feature**: Created complete automated test suite for notebook feature with 54 comprehensive tests covering all functionality, replacing manual Discord testing. Created entire test file `tests/behavior/test_notebook_handler_behavior.py` from scratch this session.
- **Changes**:
  1. **Core Handler Tests (29 tests)**: Created `TestNotebookHandlerBehavior` class with tests for handler intent handling, note creation (title only, title+body, with tags), list creation (title only, with items), entry viewing (recent, show, not found cases), entry editing (append, add tags, pin), list operations (add item, toggle done), organization views (pinned, search), flow states (note body flow, list items flow with !end), command parsing variations (bang commands, slash commands), and end-to-end command processing through InteractionManager.
  2. **Command Parsing Tests**: Created `TestNotebookCommandParsing` class with tests for command parser recognition of note/list/recent/show commands, entity extraction, command variations end-to-end, and flow completion through InteractionManager.
  3. **Entity Extraction Tests (9 tests)**: Created `TestNotebookEntityExtraction` class with tests for title/body extraction (colon and newline separators), tag extraction from commands, entry reference parsing (short IDs), list items extraction, limit extraction from recent commands, tag extraction from append commands, and graceful handling of missing/empty entities.
  4. **Flow State Edge Cases (7 tests)**: Created `TestNotebookFlowStateEdgeCases` class with tests for skip/cancel note flows, interrupting flows with different commands, empty responses in flows, multiple items in list flows (batch addition), empty list flows (ending without items), and flow timeout simulation (10-minute expiration logic).
  5. **Error Handling Tests (9 tests)**: Created `TestNotebookErrorHandling` class with tests for invalid entry references, append/tag operations on non-existent entries, toggle operations on non-existent lists, invalid item indices, missing user_id defensive handling, very long titles, special characters in titles/bodies, and malformed entry references.
  6. **Test Infrastructure**: 
     - Fixed pytest marker registration by adding `notebook` marker to `conftest.py`'s `pytest_configure` hook via `config.addinivalue_line()`, eliminating `PytestUnknownMarkWarning` warnings
     - Added `notebook` marker to `pytest.ini` markers section
     - Updated [TESTING_GUIDE.md](tests/TESTING_GUIDE.md) and [AI_TESTING_GUIDE.md](ai_development_docs/AI_TESTING_GUIDE.md) to include `notebook` marker in feature markers list
  7. **Test Fixes**: Fixed multiple test failures during development including list creation parameter types, Pydantic validation issues, flow completion assertions, and case-insensitive entity extraction assertions.
  6. **Documentation Updates**:
     - Updated [NOTES_PLAN.md](development_docs/NOTES_PLAN.md) testing status section with comprehensive breakdown of all 54 tests organized by category (Core Handler, Entity Extraction, Flow State Edge Cases, Error Handling)
     - Updated test suite status to show all priority testing areas as complete (Command Patterns, Flow State Management, Command Generalization, Data Operations, Edge Cases)
     - Marked "Comprehensive Test Suite" task as completed in Implementation Remaining section
  7. **Task Tracking**: Updated [TODO.md](TODO.md) to mark notebook feature test task as completed with reference to test file location.
- **Impact**: Comprehensive test coverage ensures notebook feature robustness, validates edge cases and error conditions, and provides automated validation replacing manual Discord testing. All priority testing areas from NOTES_PLAN.md are now covered. All 54 notebook tests passing, full test suite shows 4023 passed, 1 failed (unrelated checkin test: `test_delete_custom_question`), 1 skipped. Test suite validates command parsing, entity extraction, flow state management, error handling, and end-to-end command processing through InteractionManager.
- **Files**: `tests/behavior/test_notebook_handler_behavior.py` (created), `tests/conftest.py`, `pytest.ini`, [TESTING_GUIDE.md](tests/TESTING_GUIDE.md), [AI_TESTING_GUIDE.md](ai_development_docs/AI_TESTING_GUIDE.md), [NOTES_PLAN.md](development_docs/NOTES_PLAN.md), [TODO.md](TODO.md)

### 2026-01-09 - Command Handler Consolidation and Profile Formatting Fixes **COMPLETED**
- **Feature**: Consolidated duplicate command handler implementations across `interaction_handlers.py` (monolithic) and separate handler files, fixed profile display formatting to match test expectations, and improved test runner failure display reliability.
- **Changes**:
  1. **Base Class Consolidation**: Removed duplicate `InteractionHandler` base class from `interaction_handlers.py`, standardized all handlers to import from `base_handler.py`. Fixed `notebook_handler.py` import.
  2. **TaskManagementHandler Consolidation**: Merged implementations (added default recurrence pattern and repeat_after_completion support from `interaction_handlers.py` to `task_handler.py`), updated registry to use lazy import, updated all imports to use `task_handler.py`, removed duplicate class from `interaction_handlers.py`, added detection pattern to legacy cleanup tool.
  3. **Other Handler Consolidations**: Consolidated `CheckinHandler`, `ProfileHandler`, `ScheduleManagementHandler`, and `AnalyticsHandler` by removing duplicates from `interaction_handlers.py`, updating registry to lazy imports, and ensuring all imports use separate handler files.
  4. **Registry Refactoring**: Cleaned up `interaction_handlers.py` to only contain registry dictionary, lazy import logic, and `HelpHandler` (which has no separate file). All other handlers now use lazy imports from separate files.
  5. **Test Updates**: Updated test imports in `test_interaction_handlers_behavior.py` and `test_interaction_handlers_coverage_expansion.py` to import handlers from separate files instead of `interaction_handlers.py`.
  6. **Profile Formatting Fixes** (3 test failures resolved):
     - Replaced emoji formatting with bullet point format (`- Name:`, `- Gender Identity:`, etc.) in `_format_profile_text()` method
     - Updated all profile fields (Name, Gender Identity, Email, Status, Health Conditions, Medications, Allergies, Interests, Goals, Support Network, Notes for AI, Account Features) to use consistent bullet point formatting
     - Fixed fallback error handling to also use bullet points instead of emojis
     - Tests fixed: `test_profile_no_duplicate_formatting`, `test_profile_text_formatter_direct`, `test_profile_display_format`
  7. **Test Runner Failure Display Improvements**:
     - Enhanced `run_tests.py` to more reliably extract and display test failures from pytest output
     - Improved regex patterns for capturing failures across different pytest output formats (standard FAILED lines, FAILURES sections, parallel execution output)
     - Prioritized structured `failure_details` from JUnit XML for more reliable failure reporting
     - Added deduplication logic to prevent duplicate failure messages
     - Implemented truncation for long error messages and stack traces to improve console readability
     - Added fallback message when failure details cannot be extracted but failures are detected
- **Impact**: Eliminates code duplication, improves maintainability, establishes consistent handler organization pattern. Reduces `interaction_handlers.py` from ~2800 lines to ~160 lines (registry and HelpHandler only). All handlers now follow the same pattern: separate file, import from `base_handler.py`, lazy-loaded via registry. Profile display now uses consistent bullet point formatting matching test expectations. Test runner now consistently displays failure details, making debugging easier. All 3970 tests now pass (0 failed, 1 skipped). Command handler consolidation plan reviewed and confirmed complete.
- **Files**: `communication/command_handlers/interaction_handlers.py`, `communication/command_handlers/task_handler.py`, `communication/command_handlers/checkin_handler.py`, `communication/command_handlers/profile_handler.py`, `communication/command_handlers/schedule_handler.py`, `communication/command_handlers/analytics_handler.py`, `communication/command_handlers/notebook_handler.py`, `communication/command_handlers/base_handler.py`, `communication/message_processing/interaction_manager.py`, `tests/behavior/test_interaction_handlers_behavior.py`, `tests/behavior/test_interaction_handlers_coverage_expansion.py`, `run_tests.py`, `development_tools/config/development_tools_config.json`, `archive/command_handlers_consolidation_20260109_025944/` (backup)

### 2026-01-09 - Test Suite Fixes: Discord Bot, Command Parsing, and Task Completion **COMPLETED**
- **Feature**: Fixed 8 test failures across multiple test suites, improving test reliability and ensuring all tests pass
  1. **Discord Bot Test Fixes** (3 tests):
     - Updated test assertions in `tests/behavior/test_discord_bot_behavior.py` to match actual Discord API implementation
     - Changed assertions from positional arguments to keyword arguments (`content=message` instead of `message`)
     - Tests: `test_send_to_channel_sends_message`, `test_send_to_channel_sends_with_view`, `test_send_to_channel_sends_with_embed`
  2. **Checkin Expiry Test Fixes** (2 tests):
     - Added explicit handling for `/tasks` and `!tasks` commands in `conversation_flow_manager.py` to bypass parser issues
     - Commands now directly call `TaskManagementHandler` with `list_tasks` intent, ensuring proper delegation
     - Tests: `test_slash_command_expires_and_hands_off`, `test_bang_command_expires_and_hands_off`
  3. **Task Reminder Followup Test Fix** (1 test):
     - Added missing `import re` to `communication/command_handlers/task_handler.py`
     - Fixed `NameError` that was causing `_handle_create_task` to return error response instead of proper `InteractionResponse`
     - Test: `test_task_creation_starts_reminder_followup_flow`
  4. **Task Completion Test Fixes** (2-3 tests):
     - Fixed entity extraction in `command_parser.py` to strip "task " prefix from identifiers
     - "complete task 1" now correctly extracts "1" instead of "task 1", allowing proper numeric task lookup
     - Tests: `test_discord_task_create_update_complete`, `test_discord_response_after_task_reminder`
  5. **Command Parser Improvements**:
     - Added early pattern checking for "help" and "list_tasks" to ensure they take precedence
     - Added direct string equality check for "help" command before pattern matching
     - Improved pattern matching logic to use `.match()` for anchored patterns
     - Updated `list_tasks` patterns to be more explicit and added to high-confidence intents
     - Fixed entity extraction to handle "task " prefix in task identifiers
- **Impact**: All 3970 tests now pass (1 skipped). Test suite reliability improved, ensuring proper command parsing and task management functionality works correctly. Fixed critical issues with command delegation during checkin flows and task completion parsing.
- **Files**: `tests/behavior/test_discord_bot_behavior.py`, `communication/command_handlers/task_handler.py`, `communication/message_processing/command_parser.py`, `communication/message_processing/conversation_flow_manager.py`

### 2026-01-08 - Task Creation Flow Fixes, Note Creation Verification, and Documentation Updates **COMPLETED**
- **Feature**: Fixed task creation flow routing, improved date/time parsing, verified note creation flows, and updated documentation
  1. **Task Creation Flow Fixes**:
     - Fixed `TaskManagementHandler` in both `task_handler.py` and `interaction_handlers.py` to properly route to due date flow when no valid due date exists
     - Added explicit date validation (`datetime.strptime`) to ensure `due_date` is in `YYYY-MM-DD` format before proceeding
     - Improved date/time parsing to handle natural language expressions like "in X days", "next Tuesday", "Friday at noon", "in X hours"
     - Fixed reminder flow to only prompt when a valid due date is present (previously prompted even without due date)
     - Added `_parse_time_string()` method to both handlers for consistent time parsing (handles "noon", "midnight", "10am", "2pm", etc.)
  2. **Note Creation Verification**:
     - Verified note creation flow correctly prompts with button-style format ("What would you like to add as the body text? [Skip] [Cancel]") when only title provided
     - Verified Skip and Cancel buttons work correctly to exit note body flow
     - Updated `NOTES_PLAN.md` to mark note creation as "In Progress" with verified components documented
  3. **Documentation Updates**:
     - Updated `NOTES_PLAN.md` with recent fixes: note body flow prompt format, flow expiration (10 minutes), flow interference detection, task creation flow fixes
     - Updated `.cursor/plans/notebook_feature_implementation_ce88ed1a.plan.md` with same fixes and verification status
     - Added task to investigate and deduplicate duplicate `TaskManagementHandler` classes (found in both `task_handler.py` and `interaction_handlers.py`)
     - Corrected verification status: marked flow expiration and interference detection as "not yet verified" (implemented but not tested)
- **Impact**: Task creation now correctly prompts for due date when none is provided, and reminder prompts only appear when a valid due date exists. Improved natural language date/time parsing makes task creation more user-friendly. Note creation flows verified to work correctly with button-style prompts. Documentation accurately reflects current implementation status and testing needs.
- **Files**: `communication/command_handlers/task_handler.py`, `communication/command_handlers/interaction_handlers.py`, [NOTES_PLAN.md](development_docs/NOTES_PLAN.md), `.cursor/plans/notebook_feature_implementation_ce88ed1a.plan.md`

### 2026-01-14 - Notebook Feature Documentation: Status Updates and Testing Roadmap **COMPLETED**
- **Feature**: Updated notebook feature planning documents with current implementation status, recent fixes, testing requirements, and remaining work
  1. **NOTES_PLAN.md Updates**:
     - Added "Recent Fixes & Improvements" section documenting regex pattern fixes, multi-line input support, button handler implementation, slash command conversion fixes, and flow state clearing improvements
     - Updated "Command Implementation Status" with completed features, known issues, and command support matrix (bang/slash/natural text)
     - Added "Testing Status" section listing what needs testing (command patterns, flow states, multi-line input, button interactions, edge cases)
  2. **notebook_feature_implementation_ce88ed1a.plan.md Updates**:
     - Added "Recent Implementation Fixes" section documenting architectural fixes, multi-line support, Discord button interactions, and flow state management
     - Updated Step 1.6 status to show command parser integration is complete
     - Added "Current Status Summary" section with implementation completion status, testing requirements, and remaining work (edit sessions, skip integration, AI extraction)
     - Updated milestone statuses to reflect current completion state
- **Technical Details**:
  - Both documents now accurately reflect: what's been completed (including recent fixes), what needs testing, what's left to implement, and known issues/limitations
  - Documentation provides clear roadmap for testing and future development work
- **Background**: The notebook feature implementation (Milestones 1-3) is functionally complete, but documentation needed to be updated to reflect current status, recent architectural fixes, and provide clear testing roadmap
- **Impact**: Planning documents now serve as accurate reference for current implementation status and next steps. Clear testing requirements documented for comprehensive notebook feature validation. Future development work (edit sessions, skip integration, AI extraction) clearly identified.
- **Files**: [NOTES_PLAN.md](development_docs/NOTES_PLAN.md), `.cursor/plans/notebook_feature_implementation_ce88ed1a.plan.md`

### 2026-01-07 - Notebook Feature: Core Implementation Complete and Search Fix **COMPLETED**
- **Feature**: Completed core notebook feature implementation (Milestones 1-3) and fixed critical search functionality bug
  1. **Milestone 1 - Foundations + V0 Notes (COMPLETED)**:
     - Created shared tag system (`core/tags.py`) with normalization, validation, and lazy initialization
     - Refactored task tag system to use shared module
     - Created notebook module structure with Pydantic schemas (`Entry`, `ListItem`)
     - Implemented data handlers with lazy initialization (directories/files created on first use)
     - Implemented full CRUD operations in data manager (create, read, update, search)
     - Created command handler (`NotebookHandler`) with all V0 commands (`!n`, `!recent`, `!show`, `!append`, `!tag`, `!untag`, `!s`, `!pin`, `!archive`)
     - Registered handler and added command patterns to parser
     - Fixed issues: "Untitled" notes (use body as title), timestamp format standardization, AI enhancement override prevention
  2. **Milestone 2 - Lists (COMPLETED)**:
     - Implemented list operations (`add_list_item`, `toggle_list_item_done`, `remove_list_item`)
     - Added list commands (`!l new`, `!l add`, `!l show`, `!l done/undo`, `!l remove`)
  3. **Milestone 3 - Organization Views (COMPLETED)**:
     - Implemented group support (`set_group`, `list_by_group`)
     - Implemented smart views (`list_pinned`, `list_inbox`, `list_by_tag`)
     - Added view commands (`!group`, `!pinned`, `!inbox`, `!t <tag>`)
  4. **Search Functionality Fix**: Fixed `search_entries()` returning 0 results due to `dict.fromkeys()` attempting to use unhashable `Entry` objects. Changed deduplication logic to use entry IDs instead (set of IDs to track duplicates). This fixes `!s` and `search` commands that were not finding entries.
  5. **Test Plan**: Created comprehensive test plan breaking down notebook feature testing into 15 detailed subtasks covering data handlers, data manager (CRUD/search/lists/views), command handlers, tag system, and integration tests
- **Technical Details**:
  - `notebook/notebook_data_manager.py`: Changed `list(dict.fromkeys(matching_entries))` to use `set` of entry IDs for deduplication (Entry objects are Pydantic models and not hashable)
  - All search tests now pass: `search_entries('...', 'meeting')`, `search_entries('...', 'project')`, `search_entries('...', 'like')` all return expected results
  - Timestamp format standardized to `'%Y-%m-%d %H:%M:%S'` across all notebook operations
  - Tags registered in `user_data_handlers` as core data type with lazy initialization from `resources/default_tags.json`
- **Background**: This work implements the notebook feature (notes, lists, journal entries) that enables users to capture and organize information via Discord commands. The feature includes full CRUD operations, search, tagging, grouping, and smart views (pinned, inbox, tag-based).
- **Impact**: Users can now capture notes, create and manage lists, search entries, organize with tags and groups, and use smart views - all via Discord commands. Search commands (`!s`, `search`) now work correctly, finding entries by title, body, or list items. Comprehensive test plan provides clear roadmap for ensuring feature reliability.
- **Files**: `notebook/notebook_data_manager.py`, `notebook/notebook_data_handlers.py`, `notebook/schemas.py`, `core/tags.py`, `communication/command_handlers/notebook_handler.py`, `tasks/task_management.py`

### 2026-01-05 - Multiple Fixes: Message File Creation, Error Handling Analyzer, and Path Drift **COMPLETED**
- **Feature**: Fixed three issues identified during development tools audit and user message category opt-in:
  1. **Message File Creation**: User message files were not automatically created when opting into new automated message categories
  2. **Error Handling Analyzer**: False positive flagging nested functions as Phase 1 candidates (functions needing `@handle_errors` decorator replacement)
  3. **Documentation Path Drift**: Broken file path references in TODO.md causing path drift detection failures
- **Root Causes**:
  1. **Message Files**: 
     - Malformed JSON in `resources/default_messages/word_of_the_day.json` - contained nested `messages` array structure that prevented proper parsing
     - Missing safeguard in `update_user_preferences` - if category comparison logic failed, message files might not be created even when needed
  2. **Error Handling**: Nested functions cannot use decorators, but analyzer didn't exclude them from Phase 1 candidate detection
  3. **Path Drift**: Incomplete file path references in TODO.md (missing directory paths)
- **Technical Changes**:
  - **Message File Creation**:
    - Fixed `resources/default_messages/word_of_the_day.json`: Flattened nested `messages` array structure to match expected format (all messages at top level)
    - Enhanced `core/message_management.py`:
      - Updated `create_message_file_from_defaults()` to detect and flatten nested `messages` arrays programmatically
      - Added validation to ensure all messages have required fields (`message_id`, `days`, `time_periods`)
      - Improved error handling and logging for malformed default message structures
    - Enhanced `core/user_data_handlers.py`:
      - Added safeguard in `update_user_preferences()` to ensure `ensure_user_message_files()` is called for all `new_categories` even if `added_categories` set is empty due to comparison issues
      - Added logging for safeguard path to aid debugging
  - **Error Handling Analyzer**:
    - Updated `development_tools/error_handling/analyze_error_handling.py`:
      - Added `_is_nested_function()` method to detect nested functions by checking indentation (8+ spaces) and presence of containing function at lower indentation
      - Modified Phase 1 candidate detection logic to exclude nested functions (line 619)
      - Nested functions with try-except blocks are now marked as appropriate error handling pattern, not candidates for decorator replacement
  - **Path Drift**:
    - Updated [TODO.md](TODO.md):
      - Line 67: `test_checkin_management_dialog.py` -> `tests/unit/test_checkin_management_dialog.py`
      - Line 74: `checkin_management_dialog.py` -> `ui/dialogs/checkin_management_dialog.py`
- **Impact**: 
  - Users opting into new message categories (e.g., `word_of_the_day`) now automatically receive properly formatted message files in their messages subdirectory. The system is more robust against malformed default message files and handles edge cases in category comparison logic. Manual fix applied to affected user (`05187f39-64a0-4766-a152-59738af01e97`) to restore missing `word_of_the_day.json` file.
  - Eliminates false positives in error handling reports. The nested function `on_template_selected` in `checkin_settings_widget.py` (line 748) was incorrectly flagged; reports now correctly show 0 Phase 1 candidates. This improves report accuracy and prevents unnecessary refactoring recommendations.
  - Path drift analyzer now shows 0 issues for TODO.md. Improves documentation quality and prevents false positives in path drift reports.
- **Files**: 
  - `resources/default_messages/word_of_the_day.json` (flattened structure)
  - `core/message_management.py` (nested structure detection and flattening)
  - `core/user_data_handlers.py` (safeguard for message file creation)
  - `development_tools/error_handling/analyze_error_handling.py` (nested function detection)
  - `ui/widgets/checkin_settings_widget.py` (nested function with proper error handling)
  - [TODO.md](TODO.md) (fixed path references)
- **Testing**: All existing error handling analyzer tests pass (23/23); manual verification confirms nested function is no longer flagged; path drift verification shows 0 issues for TODO.md

### 2026-01-04 - Check-in Settings UI Improvements: Min/Max Validation and Question Management **PARTIAL**
- **Feature**: Fixed original issues with check-in questions not appearing in UI and custom questions not being manageable. Enhanced check-in settings widget with improved min/max question count validation, configurable "always" and "sometimes" question inclusion options, category-based question grouping, and dynamic min/max validation. **Original issues from session start are now resolved:**
  - [OK] New questions now appear in the UI list (implemented dynamic question display via `get_enabled_questions_for_ui()`)
  - [OK] Custom questions now appear in the list and are toggleable, editable, and deletable (implemented full CRUD UI)
  - [OK] Add custom question dialog improved with better formatting and template support (added template selection combo box)
  - [OK] Question templates are now available when creating custom questions (templates load from `question_templates.json` and populate dialog fields)
- **Technical Changes**:
  - Updated `checkin_settings_widget.py`:
    - Added separate "Always" and "Sometimes" checkboxes for each question (replacing single enable/disable checkbox)
    - Implemented category-based question grouping (Mood, Energy, Health, Activities) with QGroupBox widgets
    - Added `_validate_question_counts()` method with logic:
      - Minimum minimum: `max(always_count, 1)` (doesn't depend on sometimes questions)
      - Maximum maximum: `total_enabled - 1` if sometimes_count > 0 (for variety), otherwise `total_enabled`
      - Minimum maximum: `always_count + 1` if sometimes_count > 0, otherwise `always_count`
    - Added `_on_min_changed()` and `_on_max_changed()` handlers for dynamic adjustment
    - Implemented `skip_min_adjust` parameter in validation to allow min to match reduced max
    - Attempted fixes for UI blanking: hiding scroll area/container during rebuild, using `setUpdatesEnabled()`, `repaint()`, and `QApplication.processEvents()`
  - Updated `checkin_management_dialog.py`:
    - Added tabbed interface with "Check-in Questions" and "Check-in Frequency / Schedule" tabs
    - Updated validation logic to match widget validation
    - Added check to ensure at least one question is enabled if check-ins are active
  - Updated `question_templates.json`: Removed type hints from templates (now added dynamically by UI)
  - Updated `questions.json`: Reorganized categories to "Mood", "Energy", "Health", "Activities"
- **Impact**: Resolves original session issues: all new questions and custom questions now display correctly in the UI with full management capabilities. Improves user experience by allowing fine-grained control over question inclusion and providing better visual organization. **Additional enhancements added during session:**
  - Category-based grouping (Mood, Energy, Health, Activities)
  - "Always" and "Sometimes" question inclusion options
  - Min/max question count validation with dynamic constraints
  - Tabbed interface for better organization
- **Outstanding Issues** (from additional enhancements, not original request):
  - Maximum spinbox cannot be reduced below minimum (should dynamically adjust minimum to match)
  - Questions section blanks visually when adding/deleting custom questions (data is preserved correctly, only visual issue)
- **Outstanding Issues**: See TODO.md "Investigate Check-in Settings UI Issues" for detailed investigation tasks
- **Files Modified**: `ui/widgets/checkin_settings_widget.py`, `ui/dialogs/checkin_management_dialog.py`, `resources/default_checkin/question_templates.json`, `resources/default_checkin/questions.json`

### 2026-01-04 - Check-in Questions Enhancement: New Questions, Custom Questions, and Sleep Schedule **COMPLETED**
- **Feature**: Enhanced the check-in system with new predefined questions, replaced sleep_hours with sleep_schedule (time_pair type), implemented custom question system with templates, and updated analytics to handle all new question types.
- **Technical Changes**:
  - **New Predefined Questions**: Added four new questions to `questions.json` and corresponding responses to `responses.json`:
    - `hopelessness_level` (scale_1_5): "How hopeless are you feeling today on a scale of 1 to 5?"
    - `irritability_level` (scale_1_5): "How irritable are you feeling today on a scale of 1 to 5?"
    - `motivation_level` (scale_1_5): "How motivated do you feel to do tasks today on a scale of 1 to 5?"
    - `treatment_adherence` (yes_no): "Did you follow your treatment plan today?"
  - **Sleep Quality Update**: Modified `sleep_quality` question text to clarify it's about feeling "rested" rather than sleep quality: "How rested do you feel today on a scale of 1 to 5? (1=not rested at all, 5=very well rested)"
  - **Sleep Schedule Replacement**: Replaced `sleep_hours` (number type) with `sleep_schedule` (time_pair type) that asks for both sleep time and wake time. Implemented `_parse_time_pair_response()` and `_normalize_time()` methods in `checkin_dynamic_manager.py` to handle various time formats (12-hour, 24-hour, with/without AM/PM).
  - **Custom Question System**: Implemented full CRUD operations for custom questions:
    - `get_custom_questions()`, `save_custom_question()`, `delete_custom_question()` methods in `DynamicCheckinManager`
    - Custom questions stored in user preferences under `checkin_settings.custom_questions`
    - Custom questions merged with predefined questions in `get_all_questions()` and `get_question_definition()`
    - Updated `get_enabled_questions_for_ui()` to accept `user_id` parameter and include custom questions
  - **Question Templates**: Created `question_templates.json` with templates for common questions (CPAP use, medical device use, therapy session) that users can use as starting points for custom questions
  - **UI Updates**: 
    - Updated `checkin_settings_widget.py` to use `sleep_schedule` instead of `sleep_hours` in checkbox mappings
    - Enhanced `add_new_question()` method with full dialog for creating custom questions (question text, display name, type, category)
    - Updated `get_checkin_settings()` and `set_question_checkboxes()` to handle custom questions via `get_enabled_questions_for_ui(user_id)`
    - Updated `checkin_management_dialog.py` to preserve `custom_questions` when saving settings
  - **Conversation Flow**: Updated `conversation_flow_manager.py`:
    - Added new `CHECKIN_` constants for new questions (HOPELESSNESS, IRRITABILITY, MOTIVATION, TREATMENT, SLEEP_SCHEDULE)
    - Updated `QUESTION_STATES` mapping to include new questions and `sleep_schedule`, removed `sleep_hours`
    - Modified `_start_dynamic_checkin()` to include custom questions from user preferences when building `enabled_questions`
    - Updated `_get_question_text()` and `_validate_response()` to accept and pass `user_id` to `dynamic_checkin_manager`
  - **Analytics Updates**: Updated `checkin_analytics.py`:
    - Added `_calculate_sleep_duration()` helper to calculate sleep duration in hours from sleep_schedule time pairs
    - Modified `get_sleep_analysis()` to use `sleep_schedule` and calculate duration from it (removed all `sleep_hours` references)
    - Updated `get_habit_analysis()` to include `treatment_adherence`
    - Updated `get_quantitative_summaries()` to handle new scale questions and `sleep_schedule` (converts time pairs to hours for analytics)
    - Updated `_calculate_sleep_score()` to use `sleep_schedule` and the new duration calculation
  - **Testing**: Created comprehensive test suite `tests/behavior/test_checkin_questions_enhancement.py` with tests for:
    - New predefined questions (existence, validation, responses)
    - Sleep schedule time_pair validation and duration calculation
    - Custom question CRUD operations
    - Sleep quality question text update
    - Analytics with new questions and sleep_schedule
- **Impact**: Users can now track additional mental health metrics (hopelessness, irritability, motivation), treatment adherence, and more accurate sleep tracking via time pairs. The custom question system allows users to create personalized questions (e.g., CPAP use) with optional templates. Sleep quality question is clearer about measuring "rested" feeling. Analytics properly handle all new question types and calculate sleep duration from time pairs.
- **Files**: 
  - `resources/default_checkin/questions.json` (added new questions, updated sleep_quality, replaced sleep_hours with sleep_schedule)
  - `resources/default_checkin/responses.json` (added responses for new questions)
  - `resources/default_checkin/question_templates.json` (new file with templates)
  - `core/checkin_dynamic_manager.py` (time_pair validation, custom question CRUD, get_enabled_questions_for_ui with user_id)
  - `core/checkin_analytics.py` (sleep_schedule handling, new questions in analytics)
  - `communication/message_processing/conversation_flow_manager.py` (new question states, custom question inclusion, user_id passing)
  - `ui/widgets/checkin_settings_widget.py` (sleep_schedule checkbox, custom question dialog, user_id in get_enabled_questions_for_ui calls)
  - `ui/dialogs/checkin_management_dialog.py` (preserve custom_questions on save)
  - `ui/designs/checkin_settings_widget.ui` (removed sleep_hours checkbox, added sleep_schedule checkbox)
  - `tests/behavior/test_checkin_questions_enhancement.py` (new comprehensive test suite)

### 2026-01-04 - Code Quality Improvements: Error Handling, Documentation, and Cleanup **COMPLETED**
- **Feature**: Addressed multiple code quality issues identified in AI_PRIORITIES.md: stabilized documentation drift, added error handling to missing functions, removed unused imports, fixed ASCII compliance, and improved error handling analyzer logic.
- **Technical Changes**:
  - **Error Handling**: Added `@handle_errors` decorator to `signal_handler` in `run_tests.py` and `_on_save_clicked` in `channel_management_dialog.py`. Removed redundant try-except blocks from `get_selected_channel` and `set_selected_channel` (they already had decorators). Updated error handling analyzer to exclude `__init__` methods from Phase 1 recommendations since both decorator and try-except patterns are valid for constructors.
  - **Documentation**: Removed broken references to non-existent files (EXISTING_TOOLS_COMPARISON.md, COMPLEMENTARY_TOOLS_GUIDE.md) from TODO.md. Fixed broken file path reference in AI_TESTING_GUIDE.md (test_memory_profiler.py -> memory_profiler.py). Moved "Evaluate and Integrate Complementary Development Tools" task to AI_DEV_TOOLS_IMPROVEMENT_PLAN_V3.md (Section 2.9).
  - **Code Cleanup**: Removed unused `atexit` import from `run_tests.py` and unused `List` import from `generate_test_coverage_report.py`.
  - **ASCII Compliance**: Fixed multiplication symbol (x) in AI_TESTING_GUIDE.md. Enhanced ASCII fixer to handle additional common symbols: degree (deg), plus-minus (+/-), division (/), bullet (-), trademark (TM), registered (R), and copyright (C).
  - **Test Fixes**: Fixed `test_save_channel_settings_exception_handling` by properly binding real methods to mock instances so decorators execute correctly.
- **Impact**: Improved code quality, documentation accuracy, and test reliability. Error handling is now consistent across flagged functions, documentation paths are correct, and the ASCII fixer can automatically handle more common non-ASCII characters in future runs.
- **Files**: `ui/dialogs/channel_management_dialog.py`, `run_tests.py`, `development_tools/tests/generate_test_coverage_report.py`, `development_tools/docs/fix_documentation_ascii.py`, `development_tools/docs/analyze_ascii_compliance.py`, `development_tools/error_handling/analyze_error_handling.py`, `tests/ui/test_channel_management_dialog_coverage_expansion.py`, [TODO.md](TODO.md), [AI_TESTING_GUIDE.md](ai_development_docs/AI_TESTING_GUIDE.md), `development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V3.md`

### 2026-01-04 - Memory Leak Fix: Test Mocking and Parallel Execution Stability **COMPLETED**
- **Feature**: Fixed critical memory leak in parallel test execution that was causing worker crashes at 94% system memory. Root cause was `test_full_audit_status_reflects_final_results` running real tools instead of mocks, causing memory accumulation when multiple workers executed real audit tools simultaneously.
- **Technical Changes**:
  - **Root Cause**: Test was only mocking some tools, not all tools that `run_audit()` calls. Missing mocks included `run_analyze_package_exports`, `run_unused_imports`, `run_analyze_function_patterns`, `run_analyze_module_imports`, `run_analyze_dependency_patterns`, `run_generate_unused_imports_report`, and `run_script`. Real tools were loading large files from disk, causing memory spikes in parallel execution.
  - **Fix Applied**: Added mocks for all missing Tier 1 and Tier 2 tools in `test_full_audit_status_reflects_final_results`. Test now runs in 5.84s (was 25.65s) with 0.00s tool execution time.
  - **Additional Fixes**:
    - Fixed race condition in `temp_project_copy` fixture: Added retry logic with exponential backoff to handle files being deleted during `copytree` in parallel execution.
    - Fixed preferences test failure: Added cache clearing and explicit preferences reload to ensure preferences persist correctly after partial saves.
  - **Enhanced Logging**: Added detailed logging in `_reload_all_cache_data()` to track memory leak prevention, including project root paths, test directory detection, and file loading operations.
- **Impact**: Memory leak resolved - test suite now runs successfully with 3975 tests passing, no worker crashes, and memory staying below 90%. Test execution time improved from 25+ seconds to <6 seconds for the problematic test. All tests pass consistently in parallel execution.
- **Files**: 
  - `tests/development_tools/test_audit_status_updates.py` (added missing mocks)
  - `development_tools/shared/service/audit_orchestration.py` (enhanced logging)
  - `tests/development_tools/conftest.py` (fixed race condition in `temp_project_copy`)
  - `tests/ui/test_account_creation_ui.py` (fixed cache issue in preferences test)

------------------------------------------------------------------------------------------
## Archive Notes
To keep this file usable, older entries have been moved into archive files under `development_docs/changelog_history/` 

**Archive files:**
- `development_docs/changelog/CHANGELOG_DETAIL_2025_08.md`
- `development_docs/changelog/CHANGELOG_DETAIL_2025_09.md`
- `development_docs/changelog/CHANGELOG_DETAIL_2025_10.md`
- `development_docs/changelog/CHANGELOG_DETAIL_2025_11.md`
- `development_docs/changelog/CHANGELOG_DETAIL_2025_12.md`
