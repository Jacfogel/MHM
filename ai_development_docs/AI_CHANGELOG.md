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

### 2026-11-06 - Finish TODO health, memory, and documentation work
- Added independently persisted message/chat health preferences and desktop controls; authenticated health identity is saved only after verification. Connect failure cannot enable an account; first sync now follows enablement.
- Added sync page counts, complete non-sleep pagination with 1,000-record pages (sleep cap 25), and a validated 7-90-day historical baseline window, default 14, excluding future/target dates and retaining sparse-history safeguards.
- Bounded context/session retention. The isolated state workload retained about 2.1 MB after two batches versus 41.3 MB before, then about 47 KB after explicit expiry; this excludes live providers and test-worker/OS pressure. Finished reference/guide/recovery refreshes; detailed evidence is in the paired changelog.
- Validation: 115 focused rerun checks, targeted Ruff, and standard Tier 2 audit pass. All five standalone TODO items are implemented and removed; test reliability remains in TEST_PLAN. Full run was incomplete: 2,980 passes, 1 failure, 2 errors, 27 skips; development-tools parallel phase passed 1,694. Worker/xdist and serial configuration issues remain in TEST_PLAN 2.8. No live service or delivery was run.

### 2026-11-05 - TODO progress: task processing, reconnects, and documentation
- Removed duplicate task-read initialization. Local task-list medians improved from 5.29 to 4.19 ms (Discord) and 5.27 to 3.84 ms (email); task completion improved modestly. Provider/network time is excluded; check-in/fallback gains are not claimed.
- Retained accounts linked to the same Discord identity receive a short reconnect acknowledgement without setup buttons. Non-creating account reads reject stale/unlinked/missing identities without reconstructing data or changing preferences; restart MHM to load the change.
- Corrected setup/email/button guidance and expanded precise references. Added optional read-only `--check-section-links` / `--section-path` inventory: 177 resolved references, no broken anchors, 36 advisory hints. Remaining guide/reference review stays in TODO 3.1/4.4/4.5; completed TODO 3.2/4.3 and the finished checker subtask were removed.
- Validation: 20 task/profile checks, 28 welcome checks, 25 tooling checks, and targeted Ruff passed; six reconnect checks passed again after encoding repair. Path/link regression checks also pass after fixing heading/query suffix handling; static docs were regenerated and path-drift analysis now reports zero issues instead of 103. A standard Tier 2 audit passed and refreshed the generated status reports, clearing the drift, registry, and completed-TODO warnings. No full audit or live delivery was run. A broader welcome run was stopped; a focused async attempt timed out in Windows event-loop/socketpair setup before application code. Focused view/delivery checks mock loop-bound dependencies.

### 2026-11-05 - Optional AI, health sync, and TODO cleanup **COMPLETED**
- Added manual-only AI controls and per-request task-breakdown authorization; global off and feature disables remain authoritative. Desktop Health Sync Now runs in the background, prevents duplicate actions, and offers reconnect/retry guidance, including revoked credentials retained on disk.
- Clarified TODO scopes and completion criteria, moved test-performance measurement to TEST_PLAN section 2.9, closed completed AI/sync/contract tasks, and filled Health mocking/context documentation gaps. Documented policy, persistence, routing, and recovery contracts; synchronized configuration/spec guidance and regenerated registry/dependency documentation.
- Fixed five TODO paths, standardized worker/close-hook error handling while preserving completion signals, updated the explicit-request test mock, and resolved optional-thread type warnings. Reviewed the routing facade advisory as a false positive and documented a narrow exclusion.
- Validation: focused runs passed 45 AI/settings/UI/task checks, 2 manual-breakdown checks, 33 client/policy checks, 54 Health checks, and 67 task/UI checks (overlapping coverage); the previously failing node also passed with two workers. Ruff passed; doc-sync, Pyright, and targeted error-handling/facade checks reported zero findings. Broader Discord runs stalled; no live-provider verification. Full audit interrupted at the user's request before Tier 3; future full audits belong to the user.

### 2026-11-05 - Clearer task reminders and simpler Discord controls
- Shortened the gentle reminder heading, moved the priority emoji beside the title, added the short task ID below priority, and removed the automatic smaller-step closing suggestion.
- Removed the Discord "Leave me alone" button and the due-date reassurance from the snooze-choice prompt. Snooze behavior and the text skip command remain unchanged.
- Updated reminder-format and button tests. Six focused tests passed for the initial wording/layout changes; the later combined run stalled and was stopped, leaving final verification incomplete.

