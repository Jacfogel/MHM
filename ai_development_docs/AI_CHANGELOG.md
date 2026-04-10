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

### 2026-04-10 - Tier 3 Bandit + pip-audit; Pyright in pyproject; coverage interrupt logging **COMPLETED**
- **Security/supply-chain**: Tier 3 runs [`analyze_bandit`](../development_tools/static_checks/analyze_bandit.py) and [`analyze_pip_audit`](../development_tools/static_checks/analyze_pip_audit.py) (JSON + report surfacing); `bandit` / `pip-audit` added to `requirements.txt`; paired guides Section 10 updated; V5 Section 5.4 - 4.2 marked complete.
- **Operational**: KeyboardInterrupt during coverage pytest subprocesses logs at **WARNING** (not ERROR) so intentional audit stops do not pollute `logs/errors.log` / system-signals noise.
- **verify_process_cleanup**: Pyright-clean `ProcessId` parse (prior same-day fix).
- **Pyright**: Root **`pyrightconfig.json`** removed; settings live in **`[tool.pyright]`** in [`pyproject.toml`](../pyproject.toml); default **`pyright_project_path`** is **`pyproject.toml`** ([`analyze_pyright.py`](../development_tools/static_checks/analyze_pyright.py), [`config.py`](../development_tools/config/config.py)); owned [`development_tools/config/pyrightconfig.json`](../development_tools/config/pyrightconfig.json) unchanged for alternate `--project`; policy tests + guides updated; DEPRECATION **`root_pyrightconfig_json`**.
- **Static-check cache**: [`tool_wrappers.py`](../development_tools/shared/service/tool_wrappers.py) `_compute_source_signature` now hashes **`pyproject.toml`** and owned **`development_tools/config/pyrightconfig.json`** / **`ruff.toml`** so Tier 3 Pyright/Ruff/Bandit caches invalidate when only tool config changes (fixes stale huge Pyright counts after config migration). Test: [`test_tool_wrappers_cache_helpers.py`](../tests/development_tools/test_tool_wrappers_cache_helpers.py).
- **Pyright override**: Live **`development_tools_config.json`** had **`static_analysis.pyright_project_path`** still set to removed root **`pyrightconfig.json`**, so **`analyze_pyright`** invoked Pyright without valid config (1000+ spurious findings under `archive/` / `scripts/`). Updated to **`pyproject.toml`**; [`analyze_pyright.py`](../development_tools/static_checks/analyze_pyright.py) falls back to root **`pyproject.toml`** when the configured path is missing.
- **Priorities remediation (same day)**: Raised `requirements.txt` floors (`aiohttp`, `requests`, `urllib3`, `PyNaCl`, `black`, `pygments`) + **pip-audit clean** in venv; **Bandit** scans first-party roots only (skips `.venv`/`archive` noise), reads **`[tool.bandit]`** in [`pyproject.toml`](../pyproject.toml) via `-c` (`bandit[toml]`), `md5(..., usedforsecurity=False)` where appropriate, targeted `# nosec` / `tree.com` on Windows for `generate_directory_tree`; Ruff SIM on `analyze_*` static helpers.

