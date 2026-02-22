# AI Changelog - Brief Summary for AI Context
> **File**: `ai_development_docs/AI_CHANGELOG.md`
> **Audience**: AI collaborators (Cursor, Codex, etc.)
> **Purpose**: Lightweight summary of recent changes
> **Style**: Concise, essential-only, scannable
> **See [development_docs/CHANGELOG_DETAIL.md](development_docs/CHANGELOG_DETAIL.md) for the full history**

## Overview
This file is a lightweight summary of recent changes for AI collaborators. It provides essential context without overwhelming detail. For the complete historical record, see [CHANGELOG_DETAIL.md](development_docs/CHANGELOG_DETAIL.md).

## How to Update This File
1. Add a new entry at the top summarising the change in 2-4 bullets.
2. Keep the title short: "YYYY-MM-DD - Brief Title **COMPLETED**".
3. Reference affected areas only when essential for decision-making.
4. Move older entries to archive\AI_CHANGELOG_ARCHIVE.md to stay within 10-15 total.
Template:
```markdown
### YYYY-MM-DD - Brief Title **COMPLETED**
- Key accomplishment in one sentence
- Extra critical detail if needed
- User impact or follow-up note
```
Guidelines:
- Keep entries concise
- Focus on what was accomplished and why it matters
- Limit entries to 1 per chat session. Exceptions may be made for multiple unrelated changes
- Maintain chronological order (most recent first)
- REMOVE OLDER ENTRIES when adding new ones to keep context short
- Target 10-15 recent entries maximum for optimal AI context window usage

## Recent Changes (Most Recent First)

### 2026-02-22 - Flow deferral/cooldown hardening + Discord wiring tests **COMPLETED**
- Implemented scheduled-send flow protection end-to-end: active-flow and post-flow cooldown gating now defer scheduled sends, and scheduler performs a one-time +10 minute retry without recursive deferral.
- Added flow completion/cooldown tracking APIs in `conversation_flow_manager` and updated `channel_orchestrator` send-status handling (`sent`/`deferred`/`skipped`/`failed`), with scheduler branching on deferred behavior.
- Added focused coverage for the new behavior in `tests/unit/test_channel_orchestrator.py`, `tests/behavior/test_conversation_flow_manager_behavior.py`, and `tests/behavior/test_scheduler_coverage_expansion.py`.
- Added Discord behavior coverage for dynamic app command callback routing, `on_ready` app-command sync, and classic dynamic command mapping with explicit `help` skip in `tests/behavior/test_discord_bot_behavior.py`.
- Compliance re-check against `ai_development_docs/AI_TESTING_GUIDE.md` plus policy-guard run passed (`206 passed`), and user-reported full audit run raised no new issues with all tests passing.
- Completed live runtime validation on February 21, 2026: observed active-flow and cooldown deferral reasons, verified one-time +10 minute deferred retry execution (`allow_deferral=False`), confirmed outbound-triggered check-in flow expiry behavior, and confirmed restart/persistence behavior from logs.
- Resolved `MESSAGE_SELECTION_NO_MATCH` period-label mismatches for affected users by normalizing message library `time_periods` to include canonical schedule period names in:
  - `data/users/c59410b9-5872-41e5-ac30-2496b9dd8938/messages/motivational.json`
  - `data/users/05187f39-64a0-4766-a152-59738af01e97/messages/motivational.json`
  - `data/users/05187f39-64a0-4766-a152-59738af01e97/messages/word_of_the_day.json`
- Session closeout updates applied: completed TODO items removed from [TODO.md](TODO.md), follow-up validation/monitoring tracked in [PLANS.md](development_docs/PLANS.md), and full diff review (`git diff --stat` + `git diff --name-only`) completed before finalizing changelog entries.

### 2026-02-21 - Backup reliability hardening + JSON-only reporting **COMPLETED**
- Runtime backups are now directory-first with zip kept only as a temporary `# LEGACY COMPATIBILITY:` read-path bridge for historical artifacts.
- Weekly backup reliability was hardened: scheduler now checks weekly cadence from `weekly_backup_*` artifacts, and retention no longer lets frequent auto backups evict weekly backups.
- `analyze_backup_health` now validates weekly presence/recency explicitly and feeds `AI_STATUS.md`, `consolidated_report.md`, and `AI_PRIORITIES.md` (priority item appears automatically on backup-health failure).
- Backup tooling outputs are now JSON-only in `development_tools/reports/jsons`, and drill restore extraction folders are temporary/auto-cleaned after verification.
- `backup_zip_compat_bridge` legacy tracking remains registered; removal plan is unchanged (remove bridge after no zip backups remain for one full 30-day Category-A retention window).

