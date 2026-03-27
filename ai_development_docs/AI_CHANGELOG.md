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

### 2026-03-27 - V4 plan: coverage tests, Pyright policy, report linkify extract **COMPLETED**
- **Doc-sync**: Paired guides path drift + ASCII fixes; `analyze_documentation_sync` clean (addresses AI_PRIORITIES doc drift / Quick Win).
- **Inventory**: `DEPRECATION_INVENTORY` notes for `root_ruff_compat_mirror`; scripts/flaky backlog consolidated into approved [scripts/SCRIPTS_GUIDE.md](../scripts/SCRIPTS_GUIDE.md) + paired dev-tools guides (unapproved migration markdown removed).
- **Code**: `report_generation_linkify.py` extracted from `report_generation.py`; new `test_analyze_test_coverage.py`; Pyright owned/root exclude alignment + optional e2e JSON smoke; `test_commands_coverage_helpers` domain-parse edge case; `test_tool_wrappers_cache_helpers` signature test excludes pytest-temp false negative.
- **Docs**: Paired guides Section 9 portability criteria and Section 10 pydeps/vulture; TODO.md deferred Section 2.8 / test_config pointers.

### 2026-03-26 - V4 continuation: inventory, analyze_config tests, roadmap **COMPLETED**
- **Deprecation inventory**: Phrase-only `search_terms` for `root_ruff_compat_mirror` so legacy scans surface the Ruff root-compat bridge in `sync_ruff_toml.py` without noise from tests or `sync_root_compat` uses elsewhere; `LEGACY_REFERENCE_REPORT` refreshed (**1** file / **4** markers).
- **Tests**: `test_analyze_config.py` for `ConfigValidator`; `test_pyright_config_paths` exclude + Section 7.6 parity strategy note. **AI_PRIORITIES #2**: extended `test_audit_orchestration_helpers`, `test_commands_coverage_helpers`, `test_run_test_coverage_helpers` for `audit_orchestration.py`, `commands.py`, `run_test_coverage.py`. **Strict Tier 3**: lock-path tests use `patch.object` on `import development_tools as dt; dt.config` so `get_external_value` mocks match the runtime config binding after conftest loads.
- **Docs**: V4 Section 3.16 structure map + Section 6 snapshot; [TODO.md](TODO.md) dev-tools backlog scheduling block.

### 2026-03-25 - V4 continuation: coverage tests, reports, guides, portability **COMPLETED**
- **file_rotation / tests**: Extracted `path_looks_like_test_directory()` (module-level) from `create_output_file` so test isolation logic stays single-source; [tests/development_tools/test_file_rotation.py](tests/development_tools/test_file_rotation.py) fixes Tier-3 failures (patch `get_component_logger` for DIRECTORY_TREE safeguard; patch heuristic off for AI_STATUS isolation under `tmp_path`); per-test `@pytest.mark.unit`; Ruff-clean. `doc-fix --fix-ascii` re-run for CHANGELOG ASCII Quick Win.
- **V4 backlog hygiene**: `test_pyright_config_paths` Section 7.6 doc + extra test; scripts/refactor backlog text consolidated into V4 + paired guides Section 10 (removed ad-hoc `development_tools/docs/*.md` inventories).
- **Docs + tests**: `test_fix_documentation_links` main tests use `patch.object(links_module, 'DocumentationLinkFixer')` so `load_development_tools_module` and `main()` share the same module object; deleted unapproved ad-hoc inventory docs under `development_tools/docs/` (content merged into V4 + **DEVELOPMENT_TOOLS_GUIDE** / **AI_DEVELOPMENT_TOOLS_GUIDE** Section 10).
- **Config / coverage**: Fixed import cycle so `load_external_config()` runs before `constants.LOCAL_MODULE_PREFIXES` freezes - pytest-cov now receives all `core_modules` from JSON (not only `core`); lazy `AUDIT_TIERS` + `test_constants_config_import_order.py` (`@pytest.mark.unit` satisfies category marker policy).
- **Tests**: `test_audit_signal_state.py` (SIGINT multi-tap); extended `commands` lock-path config-failure and `run_test_coverage` shard wait/discover helpers; `test_pyright_config_paths` owned Pyright structural check; linkify + domain-summary tests; `format_repo_paths_as_markdown_links` + `test_service_utilities` coverage.
- **Reports**: AI_PRIORITIES "Review for guidance/details" linkifies `.md`/`.json` paths; path-drift **Top offenders** use markdown links with `/`; TEST_COVERAGE_REPORT domain section shows measured domains only plus an "in scope, not represented" note (no fake `0/0` rows); **Coverage Scope** still lists all `coverage.ini` sources.
- **Docs**: V4 snapshot (2026-03-25 metrics); paired guides **Section 10** (external tools evaluation + scripts backlog-removed dead `scripts/testing/flaky_detector.py` prose path); **version-sync** experimental docs; Section 6 legacy count alignment.
- **Doc hygiene**: Ran `doc-fix --fix-ascii`, `doc-fix --convert-links`, and `doc-sync` for AI_PRIORITIES Quick Wins (ASCII / unconverted links).
- **Tests**: `test_analyze_module_dependencies` + `test_analyze_unused_imports` use `patch.object(<loaded_module>, ...)` for subprocess/logger mocks so patches match `load_development_tools_module` under `sys.modules` churn (parallel Tier 3; fixes `test_cache_disabled`).
- **Note**: Full `tests/development_tools` run reported one flaky failure in `test_get_static_analysis_config_honors_external_overrides` under xdist/randomly; single re-run passed.