### 2026-04-09 - Dev-tools overlap + helper tests **COMPLETED**
- **V5 plan continuation**: `verify_process_cleanup` uses Windows **CIM** (`Win32_Process` command lines); `sync-todo --dry-run`; expanded `EXPECTED_OVERLAPS`; guides Section 10 decisions + Section 10.1 gap alignment; taxonomy + Pyright policy tests; V5 sections updated (Section 3.18 complete, Sections 4.1 / 5.x partial).
- Legacy scan now stays quiet for `fix_project_cleanup.py` (removed a false-positive "legacy path" phrase); [LEGACY_REFERENCE_REPORT.md](../development_docs/LEGACY_REFERENCE_REPORT.md) shows 0 issues.
- Added small portability coverage in `test_analyze_config.py` for absolute `get_project_root()` behavior.
- Added helper-focused tests for `commands.py`, `run_test_coverage.py`, and `audit_orchestration.py` (coverage metadata, path mapping + totals, Tier 3 scope finalization).
- Added `prerequisites` and `test suite structure` to `EXPECTED_OVERLAPS` so doc overlap warnings do not flag shared test-guide boilerplate.
- Executed V5 scripts backlog migration: added tracked replacements `development_tools/tests/flaky_detector.py` and `development_tools/tests/verify_process_cleanup.py`, wired CLI commands `flaky-detector` and `verify-process-cleanup`, added unit coverage, and updated V5/TODO/guides; `development_tools/shared/fix_project_cleanup.py` remains canonical cleanup owner while historical scripts paths are retired in deprecation inventory.
- Follow-up hardening: `verify_process_cleanup` in Tier 3 audits; `flaky_detector` wrappers + JSON normalization are **manual/CLI-only** (not in audit tiers) so nested pytest does not contend with coverage. `flaky_detector` handles subprocess timeout with structured JSON.
- `verify_process_cleanup` reporting: **AI_STATUS** snapshot line, **CONSOLIDATED_REPORT** section + executive WARN when Windows issues, **AI_PRIORITIES** only on WARN/issues (Windows); [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md](../development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md) **Section 3.18** tracks WMI/CIM command-line detection.

### 2026-04-08 - V5 dev-tools continuation (scoped reports + doc overlap) **Progressed**
- **DEV_TOOLS_*** reports: snapshot uses dev-tools package coverage when main Tier 3 tracks are skipped; scope notes + `DEV_TOOLS_PRIORITIES` / quick-command fixes; consolidated reference links for scoped runs; safe docstring-% parsing when coverage text is non-numeric ([report_generation.py](../development_tools/shared/service/report_generation.py), tests under `tests/development_tools/test_dev_tools_scoped_status_report.py`).
- **Dev-tools-only scope (follow-up)**: Priorities filter dependency patterns, unused-import obvious counts, doc quick wins (per-file), handler/no-doc signals, dependency-doc quick wins to `development_tools/`; paired-doc quick wins omitted; `DEV_TOOLS_STATUS` unused-import counts scoped; no "Full-repo test coverage" snapshot bullet when scoped. **`--clear-cache`**: audit clears `dev_tools` vs `full` cache trees only (`fix_project_cleanup.py` + `run_development_tools.py`); tests in `test_fix_project_cleanup.py`. Plan: [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md Section 7.18](../development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md).
- **Audit completion stdout**: `run_audit` prints **Dev Tools Status / Priorities / Consolidated Report** labels when `dev_tools_only_mode` is set ([audit_orchestration.py](../development_tools/shared/service/audit_orchestration.py)). **`test_cache_clear_alias_routes_to_clear_cache`**: mock `_clear_all_caches` accepts `cache_scope` ([test_integration_workflows.py](../tests/development_tools/test_integration_workflows.py)).
- **Global `--dev-tools-only`**: [run_development_tools.py](../development_tools/run_development_tools.py) sets `service.dev_tools_only_mode` when the parent parser consumes `--dev-tools-only` (so Tier 3 runs `generate_dev_tools_coverage` only and writes `DEV_TOOLS_*.md`); [cli_interface.py](../development_tools/shared/cli_interface.py) ORs subcommand flag with preset. Test: `test_global_dev_tools_only_sets_service_mode`. **Lint**: Ruff unused `refactor_summary` removed; Pyright `phase2_by_type` aggregation guarded against `None` from `to_int` ([report_generation.py](../development_tools/shared/service/report_generation.py)).
- **Overlap analyzer**: Numbered generic headings (`1. Purpose and Scope`, etc.) filtered like `EXPECTED_OVERLAPS` ([analyze_documentation.py](../development_tools/docs/analyze_documentation.py)).
- **Section 4.1**: External security/complexity tools stay manual (not in `requirements.txt`); guides Section 10 updated with 2026-04-08 evaluation note. **Section 1.5**: Benchmark recipe documented in [CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md); numbers still machine-local. **Section 3.17**: Entry points already `Path.resolve()` - verified, no code change.

