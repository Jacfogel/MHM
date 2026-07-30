# AI Changelog - Brief Summary for AI Context
> **File**: `ai_development_docs/AI_CHANGELOG.md`
> **Audience**: AI collaborators (Cursor, Codex, etc.)
> **Purpose**: Lightweight summary of recent changes
> **Style**: Concise, essential-only, scannable
> **See [development_docs/CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md) for the full history**

## Overview
This file is a lightweight summary of recent changes for AI collaborators. It provides essential context without overwhelming detail. For the complete historical record, see [CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md).

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

### 2026-07-29 - NOTES_PLAN refresh; `|` separators; group disambiguation; `!edit` **COMPLETED**
- Validated/refreshed NOTES_PLAN + PLANS notebook status (help polish, AI context privacy remaining).
- Parser: title/body accepts newline / `|` / `:`; append strips optional leading `|`.
- Group ambiguity: `!setgroup` aliases; bare `!group` set only for short-ID/UUID; multi-word groups list; anchored `quick note(s)`.
- `!edit` sessions: `FLOW_ENTRY_EDIT` replace-body flow with cancel/skip/timeout leaving entry unchanged.
- Fix: `edit_entry` no longer steals `edit profile`; function registry regenerated; changelog ASCII cleaned.

### 2026-07-28 - Close V6 B-012 / B-013; archive V6 and Google Health plans **COMPLETED**
- B-013: Combined `analyze_gap*` declined; Section 10.1 map + `AI_PRIORITIES` is triage.
- B-012: Radon/pydeps uniqueness spikes duplicated existing complexity/coupling signals; pre-commit and deeper Ruff declined. Vulture remains the only B-012 Tier 3 add.
- Archived [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V6.md](../archive/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V6.md); residual **B-016** carried in PLANS Section 6.4 / TODO. Live triage = `AI_PRIORITIES.md`.
- Archived [HEALTH_INTEGRATION_PLAN.md](../archive/HEALTH_INTEGRATION_PLAN.md); monitoring in GOOGLE_HEALTH_GUIDE; deferred leftovers in TODO; PLANS Section 8 updated.
- TODO.md ASCII/link hygiene via `doc-fix` (`--fix-ascii`, `--convert-links`) + `doc-sync`.
- Docs: TODO, PLANS, paired DEVELOPMENT_TOOLS guides, HOW_TO_RUN, LIST_OF_LISTS, legacy guide links retargeted; radon/pydeps stay optional manual recipes (not in requirements).

### 2026-07-27 - Vulture triage: real fixes + noise excludes **COMPLETED**
- Nightly CI: `.gitignore` `**pytest**` was ignoring `coverage_pytest_argv.py` (ModuleNotFoundError). Narrowed to temp dirs + `**/pytest_*.log`; module now trackable.
- Nightly CI: fixed parallel timeout in account-management integration test - TestUserFactory username lookup uses unlocked test JSON reads (and v2 unwrap) instead of locked `safe_json_read` scans under worker-store contention.
- Triaged 647 findings: ~384 generated unused imports + ~255 pytest fixture "unused vars" were false positives; real hits fixed.
- Critical: restored `TestAccountHandlerBehavior` class (31 tests were unreachable / uncollected after helper return).
- Cleanup: Discord bot duplicate unreachable return; unused typing imports in `backup_manager`; protocol unused args in `SafeFileContext.__exit__`; webhook placeholder params referenced in debug log.
- Portability: `analyze_vulture` no longer hardcodes project paths; uses shared `get_exclusions("vulture")` / `should_exclude_file`; MHM `tests/*` skip lives in `exclusions.tool_exclusions.vulture`. Removed `*/ui/generated/*` from portable exclusion defaults (keep generic `*/generated/*`). Underscored unused signal `frame` in `core/service.py`.
- Follow-up: Ruff py310 f-string escape in `analyze_vulture` fixed; ASCII cleaned in CHANGELOG_DETAIL.
- Vulture PASS (0). Paired guides Section 10 updated.

