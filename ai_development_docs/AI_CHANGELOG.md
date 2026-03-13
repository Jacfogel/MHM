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

### 2026-03-13 - Qt UI Windows skip refinement **Progressed**
- Narrowed Windows-only Qt UI skips: centralized `skip_qt_ui_on_windows`, limited default skips to `CheckinSettingsWidget` and `ScheduleEditorDialog` behavior modules, and restructured dialog tests so non-problematic Qt dialogs still run on this PC.
- Ensured full `python run_tests.py` suite passes here with focused 21-test skips while keeping the existing `MHM_QT_UI_FORCE` opt-in to run the previously unstable modules on machines where they succeed.
- Updated `tests/debug_qt_ui_windows.py`, `tests/TESTING_GUIDE.md`, and `development_docs/TEST_PLAN.md` to document the current Windows Qt skip behavior and track follow-up work to reduce or remove these environment-driven skips.

### 2026-03-12 - Doc drift, Ruff clean, fixture metadata, module_deps fallback **COMPLETED**
- **Documentation drift**: Fixed path references (sync_ruff_toml → development_tools/config/sync_ruff_toml.py in guides; TODO script paths reworded; memory_profiler refs softened in AI_TESTING_GUIDE and TESTING_GUIDE). Ran doc-fix (ASCII, headings, convert-links). Added fixture placeholders: AI_STATUS.md, AI_PRIORITIES.md in tests/fixtures/development_tools_demo; tests/ai/results/ai_functionality_test_results_latest.md so path drift and links resolve.
- **Ruff**: Resolved all 6 issues (UP015, SIM105, UP045, F401 unused QTimer) in analyze_unused_imports.py, audit_signal_state.py, debug_qt_ui_windows.py; `ruff check .` passes.
- **Fixture test**: Updated fixture status files to include required metadata (`> **Generated**: This file is auto-generated.` and `> **Last Generated**: YYYY-MM-DD HH:MM:SS`) so test_fixture_status_files_have_valid_metadata passes.
- **Report generation**: analyze_module_dependencies now always stores a standard-format result in results_cache and disk (even when parser returns no summary) so report generation finds data and no longer logs "[DATA SOURCE] no data found in any source".

### 2026-03-12 - Audit interrupt reliability, DATA SOURCE warnings, cache merge **Progressed**
- **Audit stop on intent only:** Second Ctrl+C was logging "stopping" but audit still completed. Now post-handler check returns exit 1 when stop was requested; Tier 3 polls `audit_sigint_requested()` and breaks/stops so the run actually ends. Spurious SIGINT (no user Ctrl+C) was stopping the audit on Windows; now **three** SIGINTs within 2s are required to stop, and worker KeyboardInterrupt no longer counts as a tap (`development_tools/shared/audit_signal_state.py`, `run_development_tools.py`, `audit_orchestration.py`).
- **DATA SOURCE warnings removed:** `analyze_module_dependencies` and `config_validation_summary` no longer log "no data found" / "not found": (1) Tier 1 runs `run_analyze_config` and persists to cache/file so reports find config data; (2) `analyze_module_dependencies` stores standard format in `results_cache` for the loader; (3) `_load_config_validation_summary` tries results_cache -> standardized storage -> file; (4) `_reload_all_cache_data` merges disk into cache instead of clearing it, so in-memory results from the current run survive for report generation.
- **Tests:** Audit orchestration interrupt tests updated (patch `audit_module.audit_signal_state.record_audit_keyboard_interrupt`, fake executor `shutdown`); `test_run_analyze_module_dependencies_builds_standard_summary` asserts cache `details` shape.