### 2026-02-20 - Coverage expansion batch + stability fixes **COMPLETED**
- Main session outcome: expanded automated test coverage across priority domains (`communication`, `ui`, `core`) with additional scenario/branch-focused tests and refreshed coverage/report outputs.
- As part of keeping the coverage run green, resolved two active Tier 3 failures:
  - `tests/behavior/test_account_handler_behavior.py::TestAccountHandlerBehavior::test_username_exists_checks_existing_username`
  - `tests/ui/test_account_creation_ui.py::TestAccountCreationErrorHandling::test_invalid_data_handling_real_behavior`
- Hardened username lookup behavior in `communication/command_handlers/account_handler.py` to skip per-user read errors during scans, and stabilized related behavior tests with unique identifiers + explicit setup assertions.
- Updated the failing UI persistence assertion path in `tests/ui/test_account_creation_ui.py` to use runtime path resolution with bounded retry and non-auto-create verification, removing a parallel timing/path assumption.
- Coverage-focused updates reflected in current diff include `tests/unit/test_channel_orchestrator.py`, `tests/ui/test_ui_app_qt_core.py`, and `tests/behavior/test_service_utilities_behavior.py`, plus refreshed `AI_STATUS/AI_PRIORITIES/consolidated_report` and report JSONs.
- Validation: targeted reruns passed; user-confirmed full `audit --full` now has all tests passing.
- Full-diff review (`git diff --stat` + `git diff --name-only`) completed before wrap-up; per user, all diff files were actioned this session.

### 2026-02-20 - Tier 3/logging follow-up and full-diff session wrap **COMPLETED**
- Completed a focused follow-up pass on audit/logging behavior: `quick_status` now runs only during explicit quick audits, and tool completion labels are standardized to `PASS`/`FAIL` with `issues=<n>` detail.
- Finalized Tier 3/report/logging integration updates across service orchestration/wrappers/commands/reporting and coverage runner paths (`audit_orchestration.py`, `commands.py`, `report_generation.py`, `tool_wrappers.py`, `run_test_coverage.py`), with refreshed status/priorities/consolidated outputs.
- Updated dev-tools tests and reliability coverage in current session tree (including `test_generate_function_registry.py`, `test_regenerate_coverage_metrics.py`, `test_report_generation_quick_wins.py`, `test_audit_strict_mode.py`, plus targeted test stabilization updates).
- Adjusted `tests/development_tools/test_changelog_trim_tooling.py` to match current INFO/DEBUG policy.
- Validation: targeted dev-tools pytest checks passed; user-confirmed `audit --full --clear-cache` passes.
- Full `git diff --stat` + `git diff --name-only` review completed; current tree treated as session-scoped and reflected by this entry.

### 2026-02-19 - Tier-3 test-failure fixes + testing-guide policy clarifications **COMPLETED**
- Added an explicit temporary legacy-compatibility bridge for Tier 3 `coverage_outcome` v1 fields (`state`, counts, `return_code`, `failed_node_ids`) with marker/commenting, usage logging when state-only payloads are encountered, and specific legacy-pattern registration for cleanup tracking; removal plan is to delete this bridge after downstream consumers stop reading v1-only fields.
- Fixed Tier-3 failures by removing nondeterministic and collision-prone test patterns in:
  - `tests/unit/test_user_management.py`
  - `tests/ui/test_category_management_dialog.py`
  - `tests/unit/test_config.py`
  - `tests/behavior/test_account_handler_behavior.py`
  - `tests/behavior/test_checkin_handler_behavior.py`
- Corrected account-handler test setup misuse where `TestUserFactory.create_basic_user(...)` bool return values were used as user IDs; tests now resolve UUIDs explicitly.
- Updated paired testing docs [AI_TESTING_GUIDE.md](ai_development_docs/AI_TESTING_GUIDE.md) and [TESTING_GUIDE.md](tests/TESTING_GUIDE.md) with explicit rules for factory return semantics, UUID resolution, unique per-test IDs for parallel safety, and policy guard tests (`tests/unit/test_test_policy_guards.py`).
- Updated planning/status artifacts and reports in this same session: [TODO.md](TODO.md), [PLANS.md](development_docs/PLANS.md), `development_tools/AI_PRIORITIES.md`, `development_tools/AI_STATUS.md`, `development_tools/consolidated_report.md`, and refreshed generated reports under `development_docs/*REPORT.md` plus `development_tools/reports/*.json`.
- Additional test files updated this session and reflected in diff: `tests/conftest.py`, `tests/core/test_file_auditor.py`, `tests/debug_file_paths.py`, `tests/development_tools/test_analyze_functions.py`, and `tests/test_error_handling_improvements.py`; new untracked tests created: `tests/development_tools/test_analyze_test_markers.py`, `tests/development_tools/test_fix_test_markers.py`, `tests/development_tools/test_tool_guide.py`, `tests/unit/test_test_policy_guards.py`.
- Validation: targeted previously failing nodes and focused account-handler/checkin-handler subsets passed.