### 2026-07-26 - V6 deferred trio + B-015 coverage helpers **COMPLETED**
- B-013: gap-category map folded into DEVELOPMENT_TOOLS_GUIDE Section 10.1 (standalone matrix removed; no `analyze_gap*` tool).
- B-012: Tier 3 `analyze_vulture` (min-confidence 80); Radon/pydeps stay manual.
- B-016 MVP: `--audit-scope` -> `scope_*` storage + Tier 2 scan-dir tools; no AI_* overwrite.
- B-015 slice #4: coverage argv/shard/domain-cache + report scope helpers extracted.
- AI_PRIORITIES cleanup: path-drift/ASCII/address on scoped status + guides; Ruff UP035/SIM110 on B-015 helpers; `pyasn1>=0.6.4` floor (pip-audit clean).
- Fixed Tier 3 test failures (scoped MagicMock + regenerated `tool_cache_inventory.json` for `analyze_vulture`); vulture always excludes `tests/data` and similar ephemeral paths.
- Removed standalone gap matrix doc; triage map lives in DEVELOPMENT_TOOLS_GUIDE Section 10.1 only.

### 2026-07-23 - Sync->async bridge, check-in logging, errors.log routing **COMPLETED**
- Managed event loop always runs on a background thread; sync bridge uses `run_coroutine_threadsafe` when the loop is running (fixes concurrent `run_until_complete` / "loop already running").
- Scheduled check-in success log gated on actual send result.
- `setup_error_handler_logging()` dual-writes `mhm.error_handler` plus bootstrap raw loggers (`network_probe`, `time_utilities`, `config`) ERROR/CRITICAL to `errors.log`.
- `channel_orchestrator` / handlers / AI+UI extras alias via `COMPONENT_NAME_ALIASES`; `_log_error` collapsed to one structured ERROR line.
- Static logging check rejects unknown `get_component_logger("...")` names (parses `CANONICAL_COMPONENT_NAMES` + aliases from `logger.py`).
- Failed check-in/message/confirmation/Discord-reply sends raised to ERROR; paired logging/error-handling docs corrected.
- Audit cleanup: error-handling on logger helpers, function registry, ASCII/heading numbering, Pyright warnings from this slice.

### 2026-07-20 - Nightly CI logging check + marker **COMPLETED**
- Static logging check falls back to committed `.example` when live config is missing; example allowlist restored for core logger/config files.
- Registered `development_tools` pytest domain marker for `--strict-markers` collection.
- V6 deferred trio: B-011 coverage-cache numbers (cold **298.67s** / build **326.99s** / hit **0.91s**); B-014 keep memory profiler standalone/local; B-010 TODO sync workflow recipe in paired guides.
- V6 B-009: system signals drops doc-sync re-derive; critical_alerts from severity. B-015 first extract: `coverage_json_helpers` + `report_generation_tier3_helpers` (no legacy shims).
- V6 B-015 slice #2: `coverage_outcome_classification` (track/cache outcomes, Windows/xdist/infra detectors, `strip_xdist_args`); regenerator methods thin-delegate.
- V6 B-015 slice #3: AI_STATUS / AI_PRIORITIES / CONSOLIDATED builders moved to dedicated mixins; `report_generation.py` composes them (no legacy shims).
- Cleared post-split F401/Ruff noise: unused imports removed from report builder modules; linkify tests import `report_generation_linkify` directly.

### 2026-07-19 - V6 residual slice (perf + noise) **COMPLETED**
- B-001: `test_fix_project_cleanup` uses `tmp_path` (no demo copytree); module-scoped demo fixtures for docs-workflow / scoped-status / static-analysis report / cache-helpers; path-drift leftovers -> `tmp_path`; archive module + legacy mutators marked `slow` for Tier 3 quick profile.
- B-001 re-profile: `run_tests.py --mode development_tools --durations-all` -> **1591 passed / 83.94s** wall (was ~195s on 2026-07-18); cleanup copytree gone from top setups.
- B-006: dependency-doc placeholder modules summarized at INFO; WARNING list limited to new/missing/changed.
- B-007: example-marker advisory skips fenced blocks and opens on prose `Examples:` labels.
- B-008: Discord-spec boilerplate headings added to `EXPECTED_OVERLAPS`. V6/TODO retargeted; coverage stays outside V6 active driver.
- Cleared AI_PRIORITIES example-marker hints: renamed neutral `Examples:`/`Example:` labels in DOCUMENTATION_GUIDE, AI_DEVELOPMENT_TOOLS_GUIDE, TESTING_GUIDE; prose openers now end at any ATX heading. ASCII compliance already CLEAN.