### 2026-04-07 - Welcome tracking parallel flake fix **COMPLETED**
- `welcome_manager` load/save use `welcome_tracking_json_path()` so patched `BASE_DATA_DIR` matches I/O; tests isolate via `tmp_path` per test (welcome manager, handler, webhook behavior modules).
- Fixes xdist race on `tests/data/welcome_tracking.json` (`test_welcome_tracking_handles_missing_file_gracefully` and related). **Tests**: `pytest` on those three behavior modules with `-n 4` (pass).
- `welcome_tracking_json_path`: `@handle_errors(..., re_raise=True)`; Ruff F401 cleanup on behavior tests; `run_development_tools.py docs` for registry.
- **V5 continuation**: Scoped-only reads for tool JSON and Tier 3 aggregates/timings (removed flat/unscoped read fallbacks per Section 7.16); `DEPRECATION_INVENTORY` updated; ADR for directory taxonomy Phase 2 gate; DEV_TOOLS report headers + paired guides (overlap advisory, Radon pilot, scoped JSON examples); `analyze_config` resolved package root. Tests: `python -m pytest tests/development_tools/` (1161 passed).

### 2026-04-06 - Unified Tier 3 dev-tools coverage (V5 plan) **COMPLETED**
- **Behavior**: `run_test_coverage` (full-repo Tier 3) now includes `tests/development_tools/`, measures `development_tools`, writes `coverage_dev_tools.json` from main `coverage.json`, saves `generate_dev_tools_coverage`, and reports `dev_tools_test_outcome`; config `derived_prefix_excludes.core` no longer drops `development_tools` from `CORE_MODULES` for MHM.
- **Docs**: [`AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md`](../development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md), paired dev-tools guides + `dev_tools.mdc` updated; see [CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md) for file list and tests run.
- **Fix**: Dev-tools subset logging uses single-string `ComponentLogger.info`/`warning` messages; Ruff SIM114 in `_finalize_tier3_audit_scope`; guide link targets normalized under `development_tools/` + `doc-fix`/`doc-sync` clean.
- **Reports**: Full-repo `AI_PRIORITIES.md` no longer adds a separate **Raise development tools coverage** item; `development_tools` appears only in **Raise coverage for domains below target**. Dev-tools-only output still uses the dedicated priority + watch ([`report_generation.py`](../development_tools/shared/service/report_generation.py)).
- **Docs**: [`AI_DEVELOPMENT_TOOLS_GUIDE.md`](../development_tools/AI_DEVELOPMENT_TOOLS_GUIDE.md) uses repo-relative `development_docs/TEST_COVERAGE_REPORT.md` in backticks so path-drift no longer reports a false missing file.
- **Reports**: [`TEST_COVERAGE_REPORT.md`](../development_docs/TEST_COVERAGE_REPORT.md) domain table includes **`development_tools`** ([`generate_test_coverage_report.py`](../development_tools/tests/generate_test_coverage_report.py)); matches unified main coverage run.

### 2026-04-06 - Reduce dependency pattern risk (plan complete) **COMPLETED**
- **Scope**: [reduce_dependency_risk_70688c22.plan.md](../.cursor/plans/reduce_dependency_risk_70688c22.plan.md) - triaged mutual-import cycles (core infra, data/message cluster, communication flow triangle, UI dynamic list pair); verification and full-audit passes completed per plan.
- **Outcomes**: Cycles addressed with thin modules, deferred/`TYPE_CHECKING` imports, and narrower surfaces (no long-lived legacy bridges required for this slice). [MODULE_DEPENDENCIES_DETAIL.md](../development_docs/MODULE_DEPENDENCIES_DETAIL.md) and [analyze_dependency_patterns.py](../development_tools/imports/analyze_dependency_patterns.py) remain the evidence path; post-change **`circular_dependencies`** in [analysis_detailed_results.json](../development_tools/reports/scopes/full/analysis_detailed_results.json) is empty under typical full audits.
- **Deferred**: Optional Phase 2 "trim fan-in/out" on `ui_app_qt.py`, `conversation_flow_manager.py`, and `analytics_handler.py` was **cancelled** in the plan (follow up only if coupling stays noisy).