### 2026-11-05 - Reminder and Google Health notification recovery
- Prevented restart duplicates by checking persisted successful deliveries for the same category, period, and day before scheduling or sending. Existing delays remain unchanged; reminder-focused runs passed 23 and 49 tests.
- Traced missing Google Health messages to October 4 token failures and auto-pause after the last October 3 sync/message. The reconnect warning failed and was never revisited; its original delivery error is no longer available. The personalized Google Health category is also absent from enabled preferences despite a saved schedule.
- Persisted reconnect-warning recovery now retries paused accounts on health polls, independently acknowledges primary/website delivery, bypasses in-memory retries, and resets after successful sync. Disabled accounts and non-auth pauses remain silent. All 41 focused health tests and targeted Ruff checks pass; integration guide and data-model docs were updated.
- Full-suite/live-service validation remains incomplete: the latest full run stalled after 1,152 recorded passes with no recorded failures and was interrupted; follow-up is in `TEST_PLAN.md`. Google reconnection and category re-enablement were not performed. Restart MHM to load the changes.


### 2026-11-05 - Nightly test fixes and crash diagnostics **COMPLETED**
- Added required category/domain markers for nine profile/context tests and completed three logger mocks with the Google Health log path. Verification passes 49 affected/policy tests with normal logging and 17 logger tests with verbose logging; targeted Ruff passes.
- Nightly diagnostics now record per-process collection/execution histories, random seeds, invocation arguments, environment versions, and stall/native stack traces without changing application log verbosity. Raw cores stay on the runner and are deleted after extraction; only stack traces are uploaded.
- Verified the recorder locally, including abrupt-exit durability, and on Ubuntu with six focused tests and a controlled native crash. Workflow YAML and shell syntax checks pass. The full suite was not rerun after the fixes; workflow changes are not yet active on main.
- The original Qt crash remains unexplained: 12 local parallel widget runs and two full Linux diagnostic runs did not reproduce it. The Linux runs exposed the marker regression and verbose-only logger mock failures addressed here.

### 2026-11-04 - Varied profile messages and expanded context **COMPLETED**
- Profile messages receive up to five recent profile deliveries as repetition examples, vary their focus and writing approach, and request fresh generation instead of cached wording. Fallbacks choose across interests, goals, and encouraging activities and avoid recent exact repeats when alternatives exist.
- Added pronouns, gender identity, loved ones, and custom fields to scheduled profile context. Limits are now 1,000 characters per standard field, 2,000 each for custom fields and support notes, and 12,000 overall; check-in and Google Health limits remain unchanged.
- Both variety helpers use shared error handling with safe defaults. Regenerated function registries, dependency documentation, and directory trees.
- **Verification**: 90 focused tests passed for the message/context changes; six variety tests passed after adding failure-path coverage. Documentation generation completed successfully. Live message quality was not evaluated.

### 2026-10-29 - Nightly result-rewrite tests **COMPLETED**
- Result-reply tests now call `generate_result_text` instead of the removed executor helpers and chat `generate_response`.
- Task confirmations stay exact. Eligible actions can still be rewritten, and ungrounded check-in statistics are still dropped.
- **Verification**: 24 focused checks pass. Targeted Ruff passes. Local `nightly-test-suite --strict` passed 6,358 tests with no failures.

### 2026-10-28 - OpenAI prompt and context review **COMPLETED**
- Unified catalog-backed action prompts, field requirements, and output budgets; separated runtime data from instructions and preserved relevant conversation context, including explicitly selected assistant suggestions.
- Removed duplicated response enhancement, aligned persona loading/reloading and task prompts, and stopped canned repairs from overwriting valid facts, focused advice, emotional replies, stories, or feature restrictions. Execution checks and deterministic fallbacks remain authoritative.
- Added a synthetic live evaluation runner with raw/final responses, timing, and token use: the baseline exposed four repair regressions; the corrected suite passed 30/30 checks plus 2/2 failed-result checks, without executing actions or writing user accounts.
- Completed strict Tier 3 audit follow-through: repaired stale tests, missing error handling, the circular dependency, registry/documentation drift, and Ruff/Pyright findings. Regenerated documentation; reviewed high-fan-out hubs without cosmetic refactoring. Removed the temporary review document after consolidating lasting guidance in the AI system guide.

### 2026-10-28 - Nightly marker and email-socket failures **COMPLETED**
- Task-simplify and task-response tests now carry the required category and domain markers that failed nightly policy checks on Oct 26-28.
- Email initialization and recovery tests mock IMAP, so a live Gmail socket can no longer time out and fail a later nightly test during garbage collection.
- **Verification**: 15 focused checks pass, including both marker guards. Targeted Ruff passes. The full nightly suite was not rerun locally.

