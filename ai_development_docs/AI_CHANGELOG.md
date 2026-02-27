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

### 2026-02-27 - Static-analysis pipeline hardening + report clarity improvements **COMPLETED**
- Fixed Ruff/Pyright audit-runtime drift by normalizing configured `python -m ...` launchers to the active interpreter, eliminating false "tool unavailable" states in static-check wrappers.
- Added portable Ruff config sync scaffolding via `development_tools/config/sync_ruff_toml.py`; generated root `.ruff.toml` from shared exclusions; removed Ruff settings from `pyproject.toml` to avoid split ownership.
- Improved static-analysis reporting:
  - Ruff top rules now include readable rule names (code + name + count).
  - Pyright now reports separate top files for errors vs warnings, with conditional lines so zero-count severities are omitted.
  - Static-analysis unavailable messaging in AI reports was tightened to show explicit reasons when tools are missing.
- Updated dev-tools roadmap planning with portability and structure follow-ups in `AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md` (`7.6` static tooling/packaging portability, `7.7` directory taxonomy + config boundary cleanup) and synced `PLANS.md` pointer.
- Validation in-session:
  - targeted static-analysis/reporting tests passed (`test_static_analysis_tools.py`, `test_report_generation_static_analysis.py`, `test_tool_wrappers_static_analysis.py`).
  - full audit completed with no new non-static-analysis issues; regenerated `AI_STATUS.md`, `AI_PRIORITIES.md`, and `consolidated_report.md` reflect updated static findings.

### 2026-02-26 - Dev-tools coverage + AI work CLI follow-up **Progressed**
- Continued `AI_PRIORITIES` item `#2` with targeted low-risk test expansions across dev-tools modules, plus `analyze_ai_work.py` non-JSON CLI logging migration (`print` -> `logger.info`) with regression coverage.
- Validation progressed across batches from targeted suites (`7 passed`, `9 passed`, `103 passed`) to the consolidated suite (`141 passed`).
- Dev-tools-only coverage progressed `56.6%` (`14164/25008`) -> `58.6%` (`14667/25008`) -> `59.6%` (`14916/25008`, report rounds to `60%`).
- Hardened docs/audit lock behavior: `run_docs` now fails fast when audit/coverage locks exist, and `run_development_tools.py` now cleans audit/coverage lock files on interrupted `audit`/`full-audit` (`KeyboardInterrupt`) to reduce stale-lock blockers.
- Final user-run verification: `audit --full --clear-cache` completed with no new issues.
- Updated roadmap tracking in [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md) section `1.1`; full detailed breakdown is recorded in [CHANGELOG_DETAIL.md](development_docs/CHANGELOG_DETAIL.md).

### 2026-02-26 - Sleep check-in multi-period parsing + schedule-style time formats **COMPLETED**
- Sleep check-in answers now support interrupted sleep in up to 3 chunks with flexible connectors (`and`, `to`, `-`, ` - `) plus `from`/`between` phrasing.
- Time parsing for sleep schedule now accepts schedule-style variants (`9pm`, `930pm`, `21:30`, hour-only values, `noon`, `midnight`) and chunk separators via commas, semicolons, or new lines.
- Analytics now consume chunk payloads (`sleep_chunks`/`total_sleep_hours`) so interrupted sleep totals are calculated correctly and check-in history formatting shows chunk ranges + totals.
- Updated question text/examples in `resources/default_checkin/questions.json`; behavior validation passed: `pytest tests/behavior/test_checkin_questions_enhancement.py tests/behavior/test_dynamic_checkin_behavior.py -q` (`27 passed`).
- Per user instruction, generated/audit artifact files in working-tree diff were excluded from this session's changelog attribution.