### 2026-03-11 - Spurious SIGINT double-tap, doc consolidation, scripts move **COMPLETED**
- **Double-tap Ctrl+C to stop:** Single SIGINT is ignored (avoids spurious stops); press Ctrl+C again within 2s to stop the run. Implemented in `run_tests.py` interrupt handler.
- **Doc consolidation:** Deleted `development_docs/SPURIOUS_SIGINT_INVESTIGATION.md`; content folded into TEST_PLAN.md Section 4.2 and Section 5.6.1. TESTING_GUIDE.md: fixed references to non-existent scripts (SCRIPTS_GUIDE, cleanup_windows_tasks, scripts/testing/*); added "Stopping a run" (double-tap) and pointer to TEST_PLAN.
- **Scripts move:** `run_trace_consolectrl.ps1`, `run_trace_consolectrl.py`, `trace_consolectrl.js` moved from `development_docs/` to `scripts/`; all call sites and docs updated.

### 2026-03-11 - Test runner: full-run reliability, phase-failure reporting, skip/deselect targets **Progressed**
- **Full run without spurious interrupts:** `--full` now implies `--ignore-sigint` so `python run_tests.py --full` completes; added `--no-ignore-sigint` to override. Reverted auto `MHM_QT_UI_FORCE=1` on Windows so Qt UI tests that crash (e.g. CheckinSettingsWidget access violation) stay skipped by default.
- **Combined summary reflects phase crashes:** When a phase exits non-zero (e.g. access violation) but JUnit has 0 failed/errors, the summary now shows at least 1 error and a `[PHASE FAILED]` line so the run is not reported as success.
- **Deselected and skip targets:** Combined summary "Deselected" now only counts tests deselected in both parallel and serial (excluded from entire run). TEST_PLAN.md: added program-level success criterion for at most 1 skipped test; elevated spurious SIGINT to high priority with investigate -> fix -> clean up workarounds (Section 4.2, Section 5.6.1).
- **Docs:** TESTING_GUIDE.md updated (full-run command, expected skips, Start-Process/external terminal). TEST_PLAN.md last-updated and success criteria refreshed.

### 2026-03-05 - Test suite: notebook import fix + Qt UI Windows skip + debug script **Progressed**
- Fixed notebook import in pytest: project root is now forced to the front of `sys.path` in `tests/conftest.py` (remove then insert) so pytest's prepend of the test dir no longer hides top-level packages.
- Isolated two Qt UI test modules that crash with access violation on some Windows PCs: skipped on Windows by default, overridable with `MHM_QT_UI_FORCE=1`; set `QT_OPENGL=software` on Windows in conftest to reduce GPU-related crashes.
- Added `tests/debug_qt_ui_windows.py` for env comparison (Python/OS/Qt versions, minimal widget test) and excluded it from the no-prints policy.

### 2026-03-05 - Static-analysis cleanup + guard tightening + CI policy fix **Progressed**
- Cleared Ruff backlog to zero (`128 -> 0`) across runtime/tooling/tests and revalidated static checks; Pyright baseline remains `0 errors / 54 warnings`.
- Tightened deprecation-inventory sync guard behavior to reduce false positives: narrowed trigger keywords and excluded `tests/**` + generated artifacts from trigger-file detection.
- Added guard regression tests (`test_deprecation_inventory_guard.py`) for ignored test/generated paths and verified guard pass behavior.
- Fixed GitHub `Tooling Policy Consistency` workflow dependency setup by installing `python-dotenv` with `pytest` in `.github/workflows/logging-enforcement.yml`.

### 2026-03-05 - Legacy inventory governance + compatibility cleanup **Progressed**
- Established canonical deprecation inventory governance via `development_tools/config/jsons/DEPRECATION_INVENTORY.json`, wired config/docs to it, and added legacy-analysis sync-guard enforcement for deprecation-like changes without inventory updates.
- Integrated inventory-aware legacy tooling: analyzer now injects active/candidate inventory terms into scans, and `LEGACY_REFERENCE_REPORT.md` now includes a dedicated inventory summary block with counts/hits.
- Removed deprecated compatibility paths (`--update-plan` coverage flag plumbing and `_consolidate_and_cleanup_main_logs` no-op placeholder), updated related tests, and moved both corresponding inventory items to `removed` (`2026-03-05`).
- Session wrap-up included full diff review + planning/doc sync and regenerated outputs (legacy report, coverage report, AI status/priorities, consolidated report); legacy backlog reduced to active bridge/retire-candidate items only.

### 2026-03-04 - Coverage push + report generation cleanup **Progressed**
- Added targeted coverage tests across core, communication, and UI helper/branch paths (`config`, `file_operations`, `user_item_storage`, `backup_manager`, `channel_orchestrator`, reminder parsing, UI user combo helpers).
- Updated `development_tools/tests/generate_test_coverage_report.py` so `TEST_COVERAGE_REPORT.md` now includes complete domain scope text (including `notebook`), a generated domain-coverage section, and generated marker counts under `## Test Markers`.
- Removed stale E2E marker narrative from coverage report output and regenerated coverage/audit artifacts (`AI_STATUS`, `AI_PRIORITIES`, consolidated report, analysis JSONs, and coverage report).
- Validation highlights: targeted run `50 passed`; latest generated coverage snapshot is `76.4%` overall with highest remaining misses in `ui`, `communication`, and `core`.

### 2026-03-04 - Complexity batch + priority-source correction **Progressed**
- Refactored a focused 5-function high-complexity batch with behavior-preserving helper extraction across service loop, logger rollover, interaction manager init, UI user-list refresh, and reminder parsing flows.
- Fixed `development_tools/shared/service/report_generation.py` so `AI_PRIORITIES` "Highest complexity" examples come from `analyze_functions_results.json` (global top) and only use decision-support examples as fallback.
- Re-ran audit outputs and confirmed `AI_PRIORITIES` now shows global-top examples (`initialize__register_events`, `_extract_entities_rule_based`, `_show_question_dialog`) instead of stale chatbot-only examples.

### 2026-03-03 - Full-suite interrupt hardening + reporting integrity **Progressed**
- Hardened `run_tests.py` against noisy SIGINT during active test subprocesses: first interrupt is now soft/non-blocking, while a rapid second interrupt still force-stops.
- Improved combined summary accounting for interrupted runs with explicit incomplete-test reporting, and preserved phase-specific failure source labels in combined failure output.
- Fixed behavior/dev-tools regressions uncovered in failing runs: restored `_get_user_profile` account fetch expectations (`user/context_manager.py`) and added xdist-worker-specific legacy report output naming to remove cross-worker file contention (`development_tools/legacy/generate_legacy_reference_report.py`).
- Reintroduced a low-priority `Watch List` section in generated `development_tools/AI_PRIORITIES.md` (via report generation)

### 2026-03-03 - Tier 3 remediation continuation + closeout tracking **Progressed**
- Fixed the previously remaining behavior failure `test_send_predefined_message_real_behavior` by restoring `channel_orchestrator` message path resolution through `determine_file_path`, matching real behavior and patch targets.
- Removed one safe unused import in `communication/core/channel_orchestrator.py` (`get_user_data_dir`) after the path-resolution fix; targeted Ruff check for F401 passed.
- Completed session wrap-up inventory with full working-tree diff review (`git diff --stat`, `git diff --name-only`) and created paired changelog entries for this session.

### 2026-03-02 - Task split, notebook rename, error handling Phase 1, follow-ups **COMPLETED**
- Unified user items: added `core/user_item_storage.py` and `is_valid_user_id`; split `tasks/task_management.py` into task_schemas, task_validation, task_data_handlers, task_data_manager; renamed `notebook/schemas.py` to `notebook/notebook_schemas.py`. All call sites use `from tasks import ...`; task_handler and profile_handler use lazy `_get_tasks()`.
- Test fixes: patches updated to `tasks.*` / `tasks.task_data_manager.*`; due_date in update path resolved (e.g. "tomorrow") via relative-date parsing; get_user_task_stats default and title=None validation aligned.
- Error handling Phase 1: `@handle_errors` now supports `re_raise=True`; `_get_tasks()` in both handlers use decorator with re_raise; `validate_update_field` decorated; static logging single-arg fix; unused imports removed (user_item_storage, task_schemas, task_validation). MODULE_DEPENDENCIES_DETAIL and error-handling guides updated.

### 2026-03-02 - Sleep schedule parsing + prompt concision **COMPLETED**
- Sleep schedule time_pair parser now accepts "and" inside each chunk (e.g. "1:00 AM and 4:00 AM, 6:00 and 11:00"); previously only `-`, `to`, `until`, `->` were accepted, so the first response was rejected.
- Shortened `sleep_schedule` question_text and error_message in `resources/default_checkin/questions.json` to one line each.
- Regression test added in `test_checkin_questions_enhancement.py` for multi-chunk "and" format.

### 2026-03-02 - Coverage-gap push + Phase1/2 error-handling closeout
- Added a broad targeted test pass for uncovered branches (profile handler, auto-cleanup, notebook/analytics/email/webhook helpers, file locking, tags, UI generation script, file auditor), with focused gains including `profile_handler` ~97% and `auto_cleanup` ~94% in module-targeted runs.
- Fixed `file_auditor` fallback decorator path so analyzer noise is removed in degraded-import mode; after cache-clear re-analysis, error-handling metrics now show `functions_missing_error_handling=0`, `phase1_total=0`, `phase2_total=0`.
- Resolved the previously failing parallel UI generation tests by isolating script-module loading in `test_generate_ui_files_script.py` (no shared `sys.modules['ui.generate_ui_files']` mutation); validated failing subset now passes under `-n auto`.
- Regenerated docs/audit outputs (`docs`, `doc-fix --convert-links`, `doc-sync`, `audit --quick`) and synced status/priorities/report artifacts for closeout; `audit --full` remained intermittently interrupted in this environment and is tracked as a follow-up reliability task.

### 2026-03-02 - Portability sweep static-tooling config ownership slice and closeout: timing-path relocation + audit validation **Progressed**
- Moved timing artifact path from `development_tools/reports/tool_timings.json` to `development_tools/reports/jsons/tool_timings.json` in audit orchestration; updated impacted tests/fixtures accordingly.
- Added roadmap clarification in `AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md` for dual-config static-analysis state: keep both root + dev-tools `pyrightconfig.json` and both root + dev-tools Ruff config for now, with explicit next-step criteria.
- Session validation confirmed: targeted tests passed for timing-path changes, and user-run full audit reported no regressions after doc-fix follow-up.
- Regenerated and synced standard development-tools outputs/docs as part of full-audit closeout.
- Implemented explicit static-analysis config ownership paths: Ruff now syncs/uses `development_tools/config/ruff.toml` (with optional root `.ruff.toml` compatibility mirror), and Pyright now uses explicit `--project development_tools/config/pyrightconfig.json` unless overridden.
- Extended static-analysis config surface in `development_tools/config/config.py` and both config JSON files with `ruff_config_path`, `pyright_project_path`, and `ruff_sync_root_compat`.
- Added/expanded regression coverage for static-analysis invocation args, config override handling, and Ruff sync determinism (`test_static_analysis_tools.py`, `test_config.py`, new `test_sync_ruff_toml.py`).
- Updated portability roadmap tracking (`AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md` sections `3.17` and `7.6`) plus paired development-tools guides with compatibility/ownership notes.

### 2026-03-02 - Tooling policy hardening + dev-tools coverage parallel fix **COMPLETED**
- Replaced standalone tooling-consistency enforcement with deterministic policy tests and removed the `tooling-consistency` command/analyzer wiring (`cli_interface.py`, `tool_wrappers.py`, `tool_metadata.py`, deleted `development_tools/config/analyze_tooling_consistency.py`).
- Hardened policy coverage in `tests/development_tools/test_tooling_policy_consistency.py`: command-group parity checks, runtime-budget guard, stricter command-doc parity (including stale-command detection in command sections), and AST-based scanner-candidate detection.
- Added CI enforcement via `.github/workflows/logging-enforcement.yml` job `tooling-policy-consistency` to run `pytest tests/development_tools/test_tooling_policy_consistency.py -q` on push/PR.
- Fixed dev-tools coverage worker scaling: `run_dev_tools_coverage()` now actually applies xdist flags (`-n <workers>`, `--dist=loadscope`) when parallel mode is enabled; added regression coverage in `tests/development_tools/test_regenerate_coverage_metrics.py`.

## Archive Notes
Older detailed entries live in `development_docs/changelog_history/` and remain the historical source of truth. Use [CHANGELOG_DETAIL.md](development_docs/CHANGELOG_DETAIL.md) for the latest detailed entries and the archive folder for month-split history.
