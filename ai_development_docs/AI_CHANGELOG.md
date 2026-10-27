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

### 2026-10-27 - Desktop AI controls, quiet mode, and reminder dependencies **COMPLETED**
- Desktop Admin > AI Controls owns installation-wide global and seven feature switches, with environment-default restoration. Atomic shared settings override the environment on subsequent decisions across processes; invalid saved controls fail closed, failed saves retain the draft, and Cancel writes nothing. These controls are excluded from website user settings.
- Quiet-mode shortcuts use the saved Phrases morning start time and account timezone. Focus/reminders explain quiet mode, energy thresholds, and a restart-stable 30-minute recovery hold after today's low-energy answer. Disabling energy rules bypasses the hold; health-signal cooldowns remain separate follow-up work.
- Shared reminder date fields now live in tasks/task_reminder_state.py, removing the scheduler/snooze cycle. Reminder/snooze/skip and cleanup checks pass 143 tests. Explanation failures return safe empty text; the function registry includes the new helpers.
- Desktop controls validation passes 126 focused policy/chatbot/configuration/admin tests, a final 17 settings/dialog tests, and earlier 91 desktop-shell regression checks. Ruff and Pyright pass; the rendered dialog was visually reviewed. Restart desktop and service once to load the feature; later policy saves apply without restarting. Earlier quiet-mode checks passed 90 tests; a broader website-service run stalled and was stopped.

### 2026-10-25 - Discord reminder actions and snooze delivery repaired **COMPLETED**
- Snooze, Skip, Simplify, and continued check-in replies preserve their deterministic text. Unavailable AI enhancement returns no replacement text instead of exposing an offline reply and internal action catalog.
- Discord restores saved task reminder buttons at startup. Custom Snooze rejects unrecognized dates while accepting clock-only and weekday/time phrases.
- Snoozes retain seconds through scheduling and restart recovery; one-time jobs remove themselves after delivery, including failure, and remain compatible with task/orphan cleanup. Scheduling failures report that the snooze was saved but the reminder could not be scheduled.
- Verification: the earlier action fixes passed 75 targeted tests; the final scheduling changes passed separate runs of 75 reminder/task-flow tests and 19 time/cleanup tests. Targeted Ruff checks passed. Restart the bot to apply the changes.

### 2026-10-21 - Task reminders repeat on later days **COMPLETED**
- `reminder_sent_on` blocks a second reminder for the same task on the user's local date. The next day can send again, and a pending snooze still arrives.
- Tasks stuck with `reminder_sent` and no date are eligible again. Task and check-in schedules no longer receive an all-day window; message categories still do. Existing all-day task periods were removed from every account. This account's reminders stay in the 14:00-16:00 window.
- Focused scheduler and snooze tests cover the same-day, next-day, and snooze cases.

### 2026-10-20 - Nightly notebook inbox test stays date-stable **COMPLETED**
- The October 19 nightly suite failed one test: after clearing tags, a grocery list seeded on September 19 was older than the 30-day inbox window.
- Website note fixtures now use the current timestamp, and mocked edits refresh `updated_at` the same way real notebook saves do.
- The notes route tests pass. Inbox behavior is unchanged.

### 2026-10-19 - Quiet mode and energy rules are user-controlled **COMPLETED**
- Website **Support mode** now stores a clear quiet-mode end time plus an on/off switch and threshold for deterministic check-in energy rules.
- Quiet mode pauses scheduled encouragement and check-ins, but still permits due, overdue, urgent, and critical task reminders with gentler wording; manual actions remain available.
- The saved energy rule drives both task ranking and reminder copy without inferring mood from chat or requesting an LLM. Next work is better rule explanations, cooldowns, and an "until tomorrow" shortcut.

