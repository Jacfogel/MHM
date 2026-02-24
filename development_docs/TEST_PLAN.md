# Test Program Consolidation Plan

> **File**: `development_docs/TEST_PLAN.md`  
> **Scope**: Canonical testing roadmap (reliability-first, multi-session)  
> **Status**: **IN PROGRESS**  
> **Owner**: Human developer + AI collaborators  
> **Created**: 2026-02-22  
> **Last Updated**: 2026-02-24 (Session 5 checkin-view isolation fix)
> **Parent**: [PLANS.md](development_docs/PLANS.md)  
> This plan is subordinate to `development_docs/PLANS.md` and must remain consistent with its standards and terminology.

---

## 1. Source of Truth

This document is the canonical source for testing program planning and execution.

- Testing items previously spread across `development_docs/PLANS.md` and `TODO.md` are consolidated here.
- `development_docs/PLANS.md` and `TODO.md` should keep only lightweight pointers for testing work.
- Any new testing roadmap item must be added here first, then referenced elsewhere.

---

## 2. Baseline Snapshot (2026-02-22)

### 2.1 Reliability baseline

- Latest full Tier-3 audit (`2026-02-22 21:20`): **clean/successful**.
- Notable same-day regression window:
  - Full audit at `2026-02-22 21:11` failed with 2 parallel UI nodes.
  - Follow-up full audit at `2026-02-22 21:20` passed clean.
- Previously failing node:
  - `tests/ui/test_account_creation_ui.py::TestAccountCreationErrorHandling::test_invalid_data_handling_real_behavior`
  - Current status: **stable in repeated parallel reruns** this session (`x5`) and module rerun.

### 2.2 No-parallel baseline

- `@pytest.mark.no_parallel` markers in test code:
  - **94 total markers** across `tests/*.py` (includes policy/e2e-support files).
  - **90 markers across 14 product test files** when excluding:
    - `tests/unit/test_test_policy_guards.py`
    - `tests/development_tools/test_audit_tier_e2e_verification.py`

### 2.3 Harness and logging baseline

Signals currently present in logs and/or recent outputs:

- Repeated cache invalidation messages for missing tool hash metadata were observed historically in `logs/ai_dev_tools.log`.
- Windows temp/ACL failures remain a recurring instability source in parallel runs (`tests/logs/partial_results.json`, pytest temp paths under `tests/data/tmp/pytest_runner/...`).
- Retention/archive path growth warnings (`WinError 123`) are present in `tests/logs/test_run.log` for long backup names.
- Test-run signals historically appeared in production-oriented logs (`logs/errors.log`, `logs/ai_dev_tools.log`) in some test-tooling paths.
- Current audit log source for test-tool runs is `development_tools/tests/logs/ai_dev_tools.log`; `logs/ai_dev_tools.log` may contain only stale/earlier entries.
- Compatibility note: `logs/ai_dev_tools.log` now intentionally mirrors dev-tools audit logs (in addition to `development_tools/tests/logs/ai_dev_tools.log`) for operator visibility.

### 2.4 Coverage baseline

- `development_docs/TEST_COVERAGE_REPORT.md` baseline: **72.6% overall**.
- Coverage variability remains unresolved across unchanged code runs (historical spread includes low-40s to low-70s percentages).

---

## 3. Session Progress (2026-02-22)

### Completed in this session

- Hardened `test_checkin_view` parallel isolation for Discord button-handler tests:
  - File: `tests/unit/test_checkin_view.py`
  - Replaced fixed IDs with per-test unique `user_id` / `discord_user_id` values.
  - Added explicit user-creation assertions to fail early on setup issues.
  - Target node from full audit recurrence:
    - `tests/unit/test_checkin_view.py::TestCheckinView::test_cancel_checkin_button_handler_with_valid_user`
- Hardened account-creation invalid-data test assertion path for delayed persistence/index scenarios:
  - File: `tests/ui/test_account_creation_ui.py`
  - Added broader account matching (`internal_username`, `username`, `user_id`) and `wait_until(...)`-based persistence polling.
  - Added one explicit `rebuild_user_index()` retry before final assertion to reduce xdist lag flakes.
- Implemented cache metadata/schema backfill-on-load for coverage caches:
  - `development_tools/tests/test_file_coverage_cache.py`
  - `development_tools/tests/dev_tools_coverage_cache.py`
  - Backfills missing legacy fields (`tool_hash`, `tool_mtimes`, schema keys, config mtime where available).
