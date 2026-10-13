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

### 2026-10-12 - User-facing failures explain recovery **COMPLETED**
- Website account, billing, and task failures now distinguish the failed action, state what remains unchanged or retained, and give a concrete retry, refresh, alternative, or escalation step.
- Task routes distinguish stale state from temporary service failure; browser network failures no longer expose raw diagnostics, and failed task drafts/edits remain available.
- Discord's Create menu now gives unlinked accounts, unavailable forms, and failed task/note submissions a specific recovery path; deferred note failures always receive a reply.
- Website notebook failures now distinguish stale entries from temporary save/state-change failures, retain failed drafts, hide raw network details, and tell users when to refresh before retrying an uncertain operation.
- Both Pyright warnings were cleared with explicit async-mock call narrowing. Generated documentation and audit reports now show zero registry gaps and Pyright PASS with zero warnings.
- Focused verification passes 44 account/billing gateway tests, 10 task-route tests, 24 account/task browser tests, 34 website page/asset tests, 22 Discord Create UI tests, 17 notebook route tests, and 13 notebook browser tests; the complete browser-script bridge, Ruff, and Pyright are clean.

### 2026-10-10 - Billing follow-up checks restored **COMPLETED**
- Fixed the order-dependent development-tools classifier failure by preserving complete error-handling defaults when a worker loads partial external configuration and returning isolated nested settings to each caller.
- Fixed the Tier 3 xdist interruption caused by an account-creation test repeatedly scanning every accumulated account until the five-minute timeout killed its worker. The test now checks only the canonical account paths, and an unstarted no-parallel track is reported as skipped instead of inheriting the parallel crash.
- Made the website-chat gateway tests use a fresh account ID per test so retained xdist inbox data cannot duplicate conversation turns in a later run; removed an advisory link to an absent optional coverage snapshot.
- Fixed the remaining Pyright optional-value error in the billing portal test and regenerated the function registry/module references for the new billing functions.
- Verification: the repaired six-worker main track passes 5,931 tests with 1 skip using the former crash seed; the development-tools track passes 1,661 tests; focused config/error-handling tests pass 63 tests; Pyright reports 0 errors and Ruff is clean. The user-requested full audit was stopped and not rerun.

### 2026-10-09 - Stripe post-launch hardening **COMPLETED**
- Stripe webhooks now persist processed event IDs and reconcile each handled event against the current Subscription, so duplicate or delayed invoice events cannot regress access. Invoice events can resolve an account from Subscription metadata even if they arrive before Checkout completion.
- Hourly one-time notices warn before trial expiry and when trial, failed-payment grace, or cancellation pauses scheduled support. Delivery uses the account's preferred channel and keeps a website inbox copy.
- Onboarding now says when a near-expiry trial will be charged immediately. Live-mode cutover, canary, restart, and rollback steps are documented without changing production credentials.
- Verification: 36 focused billing/storage tests, 95 scheduler/delivery tests, and 127 browser tests pass.

### 2026-10-07 - Stripe trial billing and onboarding shipped **COMPLETED**
- New accounts receive a persisted 30-day trial and can start a CA$8.99 CAD monthly Stripe subscription through hosted Checkout; signed webhooks, Customer Portal sessions, and a three-day failed-payment grace period keep local entitlement state synchronized without storing card details.
- Scheduled messages, check-ins, and task reminders stop after trial/grace expiry or cancellation, while legacy accounts remain complimentary.
- Onboarding now explains the free-to-paid transition and offers Subscribe now or Continue with free trial. Account navigation opens the Account settings panel instead of Profile.
- Fixed the account-envelope allowlist that initially replaced new trial fields with complimentary defaults. Test-mode Stripe objects and the public Worker route are deployed and verified; focused checks pass 27 Python billing/storage tests and 123 browser tests, with broader backend and scheduler checks also green.

### 2026-10-06 - Disabled automated messages stay quiet **COMPLETED**
- Category messages are no longer scheduled or sent when automated messages are disabled. A job already queued for that account is dropped instead of sent.
- Check-ins and task reminders still follow their own switches.
- Restart the running service so an account that is already disabled stops receiving the messages queued by the current process.