### 2026-10-19 - Optional AI controls centralized **COMPLETED**
- A provider-neutral policy now supports global AI off and feature-level disable lists while preserving deterministic commands, reminders, and fallbacks.
- Low-level HTTP calls and higher-level cache paths both enforce the policy; disabled features cannot make model requests or return old cached AI responses.
- Planning now prioritizes optional AI and deterministic mood/energy rules. Provider billing and budget tracking stay outside MHM, and response-quality work is paused until the model changes.

### 2026-10-17 - Adaptive task focus and reminder pressure **COMPLETED**
- Home, scheduled reminders, and chat suggestions now use one deterministic backend focus policy with urgency guardrails, snooze awareness, subtask preference, time-of-day fit, and effort estimates.
- Tasks retain five deferrals; repeated snoozes/skips surface a smaller step, **Simplify**, or due-date reconsideration. Discord actions are **Done**, **Snooze**, **Simplify**, and **Leave me alone** with unchanged underlying behavior.
- One reliable-signal policy lowers pressure across task, motivational, and Google Health messages. Missing energy/health signals preserve existing behavior.
- The new integrated regression set passes 138 Python checks and 41 browser/proxy tests; Ruff and targeted Pyright are clean.

### 2026-10-17 - Notebook persistence and reference safety hardened **COMPLETED**
- Notebook logs retain only safe operational metadata, and the privacy guard now scans every Python runtime package.
- Notebook creates and mutations use lock-scoped read-modify-write transactions; lists persist final completion states in one write, and concurrent edits no longer overwrite one another.
- Ambiguous short IDs or titles never select the first entry; command handlers ask for an exact short ID. Website GET routes derive all views from one worker-thread snapshot.
- The regenerated function registry includes the new ambiguity helper. The full quick suite passes 6,213 tests with no failures, Ruff passes, and project-wide Pyright reports no warnings.

### 2026-10-16 - Nightly policy checks match the test tree **COMPLETED**
- Nightly failures since October 13 were policy scans, not product failures. The escape-path test no longer names the production users directory, and cleanup comments no longer do either.
- Worker user-store cleanup tests now carry the `user` domain marker, so the slow domain-marker scan passes in the nightly suite.

### 2026-10-16 - Social sign-in connectivity and home history fixed **COMPLETED**
- Live Google sign-in failures were traced to the headless gateway running with outbound HTTPS blocked (`WinError 5`/`WinError 10013`). The restricted process was replaced with a normally networked service; Google provider discovery, authorization startup, client credentials, and the production callback now validate successfully.
- Home shows the most recent six conversation turns or every turn from the last 48 hours, whichever is greater. Each More click expands by another six turns or another 48 hours, whichever reveals more, and disappears when the full retained conversation is visible.
- The cache-busted website update was deployed to `mhm.jacfogel.com`. All 135 browser tests and all 40 website account-service tests pass.

### 2026-10-16 - Private logging and self-contained installs hardened **COMPLETED**
- Runtime logs no longer record user-authored message bodies; communication, AI, service, and response-tracking paths retain only safe operational metadata, backed by a static privacy regression guard.
- Package metadata now declares the runtime, UI, and development dependencies, includes shipped resources, styles, fonts, and website assets, and consistently supports Python 3.11 across metadata, CI, type checking, and setup documentation.
- Logger exception forwarding preserves traceback detail while supporting redacted exception messages. OAuth failures omit codes, state, tokens, and other secrets; shipped-resource path helpers now use centralized fail-fast error handling with failure-path tests.
- Risk-focused Discord and health tests cover unknown and returning users, blocked DMs, failed sends, account creation/linking outcomes, invalid health mutations, reauthentication, and route registration. The previously unreachable confirmation-code modal now opens from an ephemeral Discord button, validates six ASCII digits, and submits without exposing the identifier or code in logs. Focused branch coverage is 99% for inbound routing, 97% for onboarding, and 100% for health routes; the Tier 3 development-tools repair passes 1,665 tests, and Ruff and Pyright are clean.

