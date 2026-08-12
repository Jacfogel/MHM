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

### 2026-08-11 - Discord package and bot split **COMPLETED**
- Moved Discord modules into `events/`, `ui/`, `onboarding/`, `webhooks/` with search-and-close imports (no legacy shims).
- Merged helpers into `ui/helpers.py`, lifecycle into `events/lifecycle.py`, and absorbed `item_form_shared` into `ui/create_item_ui.py`.
- Extracted rich delivery, connection health, command registration, and webhook tunneling; `bot.py` is now a 545-line lifecycle host.
- Post-audit hygiene: DISCORD_GUIDE path drift, changelog link retargets, docstrings/`@handle_errors`, Ruff/Pyright clean, legacy false-positive comment fixed; `doc-sync` PASS.

### 2026-08-11 - Appropriate coupling reductions (inverted edges) **COMPLETED**
- Public check-in first-question API; `service_requests` no longer calls private flow helpers.
- Scheduler runtime handle in `scheduler.runtime_access`; tasks/admin no longer import `core.service` for the locator.
- Coupling audit signal improved: unique fan-out > 10, exclude `__init__.py`; priorities triage inappropriate edges (not hub shrink).

### 2026-08-10 - LIST_OF_LISTS move and list SSOT cleanup **COMPLETED**
- Moved `LIST_OF_LISTS.md` into `development_tools/`; retargeted pointers.
- Omitted default-copy JSON sections/keys; retired dead `quick_audit.audit_scripts` (Tier 1 = `audit_tiers`).
- Fixed `audit --quick` guide prose; `STORAGE_SCOPE_*` re-exported from `audit_scope`; prompt category/flow alignment test.
- Follow-up: doc-sync path-drift + F401/SIM300 from that SSOT work cleared (`doc-sync` PASS).

### 2026-08-06 - LIST_OF_LISTS consolidation scan, rewrite, and SSOT cleanup **COMPLETED**
- Rewrote LIST_OF_LISTS as current ownership map; trimmed completed-history tables.
- Follow-up: live/example `base_exclusions` -> additions/removals; emptied portable `CONFIG_VALIDATOR` / `DOMAIN_MAPPER_DEFAULTS` / `known_deleted_files`; omitted duplicate JSON keys (`test_run`, `analyze_duplicate_functions`, identity `directory_to_marker`, matching error_handling scalars).
- Same-day hygiene: documented MHM `derived_prefix_excludes.core` (includes `development_tools` in `CORE_MODULES`); fixed `EXPECTED_TOOLS` tier comments/count; shared `_PYTHON_KEYWORDS_SHARED` for path-drift keyword tuples.
- Updated config.py comments that pointed at old LIST_OF_LISTS section numbers.

### 2026-08-04 - Personalized greetings/closings cleanup **COMPLETED**
- Strip `Best regards`, soft day-wishes, help-offer closers, and `--[Your Name]` signatures.
- Normalize to `Hi Name.` on one line (including `Hi Name.\nBody`); drop ungrounded check-in sentences when Data has no `Recent check-ins`.
- Prompts ban Dear/newline-after-name, fake check-in claims, and letter/help-offer closings.

### 2026-08-03 - Personalized prompt + Google Health steps/AZM sync **COMPLETED**
- Removed concrete sample metrics from `generate_personalized_message()` instructions so models cannot parrot `~5.5h` / `~2,400 steps` / `~45 active minutes` when Data has no recent wellness patterns.
- Prompt now: copy only `~` values from the Data block; otherwise write a warm general message with no fabricated sleep/steps/activity numbers.
- Fixed steps/active-zone-minutes `dailyRollUp` 400s: clamp `pageSize` so `window_size_days * page_size <= 90`; re-raise rollup errors so list fallback works.

### 2026-08-02 - Richer Google Health context (rounded sleep/steps) **COMPLETED**
- Pattern text may include rounded sleep/steps/active minutes; HR/HRV remain categorical bands only.
- Multi-day streaks (>=2 days): shorter sleep, lighter activity, or higher activity.
- Signals carry optional `steps` and `active_minutes`; `build_recent_health_patterns()` feeds scheduled messages and chat (`recent_patterns` in health envelope).
- Personalized prompt may use approximate sleep/steps/active minutes and streaks from Data only; truncate limit 700; guidance summary stays tone-only.
- Follow-up: regenerated function registry for health context helpers; Ruff SIM108 cleaned in sleep-hour formatting; doc path drift + ASCII cleanup; shared `activity_effort_band()` for personalization and streak phrasing.

### 2026-08-01 - Personalized cleanup; schedule envelope save flake **COMPLETED**
- `strip_letter_signoffs()` strips dash signatures, `Best,` / `Wellness Assistant` lines, and trailing `(Note: ...)` meta text.
- `collapse_salutation_newlines()` puts the body on the same line as `Hi/Hey/Dear Name`.
- Schedule save flake: `coerce_schedules_to_in_memory()` in `profile_v2_io` unwraps v2 envelope/cache pollution in merge/validate/read; loaders do not cache failed validation payloads. Breaks `user_data_read` <-> `user_data_validation` circular import.

### 2026-07-30 - Fix `ids` logger; consolidate component logger aliases **COMPLETED**
- `core/ids.py` uses canonical `get_component_logger("main")` (no new alias/sink).
- Domain/AI/UI/Discord/communication call sites use canonical sinks; `COMPONENT_NAME_ALIASES` emptied (temporary bridges only).
- Logging guide + channel-logger/logging tests updated.

### 2026-07-29 - NOTES_PLAN refresh; `|` separators; group disambiguation; `!edit`; shared short IDs **COMPLETED**
- Validated/refreshed NOTES_PLAN + PLANS notebook status (help polish, AI context privacy remaining).
- Parser: title/body accepts newline / `|` / `:`; append strips optional leading `|`.
- Group ambiguity: `!setgroup` aliases; bare `!group` set only for short-ID/UUID; multi-word groups list; anchored `quick note(s)`.
- `!edit` sessions: `FLOW_ENTRY_EDIT` replace-body flow with cancel/skip/timeout leaving entry unchanged.
- Shared short IDs: [`core/ids.py`](../core/ids.py) owns `t`/`n`/`l`/`j` generate/parse/display; notebook rejects `t...` as entry refs; Section 5.1 Done.
- Audit follow-up: domain marker on `test_core_ids`; `user_data_v2_base` `__all__` re-export; legacy dashed-id scan clean; registry includes `ids.py`.
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

## Archive Notes
Older detailed entries live in `development_docs/changelog_history/` and remain the historical source of truth. Use [CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md) for the latest detailed entries and the archive folder for month-split history.
