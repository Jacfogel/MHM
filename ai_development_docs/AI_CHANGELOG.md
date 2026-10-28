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

## Archive Notes
Older detailed entries live in `development_docs/changelog_history/` and remain the historical source of truth. Use [CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md) for the latest detailed entries and the archive folder for month-split history.