### 2026-04-04 - Docs ASCII, duplicate markers, notebook empty-result UX, sent_messages archiving **COMPLETED**
- **Changelog / audits**: `doc-fix --fix-ascii` + `doc-sync` on [CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md). `# not_duplicate` markers in [file_operations.py](../core/file_operations.py) (`create_user_files_top_level_json`), [account_creator_dialog.py](../ui/dialogs/account_creator_dialog.py) + [user_profile_dialog.py](../ui/dialogs/user_profile_dialog.py) (`keyPressEvent_dialog_escape`), [message_editor_dialog.py](../ui/dialogs/message_editor_dialog.py) (`message_editor_row_edit_delete`). [test_dialog_helpers.py](../tests/unit/test_dialog_helpers.py) for `handle_dialog_escape_enter_keys`.
- **Notebook**: [notebook_handler.py](../communication/command_handlers/notebook_handler.py) richer empty search/group/tag replies; `@handle_errors` + docstrings on `_format_no_*` helpers; ASCII hyphen in search line; `docs` registry refresh. [test_notebook_handler_pagination_formatting.py](../tests/unit/test_notebook_handler_pagination_formatting.py).
- **Sent messages**: [message_management.py](../core/message_management.py) passes `str(archive_path)` to `save_json_data` (archive writes were skipped). [USER_DATA_MODEL.md](../core/USER_DATA_MODEL.md) retention; [TODO.md](../TODO.md) item removed. [test_message_management.py](../tests/core/test_message_management.py) (`TestArchiveOldMessages`).
- **Validation / dedupe**: [user_data_validation.py](../core/user_data_validation.py) `is_valid_user_id` now enforces length and safe charset (matches former handler rules); [base_handler.py](../communication/command_handlers/base_handler.py) and [user_data_updates.py](../core/user_data_updates.py) delegate to it. Notebook pin/archive via `_apply_entry_ref_mutation`. [test_user_data_validation_user_id.py](../tests/unit/test_user_data_validation_user_id.py).
- **Tests**: [test_audit_status_updates.py](../tests/development_tools/test_audit_status_updates.py) uses `monkeypatch.setenv` for `DISABLE_LOG_ROTATION` (satisfies [test_no_direct_env_mutation_policy.py](../tests/unit/test_no_direct_env_mutation_policy.py)).
- **Notebook error handling**: [notebook_handler.py](../communication/command_handlers/notebook_handler.py) `@handle_errors` with default `InteractionResponse` on `_handle_pin_entry` and `_handle_archive_entry` (audit + single wrapping layer); shared `_apply_entry_ref_mutation` stays undecorated. `docs` registry refresh as needed.

### 2026-04-03 - Doc ASCII, doc-sync, ops checks, user_data_read scenario tests **COMPLETED**
- `doc-fix --fix-ascii` on [CHANGELOG_DETAIL.md](development_docs/CHANGELOG_DETAIL.md) (hyphens for list punctuation); `doc-sync` PASS; `audit --quick` refreshed status so Doc Sync and ASCII show clean.
- Ops: no wake-timer `Register-ScheduledTask` noise in errors.log; scheduler.log 2026-04-03 01:00 cycle shows healthy wake timer maintenance; `backup verify` exit 0 and weekly checks PASS.
- TODO.md: removed completed wake-timer confirmation and weekly-backup monitoring checklist blocks after verification.
- Core coverage: [tests/core/test_user_data_read_scenarios.py](tests/core/test_user_data_read_scenarios.py) exercises [core/user_data_read.py](core/user_data_read.py) (`ensure_unique_ids`, `get_user_data` validation and `fields`, metadata, `normalize_on_read`, `load_and_ensure_ids`).
- `--clear-cache`: [fix_project_cleanup.py](development_tools/shared/fix_project_cleanup.py) clears scoped **full** audit JSON, `reports/scopes/full/`, `reports/archive/`, and legacy aggregate paths (not just **dev_tools** scope); test `test_cleanup_tool_cache_includes_full_scope_and_reports_archive`; guides + dev_tools rule updated.
- Tier 3 xdist: `test_reminder_followup_handles_task_without_due_date` unique user + canonical id + flow state cleanup (avoid shared `test_no_due_date` collision).