### 2026-02-19 - Coverage hardening + audit failure cleanup **Progressed**
- Picked and progressed `AI_PRIORITIES.md` item "Raise development tools coverage" by targeting the listed 0%-coverage modules: `development_tools/shared/export_code_snapshot.py`, `development_tools/shared/export_docs_snapshot.py`, and `development_tools/shared/service/data_freshness_audit.py`.
- Added focused regression/unit tests in `tests/development_tools/test_export_snapshots.py` and `tests/development_tools/test_data_freshness_audit.py` to exercise exclusion toggles, file discovery/bundling, report scanning, static freshness checks, and summary aggregation.
- Fixed a real bug discovered during test authoring: `check_cache_file_for_deleted_files()` in `data_freshness_audit.py` defined recursive scanning but never executed it; now calls `find_file_paths(data)` so deleted-file references are actually detected.
- Validation: `python -m pytest tests/development_tools/test_export_snapshots.py tests/development_tools/test_data_freshness_audit.py -q` -> `11 passed`.
- Hardened coverage orchestration cache-precheck behavior in `development_tools/shared/service/commands.py` so failed cached outcomes (`test_failures`/`failed`/`crashed`/`coverage_failed`) are not reused as `cache_only`; added regression tests in `tests/development_tools/test_audit_strict_mode.py`.
- Updated test-file coverage cache policy to persist cache artifacts whenever coverage data is collected (even on failing runs) and rely on failed-domain/run-domain invalidation on next run (`development_tools/tests/run_test_coverage.py`, `development_tools/tests/test_file_coverage_cache.py`).
- Reverted temporary full-run timeout floor so coverage pytest timeout remains config/default driven (12 minutes unless configured otherwise).
- Fixed/closed recent audit failures: removed `tests/development_tools/test_intentional_failure.py`; stabilized behavior tests with per-test unique user IDs in `tests/behavior/test_message_behavior.py` and `tests/behavior/test_checkin_handler_behavior.py`; revalidated `tests/behavior/test_discord_checkin_retry_behavior.py` targeted failure path as stable in reruns.
### 2026-02-18 - Legacy cleanup + coverage cache/reporting hardening **Progressed**
- Removed the final legacy-marker footprint from active files and reran `python development_tools/run_development_tools.py legacy`; `LEGACY_REFERENCE_REPORT.md` now reports `Total Files with Issues: 0` and `Legacy Compatibility Markers Detected: 0`.
- Standardized dev-tools coverage outcome handling to read `details.dev_tools_test_outcome` first in `development_tools/shared/service/commands.py`, while still tolerating older payloads when encountered.
- Stopped emitting the deprecated top-level `dev_tools_test_outcome` key in `development_tools/tests/run_test_coverage.py` output payloads; standardized `summary/details` output remains intact.
- Updated compatibility wording in comments (`development_tools/shared/service/data_loading.py`, `development_tools/shared/mtime_cache.py`, `development_tools/shared/service/audit_orchestration.py`, `run_tests.py`, `user/user_context.py`) to remove legacy/backward-compatibility markers while preserving behavior.
- Updated regression fixture shape in `tests/development_tools/test_audit_strict_mode.py` and validated with targeted tests (`21 passed` across strict-mode and report-generation quick-win suites).
- Hardened `run_test_coverage.py` cache behavior so reusable coverage cache state is not written when coverage collection fails (`coverage_failed` path); applies to serial/deferred-parallel test-file cache writes and dev-tools coverage cache updates.
- Updated Tier 3 priority rendering in `report_generation.py` to show per-track failed tests inline (`Parallel tests failed=N: ...`, `No-parallel tests failed=N: ...`) and derive displayed counts from deduplicated per-track failed node IDs.
- Normalized displayed pytest node IDs to compact `path::test_name` form and retained concrete applicable `development_tools/tests/logs/pytest_*_stdout_*.log` references in priority details.
- Updated regression expectations in `tests/development_tools/test_report_generation_quick_wins.py`; validated with targeted pytest runs for cache and reporting paths (all passing).