### 2026-03-24 - Dev tools: import boundary; Tier 3; V4 plan; portability; orchestration **Progressed**
- **Import-boundary (Tier 1)**: `analyze_dev_tools_import_boundaries`, `time_helpers` / `error_helpers`, policy Section 8-8.5; Option A import cleanup; fake service / strict-mode follow-ups.
- **Tier 3**: Contract enforced on `coverage_outcome` and per-track `classification`; invalidation logs at WARNING; no cache fallback in `_extract_cached_main_coverage_state`; strict/helper tests updated.
- **Docs / guides**: Removed/folded extra standalone files into paired guides; Section 9 taxonomy + Phase 2 evaluation (runtime_config/shims + legacy guide); `AI_DEVELOPMENT_TOOLS_GUIDE` link fixes; `doc-sync` writes `docs/jsons/analyze_documentation_sync_results.json`; reporting/AI_STATUS UX tweaks; Pyright + Ruff policy tests (`test_pyright_config_paths` + `tomllib` on owned + root `ruff.toml`); audit status test asserts status files on disk; module line threshold 1000; flaky cache-helper + extra coverage tests.
- **V4 roadmap (`AI_DEV_TOOLS_IMPROVEMENT_PLAN_V4.md`)**: Section 1.1/Section 1.3 reconciliation (60% vs ~80% advisory, monitoring, skips); Section 2.8 DEV_TOOLS report scoping **deferred**; Section 6 legacy pointers; Section 1.5 cache measurement recipe; Section 7.6 partial; Section 2.9 spot-check (no raw dict/list dumps in runner/orchestration `print` paths reviewed).
- **Tests**: `run_test_coverage` helpers, `commands._is_interrupt_signature`, `analyze_documentation` (topics/overlaps/corrupted artifacts), `test_config` static_analysis override patch via `get_static_analysis_config.__module__`, `test_audit_orchestration_helpers` (coverage/cache summaries, `_is_test_directory`, corrupt coverage JSON, infer-cache edge cases).

### 2026-03-23 - Legacy cleanup + AI Dev Tools Plan V4 **Progressed**
- **Legacy bridges retired**: (1) **tier3_coverage_outcome_compat_bridge**-Option A: invalidate caches lacking coverage_outcome (delete file on load); `--clear-cache` already clears it. (2) **backup_zip_compat_bridge**-removed zip read/restore/validate; directory-only backups. (3) **legacy_timestamp_parsing**-Option B: added `scripts/migrate_sent_messages_timestamps.py`; removed fallback in `_normalize_message_timestamps`; run migration before deploy.
- **AI Dev Tools V4**: Validation (3.2) fixed module-dependencies false warning; error-handling (3.6) uses `error_details`; DEPRECATION_INVENTORY.json created; coverage tests added; consolidated_report -> CONSOLIDATED_REPORT.md; `audit --dev-tools-only`; logging moved to logger.info only.