### 2026-04-02 - Headless service startup and process classification **COMPLETED**
- Headless launcher uses [core/launch_env.py](core/launch_env.py) for `resolve_python_interpreter` / `prepare_launch_environment` and always sets `MHM_HEADLESS_SERVICE` / `MHM_SERVICE_TYPE` (previously only when `.venv/Scripts` existed, so Linux/macOS and some Windows layouts never got markers).
- UI-started backend sets `MHM_UI_MANAGED_SERVICE` / `MHM_SERVICE_TYPE`; `get_service_processes` prefers env markers and drops the brittle `"ui" in path` heuristic that misclassified paths like `rapidui`.
- Behavior tests: UI+headless classification uses `core/service.py` + env; new case for `rapidui` folder path.
- **Admin panel channel status**: Email/Discord running/stopped labels use `LOG_EMAIL_FILE` / `LOG_DISCORD_FILE` + merged tails from `LOG_BACKUP_DIR` (TimedRotating backups), plus email IMAP/send activity heuristics; fixes false "Email: Stopped" after log rotation or custom log paths.
- **Tier 3 / dev tools import fix**: [core/headless_service.py](core/headless_service.py) no longer imports top-level `run_mhm` (not on `sys.path` when running `development_tools/tests/run_test_coverage.py`), which was causing immediate `ModuleNotFoundError` and `run_test_coverage` -> `coverage_failed`.
- **Audit queue**: `@handle_errors` on UI channel log merge helpers; xdist-safe Discord + user-management tests; Ruff; ASCII doc-fix and function registry regen (`docs`, doc-sync).

### 2026-03-31 - Doc-sync, DEV_TOOLS placeholders, test/parse fixes **COMPLETED**
- Audit artifact read-fallback backlog: detailed table lives under V5 Section 7.16 (not AI_LEGACY); comments/docs retargeted; Pyright warnings cleared in `utilities.py` optional `details` handling.
- Workflow section 10: repo-relative paths; ASCII cleanup; Section-sign cleanup in changelogs.
- Placeholder `development_tools/DEV_TOOLS_*.md` so path drift passes; overwritten by dev-tools-only audit.
- **Status markdown links**: `report_generation._markdown_href_from_dev_tools_report` so `AI_STATUS` / `DEV_TOOLS_STATUS` / consolidated reference links resolve from `development_tools/` (e.g. `../development_docs/...`, sibling `reports/scopes/...`).
- Task handler: `_add_one_calendar_month` uses `@handle_errors` plus safe month advance; Discord behavior test `test_discord_complete_task_by_name_variation` rebuilds user index + factory UUID fallback for xdist.
- Output storage tests: expect `jsons/scopes/full/` for saves/archives; archiving-failure test matches move-then-write semantics.
- **Report / cache**: `_extract_documentation_metrics` and `_extract_error_handling_metrics` keep standard `{summary, details}` in `results_cache` instead of replacing with flat metrics (fixes `[DATA SOURCE] ... missing 'summary' dict` during status generation after audit).
- **System signals**: `analyze_system_signals` resolves `analysis_detailed_results.json` from `reports/scopes/{full|dev_tools}/` or legacy `reports/` so "No recent audit data found" matches scoped audit output.
- **Tier 3 status text**: Scope-skipped tracks (`not_run_this_audit_scope`) are omitted from `AI_STATUS` / consolidated Tier 3 sections instead of showing redundant "skipped" lines.
- **Legacy audit paths**: V5 Section 7.16 table (backlog) + `LEGACY COMPATIBILITY` comments on aggregate/timing fallbacks and `legacy_flat_jsons_dir`; artifact-storage detail removed from `AI_LEGACY_COMPATIBILITY_GUIDE` (pointer to V5 only).
- Tier 3 Windows: `run_script` isolates `analyze_pyright` / `analyze_ruff` process groups; static-check scripts catch `KeyboardInterrupt` during tool subprocess so audits get JSON instead of uncaught tracebacks when SIGINT propagates.
- Dev-tools-only audit: `_get_status_file_mtimes` uses `DEV_TOOLS_*.md` paths so report finalization does not false-warn about `AI_*.md` mtimes when those files were not written.
- **Audit artifact scope**: `jsons/scopes/<full|dev_tools>/` and `reports/scopes/<full|dev_tools>/` for writes; legacy flat `jsons/` remains read-fallback for full scope; `--clear-cache` clears scoped trees; unused-imports CLI loads scoped results if flat file missing.