### 2026-02-18 - Priorities regression fix + safe changelog trim pathing **COMPLETED**
- Fixed `AI_PRIORITIES.md` omission of failed Tier 3 tests: the failure priority is now added before ranked rendering, so failed node IDs from `analyze_test_coverage` reliably appear in Immediate Focus.
- Standardized priority output shape in `report_generation.py`: removed redundant top blurbs, corrected AI_STATUS role wording, normalized `Review for guidance`, and enforced guidance/details bullets across priority types.
- Replaced unavailable changelog trim dependency in `audit_orchestration.py` with `development_tools/docs/fix_version_sync.py` APIs and improved warning/info logging for check/trim result handling.
- Moved changelog archive target to `archive/AI_CHANGELOG_ARCHIVE.md` and validated prepend behavior so newly trimmed entries are added at the top of archive history.
- Added/updated regression tests: `test_report_generation_quick_wins.py`, `test_changelog_trim_tooling.py`, and `test_fix_version_sync_changelog_archive_order.py`; refreshed generated status/priority/consolidated outputs after fixes.

### 2026-02-17 - New session closeout entry and follow-up confirmation **COMPLETED**
- Added a distinct same-day entry for this session (separate from the earlier 2026-02-17 work) per session-level changelog policy.
- Confirmed planning sync: completed command-map/recursion tasks removed from [TODO.md](TODO.md).
- Full audit run and no regressions found

### 2026-02-17 - Pyright/dev-tools cleanup + interaction/flow parity hardening **Largely Complete**
- Pyright in development_tools: 0 errors, 2 warnings. Fixed real issues (SCRIPT_REGISTRY, domain_mapper guard, Optional[Set[str]], report_generation optional access, changelog_manager getattr, measure_tool_timings method name). Suppressed mixin attribute-access warnings via `# pyright: reportAttributeAccessIssue=false` in the six service mixin files.
- Added AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md section 3.16 to explore refactoring report_generation.py and run_test_coverage.py (map structure, refactor plan, effort estimate).
- Interaction manager updates completed: canonical slash-command map getter/property alignment, bang-command convert+continue parity (no recursive re-entry), unknown-bang fallback fix, and decorator-based error handling for `slash_command_map` property.
- Added focused behavior tests for interaction/flow parity and edge cases in `tests/behavior/test_communication_interaction_manager_behavior.py`, plus conversation-flow manager coverage additions in `tests/behavior/test_conversation_flow_manager_behavior.py`.
- Session planning cleanup applied: completed command-map/recursion tasks removed from [TODO.md](TODO.md) and 2026-02-17 follow-up notes added to [PLANS.md](development_docs/PLANS.md).
- Ran doc tooling (`doc-fix --fix-ascii`, `doc-fix --convert-links`, `doc-sync`) via `.venv`, refreshing generated status/priority/report artifacts and related generated docs.
- Validation highlights: combined behavior run `87 passed`; targeted flaky UI rerun for the two Tier-3 node IDs `2 passed`.
- Full-tree diff was reviewed; unrelated/pre-existing edits currently in tree (not actioned this session) include `.github/workflows/logging-enforcement.yml` and [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md).

### 2026-02-16 - Static logging check migration + docs/plans refresh **COMPLETED**
- Relocated static logging enforcement script usage to `development_tools/static_checks/check_channel_loggers.py` and updated all active references (`.github/workflows/logging-enforcement.yml`, `run_tests.py`, `tests/behavior/test_static_logging_check.py`, [LOGGING_GUIDE.md](logs/LOGGING_GUIDE.md)).
- Updated planning/ownership docs for script migration and backup confidence work: [TODO.md](TODO.md), [PLANS.md](development_docs/PLANS.md), and [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md); removed stale retired-script mention from [AI_TESTING_GUIDE.md](ai_development_docs/AI_TESTING_GUIDE.md).
- Explicitly captured that `scripts/` is intentionally untracked (temporary/one-off workspace), so script-related work this session was recorded through tracked docs/plans and reference updates rather than relying on script-file git diffs.
- Applied doc drift fixes raised in-session ([TODO.md](TODO.md) path/update cleanup and [SCRIPTS_GUIDE.md](scripts/SCRIPTS_GUIDE.md) unconverted link conversion).
- Refreshed generated audit/report outputs in current diff: `development_tools/AI_STATUS.md`, `development_tools/AI_PRIORITIES.md`, `development_tools/consolidated_report.md`, `development_tools/reports/analysis_detailed_results.json`, `development_tools/reports/tool_timings.json`, plus updated generated docs (`development_docs/TEST_COVERAGE_REPORT.md`, `development_docs/UNUSED_IMPORTS_REPORT.md`, `development_docs/LEGACY_REFERENCE_REPORT.md`).
- Full tree diff was reviewed (`git diff --stat`, `git diff --name-only`) and this entry now reflects the entire current-session diff.
- `doc-fix/doc-sync` automation was attempted but blocked by missing `python-dotenv` in this environment; targeted doc edits were applied manually.