### 2026-02-26 - Dev-tools exclusions consistency + CLI logging cleanup **Progressed**
- Applied shared exclusion filtering (`standard_exclusions.should_exclude_file`) to additional non-orchestration scanners/tests paths: function docstrings, domain mapper, test marker analyzer, channel logger checker, version-sync discovery, and dev-tools coverage cache/source mtime discovery paths.
- Converted remaining standalone analyzer summary prints to structured logging in `analyze_dependency_patterns.py`, `analyze_module_imports.py`, and non-JSON mode of `generate_unused_imports_report.py` (kept JSON stdout behavior).
- Logging enforcement follow-up: hardened `development_tools/static_checks/check_channel_loggers.py` standalone CI execution with resilient exclusions loading + fallback path so `python development_tools/static_checks/check_channel_loggers.py` works in minimal environments without optional runtime deps.
- Added/updated regression coverage in `test_analyze_module_imports_cli.py`, `test_check_channel_loggers.py`, `test_fix_version_sync_file_discovery.py`, and related existing dev-tools test modules.
- Updated V4 roadmap tracking ([AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md) sections `2.2`/`3.11`), re-ran full diff review (`git diff --stat`, `git diff --name-only`, `git status --short`), and user confirmed no new issues during `audit --full --clear-cache` follow-up.

### 2026-02-25 - Tier 3 failure fix + dev-tools coverage uplift **Progressed**
- Fixed Tier 3 recurrent failure `tests/unit/test_user_management.py::TestUserManagement::test_create_user_files_success` by switching to factory-returned UUID (`create_minimal_user_and_get_id`) instead of a separate post-create index lookup.
- Added focused low-coverage dev-tools tests: `test_service_utilities.py`, `test_tool_wrappers_additional.py`, `test_analyze_system_signals_additional.py`, plus strengthened `test_fix_documentation.py` and new `test_backup_inventory.py`.
- Validated targeted suites (`20 passed`) and repeated parallel checks for the previously failing user-management test; no new issues were identified during full audit follow-up.
- Dev-tools coverage follow-up (`run_test_coverage.py --dev-tools-only --no-parallel`) improved overall from `54.5%` to `55.7%`, with target module improvements: `tool_wrappers.py 38%`, `utilities.py 69%`, `analyze_system_signals.py 53%`.

### 2026-02-25 - Weekly backup semantics restored + backup guides synced **COMPLETED**
- Restored weekly-first backup behavior in runtime: scheduler now checks `weekly_backup_*` recency for weekly creation decisions, and cleanup retention now preserves weekly artifacts in a dedicated keep window (`WEEKLY_BACKUP_MAX_KEEP`, default 4) separate from non-weekly (`max_backups=10`).
- Restored explicit weekly backup health checks in dev-tools (`weekly_backup_present`, `weekly_backup_recent_enough`) and weekly-focused backup-health reporting labels in AI status/consolidated reporting.
- Synced paired backup docs to implementation semantics: [BACKUP_GUIDE.md](development_docs/BACKUP_GUIDE.md) and [AI_BACKUP_GUIDE.md](ai_development_docs/AI_BACKUP_GUIDE.md).
- Added/updated coverage for retention behavior (`tests/unit/test_auto_cleanup_backup_retention.py`) and related dev-tools low-coverage tests (`test_cli_interface.py`, `test_analyze_module_refactor_candidates.py`, plus expanded `test_generate_function_registry.py` branches).
- Regenerated in-session audit/report artifacts and derived docs (`AI_STATUS.md`, `AI_PRIORITIES.md`, `consolidated_report.md`, `analysis_detailed_results.json`, `tool_timings.json`, `TEST_COVERAGE_REPORT.md`, `UNUSED_IMPORTS_REPORT.md`, `LEGACY_REFERENCE_REPORT.md`) and updated planning/changelog trackers ([TODO.md](TODO.md), `PLANS.md`, `AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md`, both changelog tracks).
- Full working tree was reviewed (`git diff --stat`, `git diff --name-only`, `git status --short`) and, per user confirmation, all working-tree changes were actioned in this session; user confirmed full audit pass with no new issues.