### 2026-03-30 - Tier 3 scope split + portability/docs **COMPLETED**
- **V5 Section 1.9**: Full `audit --full` runs main `run_test_coverage` only; `audit --full --dev-tools-only` runs `generate_dev_tools_coverage` only (no `generate_test_coverage_report` in that pass). Tier 3 outcome + status sections mark skipped tracks; `DEV_TOOLS_*.md` vs full-repo outputs documented in paired workflow Section 10.
- **`analyze_config`**: Single `_PACKAGE_ROOT` fallback anchor; unit test for relative `get_project_root()`.
- **Guides**: `PYRIGHT_ERROR_COUNT_MAX_DELTA` noted for optional Pyright parity (AI + human dev-tools guides).
- **Benchmark note**: Section 1.5 `Measure-Command` recipe recorded in CHANGELOG_DETAIL for future domain-cache timing.

### 2026-03-29 - Config consolidation + inventory legacy patterns **COMPLETED**
- **Unused imports tooling (plan 5.1)**: Confirmed all-zero `UNUSED_IMPORTS_REPORT` matches Ruff (no project `F401`) plus `cache_only` runs; report summary now shows backend/cache/re-lint counts and `--clear-cache` hint; batch backends key issues by `Path.resolve()`; integration test `test_scan_minimal_project_finds_ruff_f401`. See [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md) Section 5.1.
- **Constants / exclusions alignment**: `constants.derived_prefix_excludes` (scan/core/project derivation); top-level `test_markers` with `TEST_*` re-exported from `get_test_markers_config()`; legacy `constants.test_category_markers` etc. deprecated (warning); `path_drift.ignored_path_patterns` + `get_path_drift_config()`; slimmer portable `standard_exclusions` defaults (`tests/ai/results`, `mhm.egg-info` -> config); `tests/development_tools/test_constants_config_alignment.py`; LIST_OF_LISTS Section 6/Section 9b/Section 10/Section 13/Section 14.
- **Doc-sync PASS**: LIST_OF_LISTS path-qualified refs (Section 13 table: `config.py` -> `development_tools/config/config.py`); paired changelogs ASCII clean; `analyze_documentation_sync_results.json` status PASS.
- **Function registry defaults**: `AUDIT_FUNCTION_REGISTRY` in `development_tools/config/config.py` holds portable directory/entry-point/common-ops text; JSON only for `decision_trees` + overrides; `development_tools/functions/generate_function_registry.py` no longer duplicates fallbacks; LIST_OF_LISTS Section 12b resolutions.
- **Example config parity**: `development_tools_config.json.example` matches live top-level keys; `get_file_patterns_config()` + dropped redundant JSON `file_patterns`; exclusions overlap note in live JSON; `test_config` parity test.
- **DEPRECATION_INVENTORY** holds `legacy_scan_patterns`; dev-tools JSON trimmed; analyzers derive `default_docs`, core-system files, coverage test dir, registry priority dirs, validation/analyze_ai_work thresholds.
- **LIST_OF_LISTS** section 12b flags config blocks for future ROI review; sections 3 and 13 updated for canonical locations.
- **Dev-tools tests**: `patch.object` on `load_development_tools_module` targets for `generate_directory_tree`, `fix_project_cleanup`, and `fix_documentation_headings` (`config` / `DEFAULT_DOCS` / `DocumentationHeadingFixer`) - avoids patches missing the importlib-loaded module under parallel/coverage (`audit --full` Tier 3).
- **Task behavior tests**: autouse `monkeypatch` on `core.user_item_storage.get_user_data_dir` so task JSON stays under each test's `test_path_factory` root (fixes Tier 3 parallel failures from I/O under `tests/data/users/...`). **Docs**: ASCII cleanup in paired changelogs; repo-relative links in [SYSTEM_AI_GUIDE.md](../ai/SYSTEM_AI_GUIDE.md); unconverted-link + LIST_OF_LISTS path-drift cleanup (`CONFIGURATION_REFERENCE` link text; qualify `config.py` as `development_tools/config/config.py`); `doc-sync` PASS; root `custom.md` removed and gitignored (tree-generator artifact).

