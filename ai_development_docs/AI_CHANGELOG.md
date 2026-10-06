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

### 2026-10-02 - Website route families extracted **COMPLETED**
- Reusable scheduled-message CRUD endpoints moved from the oversized `WebGateway` into `core/web_messages.py` without changing their URLs, validation, account ownership, or responses.
- The account service delegates message route registration, with centralized startup error reporting and focused route-owner tests.
- Website chat send, inbox, and reaction endpoints moved from the oversized `WebGateway` into `core/web_chat.py`, beside the existing conversation reply helpers.
- The account service delegates chat route registration while preserving the existing URLs, authentication, throttling, persistence, and response behavior.
- Route initialization and registration use centralized, re-raising error handling with focused regression coverage.
- Task CRUD, bulk actions, templates, effort estimates, and the shared export serializer moved into `core/web_tasks.py`; all existing task URLs and behavior remain unchanged.
- `WebGateway` is roughly 570 lines smaller, and the former highest-complexity route now has a focused owner backed by the existing task lifecycle suite.
- The complete suite passes: 5,974 passed, 28 skipped, with zero failures, errors, or warnings.
- Self-service settings and authenticated insights endpoints moved into `core/web_settings.py`; the existing settings transformation helpers remain in `core/web_user_settings.py` and setup completion is shared without duplication.
- Google Health integration endpoints moved into `core/web_health.py`, and allowlisted public asset/font routes moved into `core/web_assets.py`; URLs, health actions, responses, route order, and file allowlists are unchanged.
- Focused ownership and behavior coverage accompanies both new route owners; all 127 web-service tests pass, Ruff and Pyright are clean, and the complete suite passes with 5,981 passed and 28 skipped.

### 2026-10-02 - Website routes extracted and test fixtures aligned **COMPLETED**
- Check-in and notebook endpoints moved from the oversized `WebGateway` into focused route modules; the account service now delegates their registration and reuses the notebook serializer.
- Route-family initialization and registration use centralized, re-raising error handling, with focused coverage for routing, validation, lifecycle behavior, and error reporting.
- Behavior tests resolve factory-only labels through `TestUserFactory`, so analytics, AI-envelope, conversation, and user-context coverage no longer depends on the retired production username lookup.
- Generated function/dependency documentation was refreshed. The normal full suite passes: 5,966 passed, 28 skipped, with zero failures or errors.

### 2026-10-01 - Internal account username compatibility field retired **COMPLETED**
- Account identity now uses canonical UUIDs and optional contact identifiers; preferred names remain display-only.
- Removed the compatibility field from schemas, persistence, lookups, indexes, admin/UI flows, prompts, and test fixtures.
- Existing account files require the documented backup, migration, and index-rebuild step before normal reads.

### 2026-10-01 - Linux locks clean up after themselves **COMPLETED**
- Unix file locks remove their `.lock` sidecar on release, so user directories no longer keep `account.json.lock` and similar files.
- The frozen-clock lock test times only its body, so session cleanup cannot trip the 5-second limit.
- Unix lock tests restore the real `fcntl` module before reload, so a busy-lock stand-in cannot make later JSON reads return `{}`.

### 2026-09-30 - Delivery and reply state fail safely **COMPLETED**
- Channels accept only explicit success or `unconfirmed`; unexpected truthy results remain failed and retryable.
- Email reply context is updated transactionally and must be stored before SMTP starts. Save failures are no longer reported as success.
- IMAP duplicate and acknowledgement identity includes UIDVALIDITY, so a rebuilt mailbox cannot reuse an old UID as the same message.
- Windows JSON locks use a crash-safe OS byte lock with same-thread re-entry. Focused verification passed 201 tests; Ruff, Pyright, and diff checks passed.

### 2026-09-30 - Inbound mail stays attached to the right message **COMPLETED**
- Incoming mail uses stable IMAP UIDs, processes the oldest unread batch first, and retries one temporary mailbox disconnect without changing the application's global network timeout.
- A handled email is marked complete only after the server confirms `\\Seen`. If that acknowledgement fails, later polls retry it without sending the reply again.
- Encoded subjects retain every fragment and declared charset. Pyright is clean after correcting the IMAP call and scheduler positional-argument lookup.
- Focused email, message-processing, orchestrator, and scheduler suites passed; Ruff and diff checks passed.

### 2026-09-30 - Website delivery records stay exact and concurrent-safe **COMPLETED**
- Scheduled messages are copied to Home only after an accepted or unconfirmed handoff. Sent history and the website row share one exact delivery ID; repeated text no longer redirects reactions to the newest copy.
- JSON writes use unique temporary files and locked read-modify-write transactions. Failed sent-history writes return failure. A backed-up manual migration linked 83 legacy rows; seven check-ins and one task reminder remain intentionally non-reactable.
- Note requests allow 128 KiB end to end, enough for a valid 10,000-character Unicode description.
- All new transaction helpers use centralized error handling. Generated registries were refreshed, and the standard audit reports 100% error-handling coverage with no missing handlers, Phase 1/2 candidates, or registry watch items.

## Archive Notes
Older detailed entries live in `development_docs/changelog_history/` and remain the historical source of truth. Use [CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md) for the latest detailed entries and the archive folder for month-split history.