### 2026-10-06 - Schedule saves keep every open period **COMPLETED**
- Website schedule saves, and the desktop schedule editor, ask the running service to rebuild that category the same way other schedule edits do.
- A period that still has time left today is scheduled inside the remaining window. It moves to tomorrow only after the window has ended.
- Sending one period leaves the other periods in that category on the schedule.
- Two sends conflict only when they are within five minutes, so neighboring windows such as morning and check-in can both go out.
- Restart the running service so it loads this scheduler. After that, save the schedule again if you want today's remaining windows queued.
- The period-window helper and the job-matching helpers now have docstrings and shared error handling, and the function registry includes them.

### 2026-10-06 - Error log limit, task routes, and task phrases **COMPLETED**
- `errors.log` now has one shared handler with the configured size limit, so component errors can rotate the file instead of growing past it.
- Website task handling is split into one method per action (list, create, update, complete, and the smaller task actions) with the same checks and responses.
- Due dates, times, priority, tags, links, and recurrence are read in `task_phrase_parser.py`. The command parser calls that module when it builds a task.
- The three shared-handler helpers are covered by the error decorator, logger tests close their files, and the task-phrase guide uses the full parser path.
- Size-rollover tests clear leftover backups, and fixture-label lookup uses the newest user so a second audit does not count old check-ins or old log files.
- Restart MHM so the running process picks up the shared error log. The current oversized `errors.log` rotates on the next error after that restart.

### 2026-10-06 - Discord concurrency, error recovery, and test diagnostics hardened **COMPLETED**
- Discord sends now use per-request futures without blocking the event loop, worker loops shut down cleanly, and connection-health probes close their sockets immediately.
- Error recovery no longer repeats side effects by default or disables later operations through a process-lifetime retry counter; retries are explicit, bounded, and omit call arguments from retained context.
- Test configuration now exposes ordinary warnings and fails on unhandled-thread, unraisable, unawaited-coroutine, and unclosed-resource defects, with focused Discord, health-route, and recovery regression coverage.
- Verification is clean: the scoped Tier 3 runner reports zero failures or errors, the focused Discord run passes 91 tests, and Ruff and Pyright report no findings.

### 2026-10-06 - Desktop request actions preserve account context and UI responsiveness **COMPLETED**
- Test-message requests no longer mutate the process-wide `UserContext`, preventing background polling from exposing or restoring the wrong active account.
- Check-in prompt response polling now runs through the same background Qt worker pattern as test messages, with duplicate-send protection and button-state recovery.
- Focused UI and behavior regression coverage verifies account isolation, background dispatch, and completion cleanup.
- Directory-tree generation now starts from Git-tracked and non-ignored files instead of trusting an unfiltered filesystem listing.
- `.env` variants, response flags, logs, data directories, process files, and runtime cache directories are always omitted, even if accidentally tracked.
- Regression coverage verifies that ignored secret-like files stay out while normal project files and `.env.example` remain documented.

### 2026-10-06 - Coverage isolation, dependency floors, and the last unmarked policy test **COMPLETED**
- Full coverage no longer collects `tests/development_tools/` in the host pytest process. Those tests run with `development_tools/pytest.ini`, and their coverage is combined into the main data. Development-tools-only coverage remains `python development_tools/tests/run_test_coverage.py --dev-tools-only`.
- Raised the urllib3 floor to 2.8.0 and pinned oauthlib at 4.0.0 or newer so the four pip-audit findings are covered.
- The policy test `test_run_tests_isolates_environment_before_core_imports` now inherits the unit category marker from its module.

### 2026-10-06 - Website browser coverage joins standard test gates **COMPLETED**
- Browser behavior coverage now spans 121 passing Node tests, with expanded check-in, insight, integration, message, notebook, settings, and task scenarios.
- A serial pytest bridge runs every `website/*.test.mjs` file in the normal suite, `audit --full`, and the nightly suite; PR and push checks retain a dedicated website job with Node.js 20.
- The audit cache now treats the standalone website as its own domain and invalidates browser coverage when JavaScript, HTML, CSS, or JSONC assets change.
- The completed full audit is clean: 5,980 passed and 28 skipped, with zero failures or errors across the parallel and no-parallel tracks.