- Added regression tests for cache metadata backfill:
  - `tests/development_tools/test_test_file_coverage_cache.py`
  - `tests/development_tools/test_dev_tools_coverage_cache.py`
- Added regression coverage for legacy cache instance state:
  - `tests/development_tools/test_test_file_coverage_cache.py::test_save_cache_backfills_missing_excluded_test_dirs`
  - prevents save failures when older/partial instances are missing `excluded_test_dirs`.
- Cleared documentation/test-hygiene quick wins from priorities:
  - Converted remaining unconverted references to `[AI_TESTING_GUIDE.md](ai_development_docs/AI_TESTING_GUIDE.md)` links in `ai_development_docs/AI_CHANGELOG.md` and `development_docs/PLANS.md`.
  - Removed the last obvious unused import (`uuid`) from `tests/conftest.py`; `UNUSED_IMPORTS_REPORT.md` now reports `Obvious Unused: 0`.
- Hardened test-file cache test discovery against ACL/path traversal errors:
  - Replaced brittle `rglob`-only paths with ACL-tolerant walker in `development_tools/tests/test_file_coverage_cache.py`.
- Added pytest temp-dir hardening for Windows ACL stability:
  - `tests/conftest.py` now patches pytest temp cleanup to be best-effort on `PermissionError`.
  - `tests/conftest.py` normalizes Windows `Path.mkdir(..., mode=0o700)` to avoid unreadable ACL artifacts in this environment.
  - `tests/conftest.py` now uses dedicated pytest runtime root `tests/data/tmp_pytest_runtime` and honors externally provided temp-root env overrides.
  - `tests/conftest.py` now ignores transient/manual local temp probe dirs (`/tests/tmp_pytest_*`, `/tests/manual_mode700_dir`) during collection.

### Validation completed this session

- `pytest` targeted set passed:
  - `tests/unit/test_checkin_view.py::TestCheckinView::test_cancel_checkin_button_handler_with_valid_user`
  - `tests/unit/test_checkin_view.py::TestCheckinView::test_skip_question_button_handler_with_valid_user`
  - Result: **2 passed**.
- Policy guard compliance check passed:
  - `tests/unit/test_test_policy_guards.py`
  - `tests/unit/test_checkin_view.py::TestCheckinView::test_cancel_checkin_button_handler_with_valid_user`
  - Result: **7 passed**.
- `pytest` targeted set passed:
  - `tests/ui/test_account_creation_ui.py::TestAccountCreationErrorHandling::test_invalid_data_handling_real_behavior`
  - `tests/development_tools/test_test_file_coverage_cache.py`
  - `tests/development_tools/test_dev_tools_coverage_cache.py`
- Result: **10 passed** (serial targeted run).
- Additional Phase 3 targeted validations passed:
  - `tests/development_tools/test_test_file_coverage_cache.py`
  - `tests/development_tools/test_dev_tools_coverage_cache.py`
  - `tests/unit/test_logger_unit.py::TestTestingEnvironmentDetection::test_dev_tools_log_paths_are_isolated_from_production`
- Result: **10 passed total across these Phase 3 validation commands** (`9 + 1`).
- Targeted parallel reliability validation passed for Phase 2 gate:
  - `tests/ui/test_account_creation_ui.py::TestAccountCreationErrorHandling::test_invalid_data_handling_real_behavior` (`x5`, `-n auto`)
  - Result: **5/5 passed**.
- Full module rerun passed:
  - `tests/ui/test_account_creation_ui.py` (`-n auto`)
  - Result: **41 passed**.
- Full Tier-3 validation rerun passed:
  - `.venv\Scripts\python.exe development_tools/run_development_tools.py audit --full`
  - Result: **Tier 3 successful** (`2026-02-22 16:31`).
- Session 3 validation refresh:
  - Full audit evidence:
    - `2026-02-22 21:11`: Tier 3 failed (2 parallel UI test failures).
    - `2026-02-22 21:20`: Tier 3 successful on rerun.
  - Targeted parallel reruns for regressed nodes:
    - `tests/ui/test_account_creation_ui.py::TestAccountCreationIntegration::test_full_account_lifecycle_real_behavior`
    - `tests/ui/test_account_creation_ui.py::TestAccountCreationIntegration::test_multiple_users_same_features_real_behavior`
    - Result: **5/5 runs clean** (`-n auto`, both nodes together).

