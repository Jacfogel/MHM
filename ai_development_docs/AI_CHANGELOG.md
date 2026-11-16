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
- Limit entries to 1 per chat session; update the existing session entry as work progresses.
- Maintain chronological order (most recent first)
- REMOVE OLDER ENTRIES when adding new ones to keep context short
- Target 10-15 recent entries maximum for optimal AI context window usage

## Recent Changes (Most Recent First)

### 2026-11-16 - Development tools release split and audit cleanup **COMPLETED**

- The private tools repo now has development and published branches. The development branch owns self-checks, tests, fixtures, and the testing guide. MHM uses the published runtime, one tools README, and the renamed `STATUS_BRIEF.md` and `PRIORITIES_BRIEF.md` reports.
- Run `python development_tools/run_development_tools.py audit`. The shared CLI selects MHM's config via `pyproject.toml`. Removed the root launcher and MHM-specific loader fallbacks. CLI, environment, and local config overrides still work.
- Consolidated task and notebook roadmaps into PLANS.md and moved their regression commands to the testing guide. Moved prompt evaluation snapshots to `tests/ai/prompt_reports/`. All 30 prompt regression tests passed.
- Fixed nightly logging, registry and docstring gaps, Pyright, README checks, and the runner-isolation tests. Upgraded `dnspython` to 2.9.2. Fresh pip-audit and documentation sync were clean, and the saved Tier 3 product tracks reported zero failures or errors.

### 2026-11-15 - Task dependencies **COMPLETED**

- Tasks persist `blocked_by` and inverse `blocks` relationships, reject self/missing/circular edges, and become ready automatically as prerequisites are completed or deleted.
- Website task editing manages prerequisites; website and Discord lists expose blocked state. Focused Python, browser, route, and Ruff checks pass; live rendering remains unverified.
- Recurring parents carry complete step templates and remapped dependencies into the next occurrence. Uncomplete rewinds the generated next family, progressed series are protected, completed children require an active parent, and subtasks cannot repeat independently.

### 2026-11-13 - Development-tools documentation and parallel audit test **COMPLETED**

- Fixed stale guide references, the missing README file address, and 32 links to the relocated deprecation inventory. Documentation checks reported zero issues.
- Isolated the custom-audit subprocess's logging settings from the parallel runner. All 13 portability tests passed with two workers.

### 2026-11-12 - Configurable scoped audit and backup reports **COMPLETED**

- Custom audit status and backup command reports now use host-configured destinations.
- Scoped status headers, backup health priority links, and cache inventory use the same paths as report writers.
- MHM's tracked policy and deprecation inventory moved to `development_docs/devtools/`. Host configuration also controls log, archive, and timing destinations.
- Published and pinned the private development-tools subtree at `9a7dd97c`.

### 2026-11-12 - Host-configured audit and legacy reporting **COMPLETED**

- Audit summaries and aggregate JSON use host-configured paths and keep full-repo and scoped outputs separate. Quick Status, report links, and freshness checks follow those paths.
- Legacy scanning and reporting share a configured deprecation inventory. Portability tests cover custom destinations, cross-scope links, and audit write timing.

### 2026-11-12 - Configurable coverage report paths **COMPLETED**

- Share the host-configured coverage snapshot directory and Markdown report path across coverage execution, report generation, audit readers, and snapshot cleanup.

### 2026-11-12 - Windows test performance baseline **COMPLETED**

- Established a 138-test Windows baseline for serial and two-worker runs. Closed the baseline task and kept the full-suite memory-pressure trigger in intermittent failure triage.

### 2026-11-12 - Report portability, test coverage, and task skip recovery **COMPLETED**

- Report scripts and analyzers use the host configuration. Integration tests exercise custom folders, detail overrides, and relative summary links.
- Verify that invalid mood answers preserve progress and corrected answers persist across a state reload.
- Excluded config and logs from the test backup and removed the serial-only marker after repeated two-worker checks.
- Recurring and one-off skips report reminder scheduling failures while confirming the saved task state. Snoozes and skips share the deferred reminder scheduler.

### 2026-11-11 - Relocate development-tools tests **COMPLETED**