### 2026-03-22 - List consolidation; LIST_OF_LISTS Section 15; path drift; AI_PRIORITIES; analyze_function_patterns **Progressed**
- LIST_OF_LISTS Section 15: Next action steps documented and implemented. Static check `excluded_dirs`, `allowed_logging_import_paths` -> config. Error-handling keywords from config. Function registry `directory_descriptions`, `priority_order`, `decision_trees` -> config. Exclusions merge: `base_exclusions_additions`, `base_exclusions_removals`.
- **analyze_function_patterns**: entry_point_names, data_access_keywords, communication_keywords, decorator_names -> config `analyze_function_patterns`; projects override as needed.
- Path drift: LIST_OF_LISTS bare paths -> full `development_tools/shared/...`. AI_FUNCTION_REGISTRY regenerated; doc-sync path drift now 0.
- Ruff: SIM108, F401 fixes. Tests and Ruff pass. Re-run audit to refresh AI_PRIORITIES.

### 2026-03-21 - Coverage: --cov-append, all domains, and combine logic fix **COMPLETED**
- `run_test_coverage.py`: Added `--cov-append` to parallel pytest coverage run so pytest-cov enables data_suffix and each xdist worker writes its own `.coverage_parallel.<suffix>` file. Also expanded shard discovery to find all `.coverage_parallel.*`.
- **Critical fix**: Corrected inverted if/else in combine block-previously, when coverage files existed we only logged "Combining..." and skipped the actual combine; when no files existed we tried to combine (always failed). Now combine runs when files exist; warning only when none found.
- `generate_test_coverage_report.py`: Domains now derived from actual coverage data so TEST_COVERAGE_REPORT shows all measured domains (ai, communication, core, notebook, tasks, ui, user) instead of only CORE_MODULES.
- Re-run `python development_tools/run_development_tools.py audit --full --clear-cache` to regenerate coverage and validate.

### 2026-03-20 - Fix domain_mapper regression; resolve test and backup_health failures **COMPLETED**
- domain_mapper: Added SOURCE_TO_TEST_MAPPING instance attribute for backward-compat (tests use it).
- test_file_coverage_cache: Included development_tools_config.json in tool hash (domain_mapper reads from it).
- All 5 previously failing tests pass.
- analyze_backup_health: Extended "recent enough" threshold 8->14 days (config `backup_health.recent_days`). Weekly backups now pass; full Tier 3 audit completes.

### 2026-03-19 - Consolidate tool guide lists; implement list consolidation; LIST_OF_LISTS continuation **Progressed**
- Tool guidance data derived from canonical `tool_metadata._TOOLS`; fix_version_sync category lists now derived from `docs` by path prefix; exclusions from `get_exclusions()`.
- LIST_OF_LISTS continuation: Stale rows removed (Section 6, Section 11); Section 10 Status column; Section 9a consolidation candidates resolved/deferred; Pyright documented as two canonical sources; quick index; Section 12 sorted; Section 14 quick reference table. TIER_TITLES -> tool_metadata; generated function patterns -> constants.
- List consolidation: fix_version_sync derived lists; removed file_patterns.exclude_patterns; BASE_EXCLUDE_GLOBS -> standard_exclusions; DOCUMENTATION_GUIDE Section 4.1 config-canonical. Directory lists: `local_module_prefixes` canonical; scan_directories, core_modules, project_directories derived in constants.py. Config: `tool_commands.ruff_command` canonical; unused_imports/static_analysis derive; `test_markers.directory_to_marker` derived from categories when absent.
- Scan scope fix: Restored explicit `paths.scan_directories` in config so AI_PRIORITIES and analysis tools use full scope (ai, communication, core, tasks, tests, ui, user) when derivation falls back to defaults.
- Pyright warnings are cleared (`0 errors, 0 warnings`), and the dev-tools guidance tests were updated accordingly.
- [LIST_OF_LISTS.md](development_docs/LIST_OF_LISTS.md) now reflects that `TOOL_GUIDE` is derived (not a second catalog).
- Added `tests/__init__.py` to fix full-suite pytest collection (`development_tools.conftest` conflict). `_resolve_coverage_workers()` uses `sys.modules` lookup and instance-only concurrency flags so dev-tools audit completes successfully.