### Validation still pending

- Run a second unchanged full-audit pair for Phase 4 cache-stability acceptance (cache-hit trend evidence).
- Promote two regressed account-creation integration nodes from monitor-only to sustained stability criteria (module-level + next full-suite trend).

---

## 4. Priorities and Success Criteria

### 4.1 Priority mode

1. Reliability correctness and deterministic test outcomes.
2. Harness stability (Windows temp/IO/logging behavior).
3. Throughput (no-parallel reduction, selective rerun quality).
4. Coverage consistency, then coverage growth.

### 4.2 Program-level success criteria

- [ ] Tier-3 parallel track reaches clean state on consecutive reruns.
- [ ] No recurring `tool hash missing ... cache metadata` invalidation messages on unchanged consecutive audits.
- [ ] No recurring `Access is denied`/`WinError 123` warnings in fresh test-tool runs.
- [ ] Production logs remain clean of test-run traffic in test-tool execution.
- [ ] No-parallel markers reduced by >=50% from 90 baseline (target <=45), with reason comments for all remaining markers.
- [ ] Coverage variability narrowed to a stable envelope on unchanged code.

---

## 5. Execution Plan (Reliability-First)

### 5.1 Phase 1: Canonicalization and baseline freeze

Status: **IN PROGRESS**

- [x] Create canonical plan in `development_docs/TEST_PLAN.md`.
- [x] Complete parity review: every open testing item from `PLANS.md` and `TODO.md` either:
  - migrated here,
  - explicitly marked monitor-only here, or
  - intentionally dropped with reason.
- [x] Replace old test-plan content in `PLANS.md` and `TODO.md` with source-of-truth pointers.

Acceptance:
- [x] Parity checklist complete.
- [x] `PLANS.md`/`TODO.md` testing sections reduced to pointers.

### 5.2 Phase 2: Immediate reliability blockers

Status: **FIXED (Monitor)**

- [x] Harden `test_invalid_data_handling_real_behavior` assertion path for index/persistence lag.
- [x] Validate node stability with:
  - targeted node x5 in parallel mode,
  - full `tests/ui/test_account_creation_ui.py` run,
  - full Tier-3 parallel rerun.
- [x] Update this plan item status to one of: `fixed`, `monitor`, `reopen`.

Acceptance:
- [x] 3 consecutive targeted parallel reruns clean.
- [x] 1 full rerun clean.

### 5.3 Phase 3: Harness stability (Windows/IO/retention/logging)

Status: **IN PROGRESS**

### Windows temp/ACL hardening
- [x] Eliminate tmp-path `Access is denied` races under `tests/data/tmp/pytest_runner/...` for coverage/test tracks via pytest temp-root and mkdir-mode hardening.
- [x] Ensure deterministic cleanup ownership/retry behavior for temp dirs.
- [x] Validate with parallel reruns and verify no tmp_path setup/teardown PermissionError in latest clean Tier-3 run.

### Retention/archive correctness
- [x] Fix long-name backup/archive behavior causing `WinError 123` in `tests/logs/test_run.log`.
- [x] Enforce retention model:
  - 1 current artifact
  - 7 rolling backups
  - archived history with bounded names/paths

### Production-log pollution elimination
- [x] Route all test/dev-tools test run logging to test paths only (`tests/logs/`, `development_tools/tests/logs/`).
- [x] Add safeguard checks in logger setup to prevent test-mode writes to production logs.
- [x] Verify clean production logs after full audit run.
- [x] Add compatibility mirror so `logs/ai_dev_tools.log` also receives dev-tools audit entries (intentional operational visibility).

### Test artifact cleanup simplification
- [x] Define explicit allowlist of persistent fixture/static roots under `tests/data/`.
- [x] Ensure all non-allowlisted test-generated artifacts are cleaned between runs.

Current session implementation notes (2026-02-22):
- `tests/conftest.py`:
  - `LogLifecycleManager.archive_old_backups()` now uses stable archive naming (no repeated timestamp chaining) with hash-shortening for oversized filenames.
  - `_apply_versioned_retention_protocol()` now treats archive as sink-only (no archive-to-backup promotion).
  - `_cleanup_pytest_cache_temp_dirs()` now uses stronger Windows-safe retry + chmod handling.