### 2026-07-18 - LIST_OF_LISTS currency; V6 plan status refresh **COMPLETED**
- B-003/B-004 portability: emptied MHM package roots from portable code defaults (Ruff/Pyright shards, Bandit roots, channel-logger allowlist); MHM trees live in project JSON + `.example`. Renamed pip-audit skip env to `DEV_TOOLS_PIP_AUDIT_SKIP` only (`MHM_PIP_AUDIT_SKIP` removed), renamed pip-audit/pytest temp cache prefixes, and external-repo smokes (Bandit `.` fallback, Ruff monolithic fallback, subprocess `audit --quick`).
- Fix Tier 3 flake: `test_analyze_unused_functions_finds_uncalled_helper` now passes explicit `project_root` / `scan_directories` / `apply_exclusions=False` so empty global `paths.scan_directories` from other tests cannot yield zero files.
- B-004: removed nested `development_tools/config/pyrightconfig.json`; Pyright SSOT is `pyproject.toml` `[tool.pyright]` only (cache deps, policy tests, guides, deprecation inventory updated).
- Cleared AI_PRIORITIES: `click>=8.3.3` for CVE-2026-7246; TODO.md ASCII; historical changelog hrefs to removed nested Pyright path demoted to plain backticks.
- LIST_OF_LISTS verified against live code; fixed duplicate `legacy_cleanup` JSON key; PLANS Section 2 + cursor rules inventory path aligned to `config/jsons/`.
- Catalog drift fixed: `EXPECTED_TOOLS` uses `analyze_system_signals`; `generate_dev_tools_coverage` catalogued in `_TOOLS`; subset policy test added; tool_guide basename guard skips script-registry excludes.
- Cleared AI_PRIORITIES doc-sync items: path drift, ASCII, registry regen; `doc-sync` PASS.
- LIST_OF_LISTS Section 7c documents cache/suite/static-analysis/backup policy lists.
- Deferred SSOT closed: audit_tiers group maps, paired-docs prose sync in doc-sync, COMMAND_GROUPS guide parity test, PRODUCT_LIST_OF_LISTS.md.
- Parallel-track flake fix: xdist worker-isolated `tests/data/xdist_*`; force-overwrite inherited `TEST_DATA_DIR`; actionability tests bind runtime data dir; `is_automated_messages_enabled` resolves usernames; audit_tiers TypedDict clears Pyright warnings.
- Refreshed [AI_DEV_TOOLS_IMPROVEMENT_PLAN_V6.md](../archive/AI_DEV_TOOLS_IMPROVEMENT_PLAN_V6.md) Section 1.1 / B-001-B-005 / B-018 against 2026-07-18 audit + codebase (coverage-first next slice; perf residual; portability residual; domain markers maintenance; pip CVE closed).
- B-002 coverage slice #1: branch tests for `report_generation` / `audit_orchestration` / `tool_wrappers` helpers (113 passed in the three extended test modules).
- Fixed Tier 3 parallel flakes: unique user IDs for task-stats parity, admin provisioning, and Google Health reconnect-notice sync; ran `doc-fix --fix-ascii` on changelogs.
- B-001 residual: module-scoped `temp_project_copy` in static-analysis wrapper + unused-imports report tests; legacy cleanup left function-scoped (mutates demo tree).
- Full `development_tools` durations profile: 1564 passed in ~3:15 wall; setup still dominated by function-scoped mutators (`fix_project_cleanup`, `output_storage_archiving`, `legacy_reference_cleanup`).
- B-002 coverage slice #2: deeper chokepoint edges plus new `test_analyze_unused_functions.py` (closes the 0% analyzer gap from wrapper-only mocks); 129 passed across four modules. V6 B-002 notes retargeted to ~65.6% live snapshot.
- B-002 coverage slice #3: `commands` / `data_loading` helpers (coverage summary/insights, canonical metrics, doc-subcheck freshness/cache-hit, execute_task/cleanup/status skip); 121 passed across three extended modules.
- Doc correction: coverage is refreshed only by `python development_tools/run_development_tools.py coverage` (not `audit --full`). Updated HOW_TO_RUN, DEVELOPMENT_WORKFLOW (paired with AI_*), DEVELOPMENT_TOOLS_GUIDE, V6/TODO, and generated-status follow-up strings in `report_generation.py`.
- Cleared AI_PRIORITIES quick wins: path-drift bare `TEST_COVERAGE_REPORT.md` refs -> `development_docs/...`; Pyright on new helper tests (0/0); TODO.md ASCII via `doc-fix --fix-ascii`; `doc-sync` PASS.