### 2026-10-28 - OpenAI replaces LM Studio **COMPLETED**
- OpenAI Responses API now serves optional model features, defaulting to configurable `gpt-5.4-mini`. Hosted model-access checks replace local loading and process management.
- Existing AI policy and deterministic fallbacks remain authoritative; no key means fallback. Uses `store=false`, bounded inputs/output, sanitized failures, and rejection of partial/refused output.
- **Live connection**: Existing local key is present, but OpenAI rejected it with HTTP 401. A valid local `OPENAI_API_KEY` and a desktop/service restart are required before live replies work. The synthetic test sent no user context.
- **Verification**: 365 distinct focused checks pass across chatbot/policy/configuration, Responses transport, task planning, user journeys, command parsing, and Discord review suites. Full-project Pyright and targeted Ruff pass; docs generation and doc-sync succeed. Discord async checks require local Windows event-loop sockets; the restricted run stalled before test execution and the unrestricted mocked run passes all 13 checks. A full Tier 3 audit was not run.
- **Credential follow-up**: Discord logs confirmed repeated 401 fallbacks because stale inherited Windows credentials overrode the replacement project key. OpenAI key resolution now prefers an explicit local `.env` setting (including blank), retaining process-environment support when no local key is set. 47 credential/configuration/policy/transport tests pass; targeted Ruff passes. Fresh-process model access and synthetic generation pass using the actual configuration without environment overrides. Restart the desktop app to reload the fix in its managed service.
- Upgraded eight vulnerable dependencies to advisory-fixed versions and raised matching metadata floors. Fresh pip-audit is clean; pip check finds no conflicts.
- Explicit positive HTTP timeout clears Bandit B113. Removed unused OpenAI manager wrappers; client readiness remains authoritative. Clarified sampling documentation and repaired eight historical broken links.
- 167 focused regressions pass, with clean Ruff/Pyright checks. Restart MHM to load updated libraries.
- **Audit refresh**: Standard analyzers now report zero dependency vulnerabilities, Bandit issues, duplicate groups, facade/shim candidates, and Markdown link-target hints. Regenerated documentation and cached status/priority reports; documentation sync passes. Full Tier 3 audit and coverage regeneration were not rerun.

### 2026-10-28 - Two-message notebook append sessions **COMPLETED**
- Reference-only `!append` now starts a persisted append session; the next reply adds to the existing note or journal entry. One-message commands remain supported.
- Cancel, skip, and timeout leave content unchanged; lists and invalid references are rejected before starting.
- **Verification**: 95 notebook behavior and handler checks pass. Targeted Ruff and Pyright checks pass. Restart the service to load the new flow.

### 2026-10-27 - Explicit Discord AI task breakdown **COMPLETED**
- Audit follow-up: repaired the stale low-energy test patch and the Discord test's button-type warning. All 129 affected tests pass sequentially and in parallel; full Pyright and targeted Ruff are clean. Regenerated registry/dependency/tree docs. Full Tier 3 was not rerun.
- Website and Discord share **Break down with AI**, **Add selected steps**, and **Add my own step** labels; reminder guidance and desktop AI controls match. Existing typed `simplify` aliases still work.
- Task details add **Break down with AI** through the deterministic task handler, with unsaved suggestions, selected/all saving, own-step entry, and cancellation.
- Global/feature disables prevent model initialization and availability probing; manual step entry works without AI. Review ownership and matching pending-confirmation cleanup are enforced. Manual-only configuration remains a follow-up.
- All 114 focused task/Discord/policy tests, static checks, and documentation sync pass. Restart the service; live Discord validation remains manual.

### 2026-10-27 - Desktop AI controls, quiet mode, and reminder dependencies **COMPLETED**
- Desktop Admin > AI Controls owns installation-wide global and seven feature switches, with environment-default restoration. Atomic shared settings override the environment on subsequent decisions across processes; invalid saved controls fail closed, failed saves retain the draft, and Cancel writes nothing. These controls are excluded from website user settings.
- Quiet-mode shortcuts use the saved Phrases morning start time and account timezone. Focus/reminders explain quiet mode, energy thresholds, and a restart-stable 30-minute recovery hold after today's low-energy answer. Disabling energy rules bypasses the hold; health-signal cooldowns remain separate follow-up work.
- Shared reminder date fields now live in tasks/task_reminder_state.py, removing the scheduler/snooze cycle. Reminder/snooze/skip and cleanup checks pass 143 tests. Explanation failures return safe empty text; the function registry includes the new helpers.
- Desktop controls validation passes 126 focused policy/chatbot/configuration/admin tests, a final 17 settings/dialog tests, and earlier 91 desktop-shell regression checks. Ruff and Pyright pass; the rendered dialog was visually reviewed. Restart desktop and service once to load the feature; later policy saves apply without restarting. Earlier quiet-mode checks passed 90 tests; a broader website-service run stalled and was stopped.

## Archive Notes
Older detailed entries live in `development_docs/changelog_history/` and remain the historical source of truth. Use [CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md) for the latest detailed entries and the archive folder for month-split history.