- `run_tests.py`:
  - `apply_artifact_retention()` now treats archive as sink-only and resolves target collisions deterministically.
  - `cleanup_post_run_test_artifacts()` now enforces explicit persistent-root allowlist (`devtools_pyfiles`, `devtools_unit`) and clears all other generated test artifacts under `tests/data/`.
- `development_tools/tests/run_test_coverage.py`:
  - Added test subprocess log-env forcing to `tests/logs` roots (`MHM_TESTING=1`, `TEST_CONSOLIDATED_LOGGING=1`, `LOGS_DIR`/backup/archive overrides).
  - Added retry-based tree cleanup helper and wired it into stray pytest cache temp cleanup.
- `core/logger.py`:
  - Dev-tools execution now routes all log files (including `errors_file`) to `development_tools/tests/logs/` by default, avoiding production log pollution.
  - Added compatibility mirror handler so dev-tools entries are also written to `logs/ai_dev_tools.log`.
- Additional temp-root hardening in this session:
  - Patched pytest temp-dir mode handling in `tests/conftest.py` to avoid unreadable ACL artifacts from `mode=0o700` directory creation in this environment.
  - Moved pytest runtime root to `tests/data/tmp_pytest_runtime` (explicitly retained by cleanup allowlist logic).
  - Patched pytest dead-symlink cleanup path to be best-effort on permission errors (prevents teardown crashes from non-test infra cleanup).
- Verification snapshot (`2026-02-22` full audit):
  - `development_tools/tests/logs/ai_dev_tools.log` contains full Tier-3 execution logs.
  - Latest Tier-3 run completed successfully with no test-track `infra_cleanup_error`.
  - Production logs did not receive new `mhm.development_tools` entries during the 12:40-12:48 audit window; `logs/ai_dev_tools.log` currently shows only earlier stale entries from 11:05.
  - Previous infra-only failures were cleared in a follow-up full audit (`2026-02-22 16:31`).

Acceptance:
- [ ] Zero new `Access is denied` in fresh run logs.
- [x] Zero new `WinError 123` in retention/archive paths.
- [x] No test-run entries in production logs **except intentional `logs/ai_dev_tools.log` compatibility mirror**.
- [x] `tests/data/` post-run contains only allowlisted persistent roots.

### 5.4 Phase 4: Coverage cache metadata stabilization

Status: **IN PROGRESS**

- [x] Add schema + metadata backfill-on-load for test-file and dev-tools coverage caches.
- [x] Add regression tests for missing tool-hash metadata backfill.
- [ ] Run two unchanged consecutive full audits and verify cache-hit behavior.
- [ ] Confirm no repeated `tool hash missing ... cache metadata` invalidation messages.
- [ ] Extend regression coverage for old-schema payload variants and invalidation-reason reporting.

Acceptance:
- [ ] Two unchanged consecutive full audits show cache reuse.
- [ ] No recurring missing-tool-hash invalidation messages.

### 5.5 Phase 5: No-parallel marker reduction (waves)

Status: **IN PROGRESS**

Baseline for burn-down: **90 markers / 14 product files**.

### Wave A (1-4 marker files)
- [ ] `tests/behavior/test_message_behavior.py`
- [ ] `tests/behavior/test_discord_bot_behavior.py`
- [ ] `tests/behavior/test_checkin_handler_behavior.py`
- [ ] `tests/behavior/test_discord_checkin_retry_behavior.py`

### Wave B (5-8 marker files)
- [ ] `tests/ui/test_ui_app_qt_main.py`
- [ ] `tests/behavior/test_account_management_real_behavior.py`
- [ ] `tests/unit/test_user_management.py`
- [ ] `tests/integration/test_account_lifecycle.py`
- [ ] `tests/integration/test_user_creation.py`
- [ ] `tests/behavior/test_backup_manager_behavior.py`
- [ ] `tests/behavior/test_user_data_flow_architecture.py`

### Wave C (9+ marker files)
- [ ] `tests/unit/test_user_data_manager.py`
- [ ] `tests/behavior/test_account_handler_behavior.py`

Per-file conversion checklist:
- [ ] Use unique per-test identifiers.
- [ ] Isolate file writes into fixture-owned paths.
- [ ] Patch shared module constants/state.
- [ ] Remove marker only after repeated `pytest -n auto` stability runs.
- [ ] Add explicit reason comments for any marker kept.