### 2026-07-17 - Session fact recall; archive completed product-AI plan **COMPLETED**
- Contextual prompts merge session + disk conversation history and label prior user turns clearly; cache skipped when prior turns exist.
- `conversation_coherence` reinforces stated facts (favorite color/name/food) when follow-ups omit them; `reply_rules.txt` updated.
- Durable routing/prompt contracts recorded in `ai/SYSTEM_AI_GUIDE.md`; completed plan moved to `archive/PRODUCT_AI_RESPONSE_INFLUENCE_AUDIT.md`.
- Live AI suite: 66 pass / 2 partial / 0 fail (T-7.1 PASS).

### 2026-07-15 - Compact planner prompt; planner default on; template/hub parity **COMPLETED**
- Planner prompt is a short ACTION-first template + compact action list; calls LM Studio directly; free-text entities must appear in the user message.
- `AI_ACTION_PLANNER_ENABLED` defaults to `true`; template/hub parity added for `create_task_from_template`, `list_task_templates`, `show_create_hub`.
- Product AI audit Phases 4-6 / slice 9.4 marked complete.

### 2026-07-14 - Plain-language wellness messaging; richer sleep quality + active minutes **COMPLETED**
- Personalized prompts use plain sleep/activity phrases (no `sleep_recovery=high` / "wearable wellness" parroting).
- New derived fields: `sleep_quality` (efficiency + deep/REM) and `active_intensity` (active minutes) feed personalization rules + message/chat context.
- User-facing effect: messages can mention solid/lighter sleep quality and higher/lighter active effort without raw metrics.

### 2026-07-13 - Register `integrations` pytest domain marker; strip two-line wellness sign-offs **COMPLETED**
- Registered `@pytest.mark.integrations` in `pytest.ini` and conftest hooks so `--strict-markers` collection no longer crashes on health context builder tests.
- Domain marker docs now list `integrations` alongside other product packages.
- **Fix (personalized sign-offs)**: `strip_letter_signoffs()` now removes split closings (`Best wishes,` + bare `Assistant` / `MHM Bot` on the next line), not only single-line `Take care, [Your Name]`.

### 2026-07-12 - Use coarse Google Health signals in wellness fallbacks **COMPLETED**
- When `message_guidance` is empty or confidence is `low`, wellness replies now use coarse signal fields via `build_user_facing_signal_wellness_snippet()` in [`health_context_builder.py`](../core/health_context_builder.py).
- Check-in fallback cites partial metrics and can combine check-in + health reads.
- **Nightly CI fix**: full-suite orchestration timeout now allows parallel + no_parallel phases (~42 min); writes fallback `run_test_suite_nightly_results.json` when the subprocess is killed so GitHub Actions artifacts include failure context.
- Audit hygiene: doc path drift fixed; docstrings/`@handle_errors` on wellness helpers; pytest markers; Ruff SIM103; `doc-sync` PASS.