### 2026-03-28 - V5 plan: legacy report clean, DEV_TOOLS report scope, Pyright venv **COMPLETED**
- **Inventory / legacy**: `root_ruff_compat_mirror` no longer injects grep `search_terms` (bridge still listed); `LEGACY_REFERENCE_REPORT` can show **0** hits while the entry documents exit criteria.
- **Reports**: Dev-tools-only audits label `DEV_TOOLS_*.md` outputs, scope blurbs, source line with `--dev-tools-only`, and drop full-repo domain-coverage priority from dev-tools priorities; `core.py` duplicate `_tools_run_in_current_tier` line removed.
- **Portability / Pyright**: `run_dev_tools.py`, `fix_legacy_references.py` resolve bootstrap paths; `generate_function_registry` rotation uses shared `project_root`; owned `pyrightconfig.json` declares repo venv via `venvPath`/`venv`.
- **Follow-up**: Section 1.5 cache benchmark numbers remain local - see CHANGELOG_DETAIL for the PowerShell `Measure-Command` pairing recipe.

### 2026-03-27 - V4 plan + V5 roadmap continuation (docs, casing, portability slice) **COMPLETED**
- **V5 backlog**: [TODO.md](TODO.md), [PLANS.md](development_docs/PLANS.md), [LIST_OF_LISTS.md](development_docs/LIST_OF_LISTS.md), paired dev-tools guides now point at [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md) for current work; V4 remains historical checkboxes.
- **Reports**: Git tracks `development_tools/CONSOLIDATED_REPORT.md` (case-normalized) to match config; `.cursor/rules/dev_tools.mdc` updated.
- **Bridge / inventory**: `sync_ruff_toml` CLI uses component logger (not `print`); `DEPRECATION_INVENTORY` `root_ruff_compat_mirror` search_terms trimmed; `analyze_config`/`generate_function_registry` portability tweaks; optional Pyright e2e delta via `PYRIGHT_ERROR_COUNT_MAX_DELTA`; [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md](development_tools/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V5.md) Section 1.2 Section 4.1 Section 7.6-7.7 Section 5.8 updates.
- **Earlier same day**: Doc-sync + `report_generation_linkify` extract + Pyright policy tests + inventory notes + scripts guide consolidation (see CHANGELOG_DETAIL).

### 2026-03-26 - V4 continuation: inventory, analyze_config tests, roadmap **COMPLETED**
- **Deprecation inventory**: Phrase-only `search_terms` for `root_ruff_compat_mirror` so legacy scans surface the Ruff root-compat bridge in `sync_ruff_toml.py` without noise from tests or `sync_root_compat` uses elsewhere; `LEGACY_REFERENCE_REPORT` refreshed (**1** file / **4** markers).
- **Tests**: `test_analyze_config.py` for `ConfigValidator`; `test_pyright_config_paths` exclude + Section 7.6 parity strategy note. **AI_PRIORITIES #2**: extended `test_audit_orchestration_helpers`, `test_commands_coverage_helpers`, `test_run_test_coverage_helpers` for `audit_orchestration.py`, `commands.py`, `run_test_coverage.py`. **Strict Tier 3**: lock-path tests use `patch.object` on `import development_tools as dt; dt.config` so `get_external_value` mocks match the runtime config binding after conftest loads.
- **Docs**: V4 Section 3.16 structure map + Section 6 snapshot; [TODO.md](TODO.md) dev-tools backlog scheduling block.

## Archive Notes
Older detailed entries live in `development_docs/changelog_history/` and remain the historical source of truth. Use [CHANGELOG_DETAIL.md](development_docs/CHANGELOG_DETAIL.md) for the latest detailed entries and the archive folder for month-split history.