- Moved the standalone suite to `development_tools/tool_tests/` and updated runners, coverage, CI, and configuration compatibility.
- Included the saved snooze time in alert scheduling failure replies.

### 2026-11-10 - Recovery messages and focused test validation **COMPLETED**

- Added specific recovery steps for Discord account errors and task snoozes whose alerts fail to schedule.
- Isolated two backup tests and removed one serial-only marker after repeated two-worker validation. Updated the parent, test, and notebook plans with current guidance and evidence.
- Passed 17 snooze tests, 150 notebook tests, both backup validation tests under two workers, and the empty-user backup test in isolation. Discord pytest results were pending at the last check.

### 2026-11-09 - Isolate audit logs and test files **COMPLETED**

- Routed dev-tools runtime logs outside production and gave each backup restore drill its own temporary directory.
- Moved read-only file and tag tests to per-test directories and fixed an order-dependent logger test.
- The Tier 3 rerun passed both product tracks with no observed production-log writes or recurrence of the Windows path error or worker exits. Removed completed test-plan section 2.2.

### 2026-11-09 - Complete test reliability and Google Health validation **COMPLETED**

- Fixed the stale nightly profile assertion. All 33 focused profile tests passed.
- Recorded consecutive clean Tier 3 audits, 6,728 Windows product passes, 1,694 development-tools passes, and 21 slow-test passes.
- Verified the live restart and signed-in Google Health sync. Removed completed test-plan section 2.1 and retained worker-loss triage in section 2.8.

### 2026-11-09 - Website bulk task and notebook actions **COMPLETED**
- Add tags to selected active tasks while preserving their existing tags.
- Add or remove tags and archive selected active notebook entries. Bulk requests identify entries they could not update.
- Bulk actions appear after selecting tasks or notebook entries. Priority requires an explicit choice before **Change priority** becomes available.
- All 51 focused website tests passed after the UI update. Backend verification had no confirmed final result.

### 2026-11-07 - Improve command failure recovery guidance **COMPLETED**
- Added actionable recovery replies and save confirmation across task, notebook, schedule, check-in, profile, account, and health commands.
- Preserved drafts on failed saves, made check-in retries idempotent, and hardened account verification and notebook list numbering.
- Notebook queries distinguish unreadable or invalid files from empty collections and preserve the original files.
- Focused tests and lint passed. The user reported a clean full audit at the earlier task/notebook checkpoint.

### 2026-11-07 - Strengthen test runner isolation and policy boundaries **COMPLETED**
- Both serial runner paths now use the tools pytest configuration/conftest boundary; regression tests cover standalone tools and full-suite modes.
- Focused validation: 15 tests passed and marker analysis passed. The real one-worker tools run reached 72 passes before memory exceeded 98%; stopped it and the concurrent audit. Complete-suite/audit validation remains open in TEST_PLAN.md.
- Monitoring follow-up: closed domain-marker monitoring after analyzer/policy validation, retaining routine maintenance. Notebook/help (23) and task-list UI (20) tests pass; Windows async tests needed local loopback access. Production log sizes stayed unchanged. Live checks remain open; only the user runs full audits.
- Added product AST boundary guards for time APIs, stream JSON storage, and core/UI imports; documented exact exceptions and scanner limits. Five health time calls now use canonical helpers; 33 policy and 62 existing health/time checks pass, plus Ruff/marker/diff checks. Completed roadmap items moved to maintenance; no full audit or live reload for this follow-up.
- Fixed boundary-test links in both testing guides and clarified prose for path scanning; narrowed AST node types to remove the Pyright warning without suppression. All 15 core/UI checks pass; follow-up uses doc-sync/Pyright only.
- Health follow-up: transition tests reproduced future-dated signals affecting pressure; fallback now excludes future dates. Health cooldown evaluation moves to monitoring; an extra timer awaits live evidence of intraday oscillation and must respect immediate opt-out. User's clear full audit is recorded separately from complete-suite/live gates; no agent full audit.

## Archive Notes
Older detailed entries live in `development_docs/changelog_history/` and remain the historical source of truth. Use [CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md) for the latest detailed entries and the archive folder for month-split history.