### 2026-03-18 - Tier 3 coverage: ignore_errors and data dir **COMPLETED**
- `coverage.ini` `[report] ignore_errors = true` - stale paths in `.coverage` no longer make `coverage json`/`html` exit 1 and fail full audit.
- Coverage data written under `development_tools/tests/`: `data_file = ${COVERAGE_DATA_DIR}/.coverage`; runner sets `COVERAGE_DATA_DIR` and absolute `--cov-config` so pytest/xdist workers write there by default (no project-root fallback needed).
- `get_all_user_ids()` (`core/user_management.py`): `_users_dir_for_listing()` honors patched `USER_INFO_DIR_PATH` for behavior tests; when the configured path still matches import-time `BASE_DATA_DIR/users`, uses runtime `TEST_DATA_DIR/users` under `MHM_TESTING=1` so xdist/stale-import listings stay correct. `_users_dir_for_listing` wrapped with `@handle_errors(..., default_return=None)`; `get_all_user_ids` returns `[]` if resolution fails.

### 2026-03-17 - Lists single-source plan, error handling Phase 1 (run_tests), Tier 3 coverage fix **Progressed**
- **Continue Lists Single-Source Analysis plan**: All todos done. Placeholder patterns from config only; path_drift.legacy_documentation_files in config example; emoji/non-ASCII in constants + fix_documentation_headings; PATH_STARTSWITH_NON_FILE derived from COMMAND_PATTERNS; EXPECTED_OVERLAPS/DOC_SECTION_WORDS; SPECIAL_METHODS/CONTEXT_METHODS in constants (exclusion_utilities + analyze_error_handling); CACHE_AWARE_TOOLS in tool_metadata; deprecation_inventory path and trigger_keywords canonical; LIST_OF_LISTS updated (principles, sections 7b/12, status table).
- **Error handling (run_tests.py)**: @handle_errors on normalize_test_id (Phase 1 medium); error_handling_exclude on nested canonicalize_nodeid/add_nodeid; try/except in those helpers; @handle_errors on _approximate_test_from_captured_output and _merge_run_results; typing and contextlib.suppress cleanups.
- **Tier 3 coverage**: run_test_coverage enters combine block when only .coverage exists so coverage_collected is set; .coverage fallback and no_parallel file-not-found messages downgraded to INFO when outcome is success.

### 2026-03-16 - Possible Duplicate Lists (Section 7.8) executed; path drift to zero, analyzer and audit fix **Progressed**
- **Plan 7.8 executed**: All five todos done-LIST_OF_LISTS.md as central inventory; audit tiers from one canonical source (measure_tool_timings, audit_orchestration); code/config lists aligned (commands, tools, deprecation path, paired_docs, SCRIPT_REGISTRY vs _TOOLS); paired-docs list drift check integrated into doc-sync; docs aligned to canonical lists.
- **Documentation drift**: Path references fixed in LIST_OF_LISTS, COMMUNICATION_GUIDE, DEVELOPMENT_TOOLS_GUIDE, TESTING_GUIDE so doc-sync reports 0 path-drift issues.
- **Path drift analyzer**: Whole-word keyword check by path segment in `analyze_path_drift.py`; constants and legacy-doc list in shared/constants and config. **Audit**: `utilities.py` sets `docs_sync_summary` and cache when `analyze_documentation_sync` runs so AI_PRIORITIES and saved results show correct doc-sync count after full audit.
- **Tests**: Path-drift tests use `development_docs/` layout and pass; Ruff clean.