Acceptance:
- [ ] Marker count <=45.
- [ ] Remaining markers all have explicit technical reason comments.

### 5.6 Phase 6: Intermittent failure backlog triage

Status: **IN PROGRESS**

### Active suspect queue (high-signal)
- [ ] `tests/ui/test_account_creation_ui.py::TestAccountManagementRealBehavior::test_feature_enablement_persistence_real_behavior`
- [ ] `tests/ui/test_category_management_dialog.py::TestCategoryManagementDialogRealBehavior::test_save_category_settings_updates_account_features`
- [ ] `tests/behavior/test_user_data_flow_architecture.py::TestAtomicOperations::test_atomic_operation_all_types_succeed` (monitor mitigation)
- [ ] `tests/behavior/test_user_data_flow_architecture.py::TestProcessingOrder::test_processing_order_deterministic_regardless_of_input_order` (monitor mitigation)
- [ ] `tests/development_tools/test_fix_project_cleanup.py::TestProjectCleanup::test_cleanup_test_temp_dirs_no_directory`
- [ ] `tests/behavior/test_webhook_handler_behavior.py::TestWebhookHandlerBehavior::test_handle_webhook_event_routes_application_deauthorized`
- [ ] `tests/unit/test_schedule_management.py::TestScheduleManagement::test_schedule_period_lifecycle`
- [ ] `tests/ui/test_task_management_dialog.py::TestTaskManagementDialogRealBehavior::test_save_task_settings_persists_after_reload`
- [ ] `tests/behavior/test_checkin_handler_behavior.py::TestCheckinHandlerBehavior::test_checkin_handler_start_checkin_conversation_manager_error`
- [ ] `tests/unit/test_config.py::TestConfigValidation::test_validate_core_paths_missing_directory`
- [ ] `tests/unit/test_user_data_handlers.py::TestUserDataHandlersConvenienceFunctions::test_update_user_account_valid_input`
- [ ] `tests/unit/test_user_data_handlers.py::TestUserDataHandlersConvenienceFunctions::test_save_user_data_transaction_valid_input`
- [ ] `tests/behavior/test_user_management_coverage_expansion.py::TestUserManagementCoverageExpansion::test_load_account_data_auto_create_real_behavior`
- [ ] `tests/ui/test_account_creation_ui.py::TestAccountCreationIntegration::test_full_account_lifecycle_real_behavior` (recurred `2026-02-22 21:09` and again `2026-02-24 13:04` in full audit; latest failure mode `KeyError: 'features'`; see `development_tools/tests/logs/pytest_parallel_stdout_2026-02-24_13-02-05.log`).
- [ ] `tests/ui/test_account_creation_ui.py::TestAccountCreationIntegration::test_multiple_users_same_features_real_behavior` (recurred `2026-02-22 21:09` and again `2026-02-24 13:04` in full audit; latest failure mode `KeyError: 'features'`; see `development_tools/tests/logs/pytest_parallel_stdout_2026-02-24_13-02-05.log`).
- [ ] `tests/behavior/test_checkin_handler_behavior.py::TestCheckinHandlerBehavior::test_checkin_handler_checkin_status_no_checkins`
- [ ] `tests/behavior/test_account_handler_behavior.py::TestAccountHandlerBehavior::test_handle_link_account_verifies_confirmation_code`
- [ ] `tests/development_tools/test_legacy_reference_cleanup.py::TestCleanupOperations::test_cleanup_legacy_references_dry_run`

### Monitor-only queue (mitigated; reopen on recurrence)
- [ ] `tests/behavior/test_interaction_handlers_behavior.py::TestInteractionHandlersBehavior::test_profile_handler_shows_actual_profile`
- [ ] `tests/ui/test_account_creation_ui.py::TestAccountManagementRealBehavior::test_user_index_integration_real_behavior`
- [ ] `tests/behavior/test_discord_checkin_retry_behavior.py::TestDiscordCheckinRetryBehavior::test_checkin_message_queued_on_discord_disconnect`
- [ ] Windows no-parallel crash code recurrence (`0xC0000135`) in `run_tests.py` serial phase.

Backlog hygiene:
- [ ] Re-rank by last 30-day recurrence + latest audit signals.
- [ ] Close stale suspects with date/evidence.
- [ ] Keep each open suspect with:
  - last observation date
  - repro command
  - current hypothesis