### 2026-10-15 - Audit reruns stay scoped after setup errors **COMPLETED**
- Class-based JUnit results now map back to the real test file, so a few setup errors no longer force the next full audit to rerun every domain from the last suite.
- Pytest exit code 1 with setup errors is recorded as test failures. Session cleanup keeps a live `pytest_runner` tree, including worker folders that are still in use.
- Parallel workers now delete the test accounts they create. Each worker clears its own `tests/data/xdist_<worker>/` store at session start and end, and each test removes user directories it added. Missed user lookups were rereading about 3,000 leftover accounts and taking about 26 seconds. Listing those directories uses `os.listdir`, so a test that replaces `Path.iterdir` cannot fail teardown.
- The audit already running when this landed still uses the previous behavior. The following audit can shrink to the files that actually failed, and its workers start by deleting the leftover accounts.

### 2026-10-14 - User-data reads simplified and compatibility facades removed **COMPLETED**
- Split `get_user_data` into explicit request, existence-policy, loader, and payload-finalization phases; removed test-only loader healing and broad exception-driven fallbacks. The existence and document-load boundaries now use standard error decorators with safe defaults.
- Moved canonical user-ID validation into dependency-free `storage/user_id.py`; all callers now import it directly, eliminating both dependency cycles and the temporary validation-module re-export.
- Existing-user saves load current documents once and pass required snapshots into update validation. The implicit compatibility reader, metadata wrapper, and v2 schema/ID re-exports were removed.
- Regenerated the function registry with all five missing entries and no stale rows. Focused checks pass 14 read-path and 27 runner tests; Ruff is clean. The standalone changed-domain suite recorded 524 passes, zero failures, and zero errors before its 1,800-second limit; timeouts now report `pytest_timeout` instead of a generic crash reason. A threaded registry test now owns its patches outside worker threads, preventing leaked mocks that caused four order-dependent Tier 3 failures; the contaminating module plus all four regressions pass 50 tests.

### 2026-10-13 - Notebook saves, user paths, and audit status hardened **COMPLETED**
- Notebook PATCH requests now validate and persist the complete edited entry in one save, preventing partial title, body, checklist, or tag changes when a later operation fails.
- Account reads reuse canonical user-ID validation, resolved data paths must stay inside the users root, and debug logs record requested data types instead of personal record payloads.
- Static-analysis summaries now require fresh successful results from Ruff, Pyright, Bandit, pip-audit, and Vulture before reporting `CLEAN`; stale, missing, or incomplete evidence is labeled explicitly.
- Focused regression coverage passes 101 tests. The clean Tier 3 full audit passes 7,610 parallel and 123 no-parallel tests, reports 80.4% coverage and documentation sync PASS, and records zero findings from all five static-analysis tools.

### 2026-10-12 - User-facing failures explain recovery **COMPLETED**
- Website account, billing, and task failures now distinguish the failed action, state what remains unchanged or retained, and give a concrete retry, refresh, alternative, or escalation step.
- Task routes distinguish stale state from temporary service failure; browser network failures no longer expose raw diagnostics, and failed task drafts/edits remain available.
- Discord's Create menu now gives unlinked accounts, unavailable forms, and failed task/note submissions a specific recovery path; deferred note failures always receive a reply.
- Website notebook failures now distinguish stale entries from temporary save/state-change failures, retain failed drafts, hide raw network details, and tell users when to refresh before retrying an uncertain operation.
- Both Pyright warnings were cleared with explicit async-mock call narrowing. Generated documentation and audit reports now show zero registry gaps and Pyright PASS with zero warnings.
- Focused verification passes 44 account/billing gateway tests, 10 task-route tests, 24 account/task browser tests, 34 website page/asset tests, 22 Discord Create UI tests, 17 notebook route tests, and 13 notebook browser tests; the complete browser-script bridge, Ruff, and Pyright are clean.

## Archive Notes
Older detailed entries live in `development_docs/changelog_history/` and remain the historical source of truth. Use [CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md) for the latest detailed entries and the archive folder for month-split history.