### 2026-10-05 - Website workflows preserve intent and prevent duplicate actions **COMPLETED**
- Task, notebook, and scheduled-message drafts now warn before destructive navigation or dismissal; stale list, filter, category, and insight responses are ignored, with clearer contextual empty states and one-click notebook filter clearing.
- Home chat restores failed sends, Home task actions retain a stable target, and task, message, check-in, insight, integration, setup, and account actions use busy locks to prevent duplicate or overlapping requests.
- Google Health handles blocked popups and expired sessions consistently, while account and sign-in flows provide durable success feedback, specific progress states, normalized verification codes, and better focus recovery.
- Browser asset versions and regression coverage were expanded, including new message, insight, and integration suites. All 92 browser-script tests pass, focused website Python suites pass with 84 tests in the largest run, and JavaScript syntax and diff checks are clean.

### 2026-10-05 - Channel outages stay bounded and quiet **COMPLETED**
- Equivalent failed deliveries occupy one retry slot; failure remains bounded, success/exhaustion releases deduplication state, and a later recovery drains the pending delivery.
- Inbound email polling distinguishes an empty inbox from failure, backs off from 1 to 15 minutes during an outage, resets to 30 seconds on recovery, and logs only outage transitions.
- Discord startup task failures are consumed by the normal error path, and the log size limit overrides the recent-file guard while preserving repeated same-day rollovers under unique backup names.
- Expanded verification passes 161 communication tests and 108 logging tests plus Ruff, Pyright, `doc-sync`, and diff checks; planning now consistently marks website chat complete and the website guide no longer claims removed notebook group views.
- Live account-flow smoke testing confirmed signed-out routing and led to provider-aware sign-in/create UI: only configured providers appear, copy names the actual choices, email-only fallback stays clean, and all 71 website script tests pass.

### 2026-10-04 - Task templates and bulk priority changes shipped **COMPLETED**
- Website task settings can save, edit, and remove up to 20 validated personal templates; they appear in the website task picker alongside built-ins.
- `task template <name_with_underscores>` and template listing resolve only the active account's custom templates, while malformed saved definitions cannot disrupt built-ins.
- Selected active website tasks can now receive one validated priority through the account-scoped bulk endpoint and hosted-site proxy.
- The desktop/admin app now manages the same custom templates, prefills new tasks from built-in or personal templates, and changes priority for multiple selected active tasks.
- Custom-template validation now uses `ValidationError`, reference helpers use shared error handling, and the analyzers report zero undocumented functions, zero missing handlers, and zero Phase 1 or Phase 2 findings.
- Focused Python, Qt, and browser-script coverage verifies storage, validation, lookup, prefills, multi-select updates, endpoint exposure, and settings controls; Ruff and Pyright are clean. The complete suite passed after the template work with 6,053 passed and 28 skipped; the desktop parity run passes 688 UI/shared-task tests with 27 expected skips, and all 70 website script tests pass.

### 2026-10-04 - AI responses and Tier 3 tests hardened **COMPLETED**
- Response cleanup removes prompt/template leaks and letter signoffs, blocks unsupported action claims, and produces concise grounded replies for common direct requests; all seven reported personalized-response failures are fixed.
- Command-mode replies are normalized to structured output, ambiguous task creation asks for a title, and chat-mode text cannot claim an action executed when it did not.
- AI fixtures and the full-suite runner now isolate test identities, data, and logs; the retired production `internal_username` field was backed up, removed from the final account, and cleared from the rebuilt index.
- Generated registries are current with zero missing entries for `response_postprocess.py`. Verification passed 65 helper tests, 149 broader response tests, all 78 manually reviewed live AI tests, and the complete suite with 6,045 passed, 28 skipped, zero failures, and zero errors.

## Archive Notes
Older detailed entries live in `development_docs/changelog_history/` and remain the historical source of truth. Use [CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md) for the latest detailed entries and the archive folder for month-split history.