Acceptance:
- [ ] Active queue contains only reproducible/high-confidence suspects.
- [ ] Each open suspect has explicit repro metadata.

### 5.7 Phase 7: Coverage consistency, then growth

Status: **IN PROGRESS**

### Consistency first
- [ ] Instrument run metadata: collected files count, combine path, per-track merge status, total statements.
- [ ] Identify variance drivers:
  - partial combine behavior
  - failed track merges
  - include/exclude drift
  - unstable test selection under cache states
- [ ] Define variance envelope for unchanged code runs and enforce monitoring.

### Growth second
- [ ] Expand tests in priority domains:
  - communication
  - ui
  - core
- [ ] Prioritize high-miss modules from latest coverage report.

Acceptance:
- [ ] Coverage variance stable within agreed envelope on unchanged code.
- [ ] Coverage trend increases without introducing instability.

### 5.8 Phase 8: Governance and automation

Status: **IN PROGRESS**

- [ ] Nightly no-shim burn-in run:
  - `run_tests.py --burnin-mode` or equivalent no-shim+random-order path
  - archive run summaries and regressions
- [ ] Policy strictness burn-down in `tests/unit/test_test_policy_guards.py`:
  - shrink allowlists in small batches
  - converge to strict defaults
- [ ] Add weekly plan review block in this file (updates + blocker summary).

Acceptance:
- [ ] Nightly artifact exists and is reviewed.
- [ ] Allowlist counts trend downward with policy tests green.

---

## 6. Testing Strategy and Coverage Work Migration

Migrated from prior testing strategy items:

- [ ] UI layer testing backlog (see Phase 7 + UI-specific waves in Phase 5/6 as applicable).
- [ ] Integration testing backlog:
  - cross-module workflows
  - end-to-end user scenarios
  - performance testing
  - Discord/text `/checkin` flow end-to-end
  - Discord slash command `/status`, `/profile`, `/tasks` end-to-end
  - Windows normalized-separator path tests for default messages + directory creation

Burn-in residuals:
- [ ] Nightly `--burnin-mode` run and regression tracking.
- [ ] After sustained green window, gate/remove remaining test-only diagnostics.

Performance optimization plan status:
- [ ] Keep broad runtime optimization monitor-only unless runtime regresses materially.
- [ ] Resume only targeted hotspot cleanup if baseline drifts.

---

## 7. Validation Gates

1. Reliability gate:
   - `python development_tools/run_development_tools.py audit --full`
2. Failing-node fix gate:
   - targeted node x5 in parallel context
3. No-parallel conversion gate:
   - per-file `pytest -n auto` loop + module run
4. Logging/isolation gate:
   - grep production logs after test-tool run
5. Cleanup gate:
   - verify `tests/data/` post-run against allowlist
6. Cache gate:
   - two unchanged consecutive full audits show reuse

---

## 8. Migration Parity Checklist

`PLANS.md` migration parity:

- [x] Test Suite Performance Optimization Plan -> Phase 5/7 monitor-only + targeted hotspot policy
- [x] No-Parallel Marker Reduction Plan -> Phase 5 waves/checklists
- [x] Investigate Intermittent Test Failures -> Phase 6 active/monitor queues
- [x] Test Standardization Burn-in residual work -> Phase 8 nightly governance
- [x] Testing Strategy Plan -> Section 6 migration backlog

`TODO.md` migration parity:

- [x] Nightly no-shim validation runs -> Phase 8
- [x] Intermittent parallel hang/crash investigation -> Phase 3 + Phase 6
- [x] Coverage cache invalidation metadata stabilization -> Phase 4
- [x] Test log visibility investigation -> Phase 3 logging
- [x] Test log rotation/archive issue -> Phase 3 retention/archive
- [x] Test log pollution of production logs -> Phase 3 logging isolation
- [x] Policy allowlist strict-mode burn-down -> Phase 8 policy strictness
- [x] Coverage variability investigation -> Phase 7 consistency
- [x] Test artifact cleanup simplification -> Phase 3 cleanup

---

## 9. Working Notes

- Reliability-first default remains active.
- Do not increase default coverage timeout to mask hang/crash path; fix root causes.
- Any completed item should be closed here with date + evidence, then removed from backlog sections in `PLANS.md`/`TODO.md`.
