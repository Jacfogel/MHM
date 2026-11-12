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

### 2026-11-07 - Audit and standardize development planning documents **COMPLETED**
- Removed completed planning items, corrected stale statuses/behavior, and preserved unfinished work found inside completed summaries. Windows suite reliability and live validation remain open; audit scope is explicit.
- Standardized all four plans' role sections, shared maintenance rules, and review checklists; repaired affected guide/spec links. Rules protect unfinished work before removing completed sections.
- Plan links/fragments and diff checks pass; no tests or live-service checks rerun in this chat. Retained existing generated report updates and fast-forwarded local main to include ten nightly-fix commits.

### 2026-11-07 - Resolve OAuthlib and pyasn1 advisory findings
- Fixed all five reproduced pip-audit findings by raising both manifests and the local environment to oauthlib 4.0.1 / pyasn1 0.6.5. Fresh scan: zero known vulnerabilities; pip check passes.
- All 72 focused Google Health auth/client checks plus real ASN.1/Google-auth/offline OAuth smoke checks pass. Canonical security cache refreshed and Tier 2 audit/report regeneration passes. Changes are local; no full-suite rerun or push yet.

### 2026-11-06 - Investigate nightly run 160
- 2026-11-07: full fixed-environment Linux run `42404010183` passed without native cores. Removed temporary Qt inventories, associated tests, probe script, and comparison workflow/input; kept dependency/lifecycle fixes, lightweight history, stall traces, and native-core failure detection. Updated guides/plan/removal inventory. All 33 focused two-worker checks, Ruff, and Tier 2 audit pass; cleanup edits remain local.
- 2026-11-07 remediation: both dependency manifests now exclude PySide6 6.12.0. Linux/Python 3.11 dry resolution selects matched 6.11.3 packages; the isolated comparison now includes 6.11.3 plus good/bad controls. Full fixed-environment Linux validation remains pending.
- 2026-11-07 source isolation: GitHub Qt-only probe `42403486795` on Python 3.11.18 shows PySide6/Shiboken 6.12.0 loses one None reference per tested void Qt call (-1/-32/-128), versus zero for 6.11.2 and both Python controls. No MHM, pytest, QApplication, or background threads involved. This confirms the native binding defect behind the ongoing none_dealloc abort. Probe/workflow commit `863dd57a` is pushed; dependency remediation and full-suite validation remain pending.
- 2026-11-07: scoped cleanup now covers simple widget behavior/check-in helper tests. Their 20 passing checks initially retained 850 valid wrappers; final teardown leaves only QApplication. Explicitly dispose the intentionally rejected second QVBoxLayout in a finally block. Earlier combined two-worker validation passed 29 checks; final serial rerun, Ruff, and Tier 2 audit pass. Latest changes are local; the Linux none_dealloc shutdown abort is not yet resolved.
- Cleaned the two remaining widget modules identified in run `42323059729` (which passed tests but aborted in CPython none_dealloc at shutdown). Their 55 local checks pass before/after; live wrappers fell from 1,419 to QApplication/QCommonStyle. Native deletion now precedes Python GC, and lifecycle assertions verify destruction. All 64 combined two-worker checks, Ruff, and Tier 2 audit pass; full Linux crash validation remains open and new edits are local.
- Reviewed six more retained UI modules and applied scoped widget teardown. Their 126 serial checks pass before/after; live wrappers fell from 14,153 to QApplication plus QCommonStyle, with no test dialogs/widgets left. Combined two-worker validation passes 154 parallel-capable checks; the five no-parallel cases passed serially. Task CRUD now asserts actual destruction. Ruff/Tier 2 audit pass; full Linux crash validation remains pending and changes are local.
- Confirmed missing DeferredDelete delivery in user-profile coverage fixtures: 28 passing tests retained 27 dialogs/17,115 valid wrappers. Scoped teardown now leaves only QApplication live; 31 serial and 33 two-worker checks pass, plus Ruff/Tier 2 audit. Other UI modules and Linux crash validation remain open; cleanup changes are local.
- GitHub rerun passed 6,451 tests with 8 skips but repeated the Qt atexit crash. Added weakly tracked QObject validity/ownership and first-observation inventories at test/shutdown boundaries, plus a workflow failure gate for native core dumps. Linux validation of the new instrumentation remains pending; the crash remains open.
- Instrumentation validation: five focused checks pass serially and with two workers, real offscreen Qt invalid-wrapper/atexit probe passes, clean/crash workflow guard probes pass, targeted Ruff and Tier 2 audit pass.
- Reproduced the no-print policy failure and moved the three measurement files to component INFO logging; 25 focused checks, targeted Ruff, and Tier 2 audit pass.
- Native diagnostics place the separate worker crash after successful session finish, inside PySide6/Qt application destruction during interpreter exit. Originating object/test remains unknown; Linux replay details and remaining full-suite validation are tracked in TEST_PLAN 2.8. No crash fix or full-suite pass is claimed.

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


## Archive Notes
Older detailed entries live in `development_docs/changelog_history/` and remain the historical source of truth. Use [CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md) for the latest detailed entries and the archive folder for month-split history.