### 2026-02-16 - Test runner diagnostics/output pass **COMPLETED**
- `run_tests.py` was enhanced with bounded default post-failure reruns, per-failure artifacts, cleaner startup/phase output, and process-priority + LM Studio pause/resume controls.
- Failure-output semantics were cleaned up (non-zero-only classification display, less recap noise for routine `exit code 1`, clearer split-run deselection semantics).
- Failure rerun artifact clutter was reduced to a single run folder (`tests/logs/failure_reruns/<run_id>/`) with phase-prefixed logs; unused rerun summary JSON generation was removed.
- Removed temporary intentional demo failures from `tests/unit/test_user_management.py` and added explicit intermittent-failure tracking for `test_checkin_handler_start_checkin_conversation_manager_error` and `test_validate_core_paths_missing_directory` in [PLANS.md](development_docs/PLANS.md); completed runner/output tasks were pruned from [TODO.md](TODO.md).

### 2026-02-15 - Dev-tools report/cache consistency pass **COMPLETED**
- Tier 3 outcomes are now consistently represented with all three tracks (parallel, no-parallel, development-tools), and AI_PRIORITIES only includes Tier 3 test/coverage items when failures/errors are actionable (clean outcomes remain status-only).
- Standardized away remaining `consolidated_report.txt` references to `development_tools/consolidated_report.md` (non-historical paths) and aligned generated report links/messages.
- Tightened cache semantics: `audit --clear-cache` now clears dev-tools cache artifacts only, while cleanup variants (`cleanup --cache`, `--full`, `--all`, and default cleanup) cover broader cache/temp artifact scopes dynamically from canonical tool metadata.
- ASCII analysis/report consumption now uses standardized `summary/details` paths without legacy flat fallback dependency; stale payload handling was hardened via freshness checks.
- Unified "Function Docstring Coverage" reporting to one explicit source (`analyze_functions`, code-docstrings) to eliminate cross-report mismatches; registry docstring signals remain labeled separately as registry-index metrics.
- Updated session planning docs and roadmap tracking ([TODO.md](TODO.md), [PLANS.md](development_docs/PLANS.md), [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md)); user-validated full `audit --full --clear-cache` runs succeeded in-session.

### 2026-02-14 - Pytest cache isolation + flake follow-up **COMPLETED**
- Added strict cleanup/hard-fail behavior for stale root `pytest-cache-files-*` temp dirs and clearer cleanup diagnostics in test/coverage paths (`tests/conftest.py`, `development_tools/tests/run_test_coverage.py`).
- Disabled pytest cacheprovider for normal runs too (`pytest.ini`, `tests/conftest.py`) and kept it disabled in coverage subprocesses to enforce zero root cache-temp dirs.
- Coverage runs now log pytest errors (not only failures) and treat errors as cache-write blockers (`development_tools/tests/run_test_coverage.py`).
- Stabilized recent intermittent tests (`test_interaction_manager_single_response`, `test_multiple_users_same_features_real_behavior`), plus robustness fixes in `core/logger.py` and `user/__init__.py`.
- Updated `run_tests.py` scope:
  - default `--mode all` now includes `tests/core/`, `tests/communication/`, and `tests/notebook/`.
  - new `--full` flag runs full `tests/` tree (including `tests/development_tools/`).