### 2026-03-16 - Static analysis (Ruff/Pyright) clean, priorities split, workflow rule, test fixes **COMPLETED**
- **Static analysis**: Cleared all Ruff and Pyright findings. Ruff: fixed `analyze_dev_tools_import_boundaries.py` (typing.Dict/List -> dict/list), conftest and dev_tools conftest setattr + noqa B010 where needed for Pyright, `test_analyze_test_markers` Callable from collections.abc. Pyright: resolved 59->0 warnings (bot application_id, lock_state None guards, test type annotations/cast/setattr, FakeAnalyzer class, no_parallel reason comments).
- **AI_PRIORITIES and report generation**: Split static analysis into separate "Address Ruff findings" and "Address Pyright findings" items so each appears only when that tool has issues; removed "Deferred Ruff style rules" watch list. Updated test_report_generation_static_analysis to expect the new titles.
- **Workflow**: Added subsection 5.4 (DEVELOPMENT_WORKFLOW) and **Ruff and Pyright** (AI_DEVELOPMENT_WORKFLOW): when Ruff and Pyright conflict, prefer Pyright on type/attribute issues and use targeted Ruff noqa.
- **Tests**: Marked `test_scheduled_user_creation` and `test_create_account_persists_checkin_settings` with `@pytest.mark.no_parallel` and reason comments to fix parallel flakiness; added reason comments so test_no_parallel_marker_requires_reason passes.

### 2026-03-16 - Portability, exclusions, and analyze_pyright robustness **COMPLETED**
- **Portability (3.17)**: Test/discovery paths are config-driven via `paths.tests_dir` and `paths.tests_data_dir`. Updated `run_development_tools.py` (cleanup), `fix_project_cleanup.py`, `tests/run_test_coverage.py` (logs/tmp and pytest basetemp), and `ai_work/analyze_ai_work.py` to use `config.get_paths_config()` instead of hardcoded `tests/data`. Added `imports/analyze_dev_tools_import_boundaries.py` to flag non-approved `core.*` imports inside `development_tools/**`. Plan 3.17 tasks (config-driven paths, exclusions verification, import-boundary check, audit run) marked done.
- **Exclusions verification**: All scanners now use `should_exclude_file(...)` where applicable. Added usage in `generate_test_coverage_report.py`, `docs/analyze_path_drift.py` (code scan loop), `shared/export_docs_snapshot.py`, and `shared/service/commands.py` (_latest_mtime_for_patterns). Plan 3.17 exclusion note updated.
- **analyze_pyright**: Timeout and crash handling improved: `run_pyright()` catches `TimeoutError`; `main()` catches `TimeoutExpired`/`TimeoutError` and `Exception`, prints JSON unavailable result and exits 1 so the wrapper always gets parseable output. Tool wrapper logs stderr with a single-argument `logger.warning` (ComponentLogger-compatible). Audit orchestration logs each failed tool's `result["error"]` (error detail) so `main.log` shows the real cause on failure. Fixed Tier 2 indentation in `audit_orchestration.py` (else block).

### 2026-03-16 - Legacy backup cleanup and static analysis/test fixes **Progressed**
- **Backups**: Removed legacy `BACKUP_FORMAT=zip` compatibility from `core/backup_manager.py` so runtime backups are always directory-based, while still supporting read-only access to historical zip artifacts; updated backup behavior tests to assert against directory payloads (manifest, users/, config/) instead of zip files, and ensured age/count-based rotation works on the new model.
- **Static analysis/tests**: Brought pyright back to 0 errors by fixing `account_flow_handler` imports and type usage, tightening `task_edit_dialog` optional-access patterns, and resolving the remaining analyzer warning in `analyze_package_exports.py`; corrected regressions in Discord bot initialization tests introduced earlier this session and aligned dev-tools coverage helper expectations with the new backup behavior, so the Tier 3 audit's failing tracks now pass.

## Archive Notes
Older detailed entries live in `development_docs/changelog_history/` and remain the historical source of truth. Use [CHANGELOG_DETAIL.md](development_docs/CHANGELOG_DETAIL.md) for the latest detailed entries and the archive folder for month-split history.