### 2026-02-25 - Conftest refactor and AI priorities follow-up **COMPLETED**
- Conftest plan Phase 1.1: Extracted test helpers to `tests/support/test_helpers.py`; added `tests/conftest_mocks.py` plugin (mock/temp fixtures), wired in pytest_plugins. Updated TESTING_GUIDE.md and AI_TESTING_GUIDE.md. Re-exports later removed; call sites use tests.support.test_helpers.
- Conftest plan Phase 1.2 (logging impl): Extracted logging to `tests/support/conftest_logging_impl.py`; ~500 lines removed from conftest. Phase 1.2 (cleanup impl): Extracted to `conftest_cleanup_impl.py`. Unused-imports: marked `import sys` with noqa in conftest; Obvious Unused: 0.
- Phase 2 plugins: cleanup, logging, hooks, user_data, env-all conftest_* plugins added and wired; run_tests imports `_consolidate_worker_logs` from conftest_hooks. Test support layout: renamed `tests/support` to `tests/test_support`; moved all six plugins there; all imports now `tests.test_support`.
- Tier 3 / AI priorities: checkin_view hardened with tmp_path; hashlib removed from conftest. Policy: allowlist conftest_hooks for datetime; removed 10 obvious unused imports (conftest + conftest_cleanup).
- AI priorities (2026-02-25): Documentation drift: DIRECTORY_TREE.md updated for tests/test_support/; path drift 0. Five UI tests marked no_parallel (shared user index/test_data_dir). Two obvious unused imports removed from conftest. ASCII: doc-fix and doc-sync verified.
- run_tests.py: `--full` parallel timeout 60 min; stuck detection (10 min no output) saves partial results then terminates.

### 2026-02-24 - Module refactor candidates tool and development tools refinements **COMPLETED**
- Added `analyze_module_refactor_candidates`: identifies large/high-complexity modules; configurable thresholds; Tier 2 audit; AI_STATUS, AI_PRIORITIES, consolidated report. Refinements: `total_function_complexity` naming, short threshold message, legacy guide in refactor guidance, top-level tests/ included; AI_PRIORITIES standard order, "Top target modules", no Effort lines, sub-indent for top-3 lists; improvement plan Section 2.8 (dev-tools-only audit mode). analyze_functions JSON: `files_affected`, `critical_complexity_examples`/`high_complexity_examples` (relative paths) from script; wrapper no longer merges cache. Test: `test_cleanup_test_temp_dirs_pytest_dirs` verified passing.

### 2026-02-24 - Checkin-view Tier 3 fix + tool-wrappers branch coverage push **Progressed**
- Investigated Tier 3 failure from `development_tools/tests/logs/pytest_parallel_stdout_2026-02-24_13-16-22.log` and fixed `tests/unit/test_checkin_view.py::TestCheckinView::test_cancel_checkin_button_handler_with_valid_user` recurrence by removing collision-prone fixed IDs.
- Hardened `tests/unit/test_checkin_view.py` valid-user button-handler tests to use per-test unique `user_id` / `discord_user_id` values and explicit user-creation assertions, reducing parallel isolation risk.
- Added branch-focused dev-tools coverage tests in `tests/development_tools/test_tool_wrappers_branch_paths.py` targeting low-coverage `development_tools/shared/service/tool_wrappers.py` wrapper decision paths (`run_script`, `run_analyze_documentation`, `run_analyze_error_handling`, `run_generate_test_coverage_report`).
- Updated planning docs with this session's progress and follow-up tracking:
  - [TEST_PLAN.md](development_docs/TEST_PLAN.md)
  - [PLANS.md](development_docs/PLANS.md)
  - [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md)
- Validation:
  - `pytest -q tests/unit/test_checkin_view.py::TestCheckinView::test_cancel_checkin_button_handler_with_valid_user tests/unit/test_checkin_view.py::TestCheckinView::test_skip_question_button_handler_with_valid_user` -> `2 passed`
  - `pytest -q tests/unit/test_test_policy_guards.py tests/unit/test_checkin_view.py::TestCheckinView::test_cancel_checkin_button_handler_with_valid_user` -> `7 passed`
  - `pytest -q tests/development_tools/test_tool_wrappers_branch_paths.py` -> `9 passed`
  - `pytest -q tests/unit/test_test_policy_guards.py tests/development_tools/test_tool_wrappers_branch_paths.py` -> `15 passed`
- Full diff review executed (`git diff --stat`, `git diff --name-only`); per user confirmation, all files currently present in the working-tree diff are session-scoped and actioned in this session.
- Session-scoped added tests also include:
  - `tests/development_tools/test_retention_engine.py`
  - `tests/development_tools/test_tool_wrappers_branch_paths.py`