- Updated testing docs ([TESTING_GUIDE.md](tests/TESTING_GUIDE.md), [AI_TESTING_GUIDE.md](ai_development_docs/AI_TESTING_GUIDE.md), [DEVELOPMENT_TOOLS_TESTING_GUIDE.md](tests/DEVELOPMENT_TOOLS_TESTING_GUIDE.md), [SYSTEM_AI_FUNCTIONALITY_TESTING_GUIDE.md](tests/ai/SYSTEM_AI_FUNCTIONALITY_TESTING_GUIDE.md)) and fixed an AI guide path typo.
- Closed related planning/tasks ([TODO.md](TODO.md), [PLANS.md](development_docs/PLANS.md)) and documented fixture-status regeneration handling ([DEVELOPMENT_TOOLS_TESTING_GUIDE.md](tests/DEVELOPMENT_TOOLS_TESTING_GUIDE.md), `tests/development_tools/conftest.py`).
- Final validation: user full run passed (`python run_tests.py` -> `3737 passed, 0 failed`).
- Additional validation: `python run_tests.py --full` -> `4556 passed, 0 failed, 1 skipped`.

### 2026-02-14 - Logging guard + coverage/cache stabilization **COMPLETED**
- Added CI logging-enforcement workflow (`.github/workflows/logging-enforcement.yml`) to run `check_channel_loggers.py` as a gate before downstream test steps; documented behavior in [LOGGING_GUIDE.md](logs/LOGGING_GUIDE.md) and removed the completed TODO task.
- Tuned legacy scan/report filtering so `run_tests.py` remains included for legacy findings while `tests/data/*` remains excluded from analyzer/report noise.
- Hardened development-tools coverage merge/report flow (`run_test_coverage.py`, `generate_test_coverage_report.py`) with expected-shard detection, wait/retry combine logic, and missing-shard validation warnings.
- Completed test-file coverage cache hardening (`test_file_coverage_cache.py`, `domain_mapper.py`, `run_test_coverage.py`): cross-domain dependency invalidation, test-file mtime/domain invalidation, explicit tool-change invalidation reasons, and skip-cache-on-failure/partial-run safeguards.
- Added focused regression tests in `tests/development_tools/test_test_file_coverage_cache.py` (tool hash/mtime persistence, all-domain invalidation on hash mismatch, dependency expansion) and enforced scratch test data under `tests/data/tmp` with explicit cleanup.
- Standardized coverage scope/artifact reporting in generated outputs (`AI_STATUS.md`, `AI_PRIORITIES.md`, `consolidated_report.txt`, `TEST_COVERAGE_REPORT.md`) and aligned artifact exclusions/ignore rules for `development_tools/tests/.coverage*` and `development_tools/tests/coverage_html/`.

### 2026-02-13 - Pyright type fixes (fixes over ignores) **Progressed**
- **tests/conftest.py**: Removed file-level pyright ignore. Fixed: (1) `setup_test_logging()` return type and assert so `test_logger`/`test_log_file` are always `Logger`/`Path`; (2) `QMessageBox.about` mock return type to `None` to match real API; (3) wrong import `AIChatbot` -> `AIChatBotSingleton`; (4) `periodic_memory_cleanup` uses module-level `_periodic_cleanup_test_count` instead of attaching to fixture function; (5) `CommunicationManager` cleanup uses local `cm_instance` so closure and later code see non-optional type.
- **tests/development_tools/conftest.py**: Removed file-level pyright ignore. Fixed: all `importlib.util.spec_from_file_location` / `module_from_spec` / `loader.exec_module` usages now guard on `spec is not None and spec.loader is not None` (or raise for final load); dynamic module attributes set via `setattr(module, "config", ...)` for loader-injected config.
- **tests/test_utilities.py** (from earlier): Optional params typed as `str | None` etc.; early `if not test_data_dir` guards in `*__with_test_dir`; added `create_minimal_user__impl_and_get_id`.
- **Audit test fixes**: Marked `test_get_user_data_account_with_discord_id` and `test_checkin_handler_start_checkin_with_old_checkin` with `@pytest.mark.no_parallel` so they run in serial during audit/coverage and avoid shared-state interference. Added `@handle_errors` to `_parse_time_period` in `communication/message_processing/command_parser.py` (AI_PRIORITIES).
- **Pyright in tests**: Reduced pyright warnings in `tests/` via typing (`str | None` for `test_data_dir` params), guards/asserts for optional members, `getattr`/`cast(Any)` for mocks, unused-expression fixes, and targeted ignores for intentional invalid-argument tests. Remaining warnings are mainly in `ui/` (dialogs/widgets).

## Archive Notes
Older detailed entries live in `development_docs/changelog_history/` and remain the historical source of truth. Use [CHANGELOG_DETAIL.md](development_docs/CHANGELOG_DETAIL.md) for the latest detailed entries and the archive folder for month-split history.
