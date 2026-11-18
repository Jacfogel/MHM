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

### 2026-11-18 - AI response quality and prompt contracts **COMPLETED**

- Strengthened command and cache assertions, separated automatic contracts from semantic review, and retained full response/context evidence with observed response sources. Expanded the synthetic prompt suite to 24 cases with adversarial safety coverage and app-versus-model failure diagnostics.
- Narrowed topic-based response guards so valid clarifications, conversation replies, and grounded wellness summaries survive. Replayed all seven unnecessarily replaced model replies successfully while retaining missing-data and false-completion protections.
- Aligned planner prompts and parsing, tightened wellness and venting instructions, and made task creation explicitly always available independently of scheduled reminders. Execution summaries distinguish verified saves, pending follow-ups, failures, and unattempted actions.
- All 850 AI-marked tests and 12 follow-up live checks passed, including six medication cases. Audit follow-up repaired documentation links/numbering, guarded and registered the new helper, and cleared Pyright warnings; all 41 focused maintenance tests passed.

### 2026-11-17 - AI replies, task availability, and test fixes **COMPLETED**

- Reply trimming now applies character and word limits together and prefers complete sentences. Replayed both cut-off capability replies successfully, and all 158 focused tests passed.
- Task creation and task context remain available with scheduled reminders off. Updated AI capabilities, fallbacks, and evaluation expectations. Both final live capability checks passed.
- The initial 30-request prompt rerun passed 29 checks. Manual review also found parser recovery of malformed venting output and a weak ambiguous-selection clarification.
- Fixed the nightly test category marker, three stale catalog expectations, and environment leakage in the missing encryption-key test. All 24 affected unit tests passed in parallel. Corrected the changelog ASCII issue and completed documentation sync.

### 2026-11-17 - Task reminder recovery and editor cleanup **COMPLETED**

- Saved snoozes and skipped-occurrence reminders recover at startup and during five-minute checks. Delivery attempts survive a restart. Explicit failures can retry, while unconfirmed attempts suppress automatic replay.
- Fixed browser task saving and moved save errors into the editor. Removed task blocking from the website, Discord, and the API. Existing task files still load, and recurring parent tasks retain their child steps.
- Documented the reminder storage callbacks, corrected the scheduler test, and regenerated the function registry. All 142 website tests, 111 focused task and API tests, and 74 scheduler follow-up tests passed in their respective runs.

### 2026-11-16 - Task, schedule, and account recovery **COMPLETED**

- Website and Discord close the snooze interaction after a saved snooze even if the alert fails. Task setup checks saved reminder windows, and partial subtask saves identify the steps that saved.
- Schedule commands validate windows before saving. Website Settings distinguishes saved changes from failed follow-ups, and website setup lets users retry delivery after Discord connects.
- Repaired relocated report links, regenerated the function registry, and fixed the stale reminder test assertion. The 118 focused audit tests passed, and `doc-sync` and Pyright reported zero issues.

### 2026-11-16 - Published tools update and report links **COMPLETED**

- Updated MHM's tools to published revision `74e5284`. MHM keeps its host configuration, and published scans exclude the tools directory.
- Regenerated the registry, dependencies, and directory tree under `development_tools/reports/`. The dependency check passed after reading the new report.
- Repaired links to removed tools files. All 43 logger tests passed, and `doc-sync` reported zero issues and zero Markdown link hints.

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

## Archive Notes
Older detailed entries live in `development_docs/changelog_history/` and remain the historical source of truth. Use [CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md) for the latest detailed entries and the archive folder for month-split history.