### 2026-02-24 - Tier 3 stabilization + portability hardening + unused-imports perf completion **Progressed**
- Closed the Tier 3 parallel race in logger behavior tests by replacing shared `tests/data/logs` teardown fixtures with isolated per-test `tmp_path` log directories (`tests/behavior/test_logger_behavior.py`).
- Hardened test-runtime temp handling and cleanup in `tests/conftest.py` + `development_tools/tests/run_test_coverage.py` + `development_tools/run_development_tools.py` (Windows mkdir/cleanup patching, safer pytest runner temp-root handling, and transient test-artifact cleanup under `tests/data/tmp*`).
- Completed roadmap item `5.1.1` in code: `development_tools/imports/analyze_unused_imports.py` now uses batched `ruff` (`F401`) with `pylint` fallback, changed-file incremental cache flow, no multiprocessing primary path, preserved categorization semantics, and explicit performance telemetry; report output now includes backend/scan-mode/throughput in `report_generation.py`.
- Advanced portability/config independence: added config-driven `tests_dir/tests_data_dir` and test-marker settings in `development_tools/config/*`; updated `shared/common.py`, `shared/constants.py`, `tests/analyze_test_markers.py`, and `shared/standard_exclusions.py` to remove hardcoded assumptions and better exclude pytest runtime artifacts.
- Updated and validated regression coverage in `tests/development_tools/test_analyze_unused_imports.py`, `test_analyze_test_markers.py`, `test_standard_exclusions.py`, `test_fix_project_cleanup.py`, and `test_regenerate_coverage_metrics.py`; refreshed generated status/priorities/reports and planning docs.
- Validation evidence included targeted reruns (`1 passed` targeted logger test; `15 passed` logger file with `-n 6`) plus user-provided full audit completion in-session (`2026-02-24 04:17:43`).
- Full diff review completed (`git diff --stat`, `git diff --name-only`); per user confirmation, **all files currently in the working tree diff were actioned in this session**.

### 2026-02-23 - TEST_PLAN consolidation + audit throughput recovery **Progressed**
- Primary objective completed: created [TEST_PLAN.md](development_docs/TEST_PLAN.md) and consolidated/organized test-related planning into it as the canonical testing roadmap (with [TODO.md](TODO.md)/`PLANS.md` pointing to it as source of truth).
- Restored safe Tier 3 coverage concurrency and added concurrency-aware worker caps in `audit_orchestration.py` + `commands.py`, recovering full-audit speed without reintroducing earlier timeout failures.
- Temporarily preserved `.analyze_unused_imports_cache.json` during `--clear-cache` (`fix_project_cleanup.py`), preventing repeated cold scans while the analyzer performance redesign is pending.
- Added explicit unused-imports performance follow-up tasks in [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md) (section `5.1.1`) and synced planning pointers in [TODO.md](TODO.md) + [PLANS.md](development_docs/PLANS.md).
- User-verified full run result after changes: `audit --full --clear-cache` completed successfully in ~`277s` wall-clock, with Tier 3 parallel savings and no tool failures.

### 2026-02-22 - Flow deferral/cooldown hardening + Discord wiring tests **COMPLETED**
- Implemented scheduled-send flow protection end-to-end: active-flow and post-flow cooldown gating now defer scheduled sends, and scheduler performs a one-time +10 minute retry without recursive deferral.
- Added flow completion/cooldown tracking APIs in `conversation_flow_manager` and updated `channel_orchestrator` send-status handling (`sent`/`deferred`/`skipped`/`failed`), with scheduler branching on deferred behavior.
- Added focused coverage for the new behavior in `tests/unit/test_channel_orchestrator.py`, `tests/behavior/test_conversation_flow_manager_behavior.py`, and `tests/behavior/test_scheduler_coverage_expansion.py`.
- Added Discord behavior coverage for dynamic app command callback routing, `on_ready` app-command sync, and classic dynamic command mapping with explicit `help` skip in `tests/behavior/test_discord_bot_behavior.py`.
- Compliance re-check against [AI_TESTING_GUIDE.md](ai_development_docs/AI_TESTING_GUIDE.md) plus policy-guard run passed (`206 passed`), and user-reported full audit run raised no new issues with all tests passing.
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

## Archive Notes
Older detailed entries live in `development_docs/changelog_history/` and remain the historical source of truth. Use [CHANGELOG_DETAIL.md](development_docs/CHANGELOG_DETAIL.md) for the latest detailed entries and the archive folder for month-split history.
