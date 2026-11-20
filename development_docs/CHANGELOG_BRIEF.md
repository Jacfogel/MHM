# Changelog Brief
> **File**: `development_docs/CHANGELOG_BRIEF.md`
> **Audience**: Developers and AI collaborators
> **Purpose**: Lightweight summary of recent changes
> **Style**: Concise, essential-only, scannable
> **See [CHANGELOG_DETAIL.md](CHANGELOG_DETAIL.md) for the full history**

## Overview

This file is a lightweight summary of recent changes for all contributors. It provides essential context without overwhelming detail. For the complete historical record, see [CHANGELOG_DETAIL.md](CHANGELOG_DETAIL.md).

## How to Update This File
1. Add a new entry at the top summarising the change in 1-3 bullets.
2. Keep the title short: "YYYY-MM-DD - Brief Title **COMPLETED**".
3. Reference affected areas only when essential for decision-making.
4. Move older entries to [CHANGELOG_BRIEF_ARCHIVE.md](changelog_history/CHANGELOG_BRIEF_ARCHIVE.md) to stay within 10 total.
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
- Target 10 recent entries maximum for optimal AI context window usage

## Recent Changes (Most Recent First)

### 2026-11-19 - Google Health nightly native crash **COMPLETED**

- Registered background connect/sync callbacks as Qt slots to keep window updates on the UI thread after the nightly bus error. Added thread-affinity regression coverage; Linux nightly confirmation remains pending.
- Updated stale message-editor/process-watcher recovery assertions and Qt metadata typing; all 78 affected dialog tests passed with two workers.

### 2026-11-19 - Helpful failures and audit fixes **COMPLETED**

- Improved vague desktop, browser, chat, Discord, task, and launcher failures with saved-state guidance and concrete recovery steps.
- Kept drafts open on failed saves, checked storage results before success, retained failed question undo, and preserved earlier planned-action results.
- Completed priority actions 1, 2, 4 and quick wins: 68 affected tests pass, four Pyright errors are fixed, and three stale references plus ten broken links are repaired. Pyright and documentation checks are clean; Vulture reports zero findings. Full audits remain owner-run.

### 2026-11-19 - Shared documentation consolidation **COMPLETED**

- Consolidated AI mirrors and session safeguards into shared guides and AGENTS.md; removed paired-heading requirements.
- Moved this brief and its archive into development_docs; removed the old AI-doc folder and Cursor rules, commands, and plans.
- Updated tooling in MHM and both upstream branches (development 352201b, published 02ca5d2). All 170 focused tests and published runtime smoke checks passed.

### 2026-11-19 - Feature guides and brief retirement **COMPLETED**

- Renamed the website README to [WEBSITE_GUIDE.md](../website/WEBSITE_GUIDE.md) and updated maintained references/anchors.
- Indexed SMS, website, and Google Health guides in human/AI navigation, communication guidance, and tracked/local tools configuration. Standalone guides remain unpaired.
- Numbered website/health headings and refreshed documentation checks and generated references.
- Retired function/dependency brief generation, outputs, brief-only settings/helpers, and navigation references. Detailed inventories remain; development c76c393 and published b5affed were pushed upstream. Tools tests: 115 passed, 1 skipped; published/MHM default and custom output checks passed.

### 2026-11-19 - Health recovery and Twilio SMS pilot **COMPLETED**

- Health status, enable, and sync failures describe unchanged or unconfirmed saved state and safe recovery without exposing service errors.
- Added separate opt-in simulation and Twilio owner-pilot modes, signed loopback webhooks, durable receipts, delivery callbacks, STOP/START, SMS preference persistence, and shared task/check-in reply handling. Pilot recipient/account/consent checks remain mandatory; live credentials and HTTPS forwarding are unconfigured.
- Final combined SMS/profile/email/reminder regression run: 75 passed; Ruff and whitespace checks passed. Paid API calls are mocked; setup/live validation and additional-user enrollment remain open in the SMS guide and plan.
- Audit follow-up: SMS docstrings/error boundaries, shared phone helper (no circular import), supported-channel test assertion, and test type fixes. Serial 102 passed; two-worker 77 passed; Pyright zero errors/warnings. Regenerated documentation and fixed metadata/headings/links.

### 2026-11-18 - Refresh Google Health before messages **COMPLETED**

- Google Health personalized messages refresh data before building context, including fallback messages when AI is unavailable. Recent pulls and failed attempts suppress repeat requests for five minutes.
- Refresh respects message personalization permissions, feature state, and testing mode. Failures retain saved-data/general-message fallback behavior; background syncing remains active.
- Updated the AI guide. All 41 targeted refresh, sync-manager, and health-context tests passed; targeted Ruff and diff checks passed.

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