### 2026-07-11 - Wellness replies use Google Health when check-ins are weak **COMPLETED**
- Removed `how am i doing` from the rule-parser `status` intent so wellness questions reach contextual chat.
- Added shared health-wellness helpers in [`health_context_builder.py`](../core/health_context_builder.py): `format_health_guidance_for_user_reply`, `health_wellness_snippet_from_context`, `context_has_usable_health_wellness`.
- Extended [`wellness_status.py`](../ai/chat/wellness_status.py) and [`checkin_summary.py`](../ai/fallback/checkin_summary.py) to use `health_guidance_summary` / recent signals when check-in data is weak or missing; coordinator and envelope fallback pass health context through.
- Unit tests in `test_wellness_status.py`, `test_context_analytics_shared_source.py`, and `test_health_context_builder.py`.

### 2026-07-10 - Phase 0 reconciliation and planner routing parity **COMPLETE (slice 9.4 LM Studio gate)**
- Reconciled [`PRODUCT_AI_RESPONSE_INFLUENCE_AUDIT.md`](../archive/PRODUCT_AI_RESPONSE_INFLUENCE_AUDIT.md): Phase 0 COMPLETE; slice 9.4 items 1-7 COMPLETE (LM Studio gate met).
- Documented hybrid routing policy: rule-parser-first for high-confidence structured commands; planner on low-confidence when `AI_ACTION_PLANNER_ENABLED=true` (default remains off).
- Added full core task-intent parity behavior tests (8 intents) and non-task parity (check-ins, profile, schedules; 8 intents) in [`test_action_planner_routing.py`](../tests/behavior/test_action_planner_routing.py); 23 tests pass via `_run_intent_parity` / `_run_task_intent_parity`.
- Fixed profile update persistence in [`profile_service.py`](../user/profile_service.py): `update_user_context`/`update_user_account` plus UUID resolution for internal usernames (was silently failing via legacy `save_user_data` 3-arg call).
- Multi-action execution in [`action_plan_executor.py`](../communication/message_processing/action_plan_executor.py): runs `plan.actions` sequentially, combines completed handler messages, stops on follow-up (`completed=False`); 29 routing/executor tests pass.
- Planner multi-action parsing in [`action_planner.py`](../ai/chat/action_planner.py): repeating `ACTION:` blocks, shared defaults, per-action validation; tests in [`test_ai_action_planner.py`](../tests/unit/test_ai_action_planner.py); 18 planner/executor unit tests pass.
- Result-aware responses for all planner-path actions in [`action_plan_executor.py`](../communication/message_processing/action_plan_executor.py): `_apply_result_aware_responses` rewrites each completed action when AI is available (including multi-action plans), independent of `enable_ai_enhancement`.
- Audit hygiene: fixed path drift in product AI audit doc; `@handle_errors` on executor helpers; profile handler behavior tests mock `update_user_context`; ASCII cleanup; function registry regen; doc-sync PASS.
- Fixed remaining profile handler gap-coverage tests to mock `update_user_context` / `update_user_account` after `apply_profile_updates` migration.
- LM Studio quality: T-13.5 false CRUD, T-15.2 persona echo, T-1.2 trim, T-14.2 coherence, T-16.2 wellness honesty. Live run 2026-07-10T20:43: **65 pass / 3 partial / 0 fail** ([`ai_functionality_test_results_latest.md`](../tests/ai/results/ai_functionality_test_results_latest.md)). Remaining partials: T-7.1, T-9.3, T-11.2 (non-blocking).
- Phase 6: `wellness_status.py`, `conversation_coherence.py`, `_finalize_contextual_response`; unit tests in `test_wellness_status.py` and `test_conversation_coherence.py`.
- `AI_ACTION_PLANNER_ENABLED` stays default off until slice 9.4 item 8 review (explicit sign-off).

## Archive Notes
Older detailed entries live in `development_docs/changelog_history/` and remain the historical source of truth. Use [CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md) for the latest detailed entries and the archive folder for month-split history.
