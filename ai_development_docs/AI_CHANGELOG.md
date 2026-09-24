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

### 2026-09-24 - Talk to MHM on the home page **COMPLETED**
- Home chat lists action names only, and leaves out actions for features that are turned off, so the prompt fits a 2048-token model. The notebook title field uses the rest of the create row. Ordinary website use is allowed 240 API calls per 10 minutes instead of 60. A website check-in saves when the check-in file is an empty list. Notebook replies no longer crash when an entry has no metadata, and the unused website inbox helper is gone. Insights says sleep length is not recorded yet instead of null hours, and Answer a check-in uses the same button as Home. Message creation keeps the message visible and tucks days and reminder windows behind More options. Every day and Any reminder window stay in step with the individual choices. Scheduled Discord messages use More like this and Not for me buttons instead of the bot adding both thumbs. Those buttons use the shared error handler. Account and Integrations are choices in the account side list. A scheduled check-in no longer replaces one that is still open, so an email reply is scored for the question in that email. Home chat shows the date and time on each message.
- The signed-in home page sends a message through `handle_user_message` as the `website` channel and shows the reply plus suggestion buttons.
- Your messages on Home use the preferred name when one is set. Account is the last page tab, and Log out is a dark button separate from the tabs. Extra home-page instructions are gone. Check-in is no longer a tab. Opening it from Home starts at the first question. The check-in page says MHM can send you one from Home. Discord linking is only on delivery settings. CPAP use is no longer a question template. Password and data download are on Account settings. The task list sits under the create form. Extra task and notebook instructions are gone. The notebook page no longer has groups. Notebook creation starts with the type and title. The notebook does not show who is signed in. Turned-off task reminders and check-ins link to those settings. The logo line stays on one line when the header has room. Check-in answer types are yes/no, 1 to 5, time, time pair, and text. A text answer is also saved as a check-in journal entry. Illegal check-in question counts reset to a legal minimum and maximum. With Sometimes questions, the maximum stays above the number of Always questions. Custom questions have no templates and no minimum or maximum fields. The public site proxy allows `/api/chat`. The website is an always-on extra delivery channel. Scheduled messages, check-ins, task reminders, and health notices are copied into the website inbox and shown on Home, while email or Discord delivery stays in place. Turning every support feature off no longer returns the account to setup. Insights shows only while check-ins are on. Google Health is on Integrations, opened from Account settings.
- An open check-in or task flow stays in charge. The typed transcript lasts for the browser visit and clears on logout.

### 2026-09-23 - Website check-ins, groups, and custom snooze **COMPLETED**
- Notebook groups are tabs again, and entries can be assigned or cleared from those groups.
- The Check-in page starts, answers, skips, and cancels a check-in in the browser. Task help accepts a typed reminder time.
- Talk to MHM on the website is planned in [PLANS.md](../development_docs/PLANS.md) Section 7.4 and is not built yet.
- Scheduled Discord messages no longer repeat themselves in an embed. The reaction flag only adds thumbs. The two check-in Pyright warnings are cleared.
- The first question starts on its own line after the opening, and later questions start on their own line after the transition phrase. The website answer box clears for the next question. Scale questions offer 1-5 and yes/no questions offer Yes and No, without a text box. Sleep times use dropdowns. Other typed questions still use the text box. Home shows an open check-in. Logging out drops an in-progress check-in. An idle check-in expires after the same two hours used by Discord and email. Check-in, Tasks, and Messages tabs show only when that feature is enabled. Tasks stay available, like the notebook. Home and Insights hide check-in actions when check-ins are off, and the Messages tab hides when messages are off.

### 2026-09-23 - Two-way email replies **COMPLETED**
- A reply keeps the new text, stays in the same email thread, and the inbox message is marked read only after MHM handles it.
- Replying to a check-in answers that check-in. Replying to a task reminder with done, later, skip, or simplify to a real smaller step applies to that task. The words after "to" become the new title.
- Behavior is specified in [email-reply-loop.md](../specs/email-reply-loop.md).
- The communication guide path, function registry, and Pyright check for this reply code are clean.

### 2026-09-22 - Planned SMS, Apple Health, and subscription scaffolds **COMPLETED**
- [PLANS.md](../development_docs/PLANS.md) Section 7 records SMS, Apple Health ingest, and a 30-day trial then monthly subscription as **PLANNED**. None of that behavior is implemented.
- SMS uses a paid provider. Apple Health is a phone push into the existing daily-summary path. The alpha account stays comped when billing exists.

### 2026-09-22 - Google sign-in creates accounts; Apple sign-in removed **COMPLETED**
- A verified Google email, or a Facebook profile that shares an email, now creates an MHM account when that address is new, then opens first-run setup.
- An address that already belongs to an active account still signs into that account. Facebook without an email does not create an account.
- Apple website sign-in, its settings, and its callback are removed. Google and Facebook remain.
- First-run setup requires one of messages, tasks, or check-ins, and it no longer force-enables task reminders. Each feature left on gets its own category, question, or task step, plus a reminder-window step.
- Setup can connect Discord and return to setup. Skipping it keeps email delivery and leaves Discord-only buttons and message reactions unavailable. Custom check-in questions and personalized message categories are added later in Account.

### 2026-09-22 - Website privacy, terms, and data pages **COMPLETED**
- Public privacy, terms, and data pages now explain what MHM stores, that it is not medical care, and how to download or request deletion.
- Home, login, and the account card link to them. The gateway and Worker allowlists serve the new files.

### 2026-09-21 - Discord thumbs reactions steer scheduled messages **COMPLETED**
- Thumbs up on a scheduled Discord message adds similar library messages, or steers later personalized messages toward that one.
- Thumbs down retires that exact message so selection and personalized generation stop using it.
- Scheduled Discord sends store the Discord message id and offer the two reactions. Check-in questions ignore both reactions.

### 2026-09-21 - Website first-run helpers follow shared error handling **COMPLETED**
- Website first-run helpers now use `@handle_errors` with safe defaults so a broken account document cannot crash login routing.
- Changelog ASCII quotes and the [TODO.md](../TODO.md) instruction link are cleaned up.

### 2026-09-20 - Compact website navigation and simpler task creation **COMPLETED**
- After login, the website lands on Home (next task, check-in request, notebook capture). Home warns when task reminders or check-ins are off. New accounts, and any account with messages, tasks, and check-ins all off, get a 3-step first run even if `needs_setup` is missing from the account summary. Home/setup scripts are page-scoped so they load with `app.js`.
- Signed-in and marketing pages now use a Menu control below 1080px so destinations stay reachable, including Create account on small phones.
- The task list is shown first; extra create fields stay behind More options unless a template fills them.
- Notebook search labels use a real `.sr-only` style, and disabled buttons no longer look like they are loading.

### 2026-09-20 - Nightly suite workers no longer leak communication event loops **COMPLETED**
- CommunicationManager now stops tracked event-loop threads on shutdown, including loops abandoned when tests clear the singleton.
- Linux pytest-timeout uses `signal` so hung tests abort at 300s; nightly output keeps the timeout-dump start so the hung thread is visible.
- The GitHub summary script indent is restored, and the serial check-in UI test expects Minimum to clamp to 1 for one Always plus one Sometimes question.

### 2026-09-20 - Verified password recovery and transparent mood trends **COMPLETED**
- Added a forgot-password flow that verifies the account by emailed code, replaces the password, revokes older sessions, and signs the recovered account in without revealing whether unknown emails exist.
- Website mood insights now explain that the trend compares the latest seven mood ratings with the previous seven, show progress until 14 ratings exist, and distinguish missing mood answers from missing check-ins.
- Focused Python and browser/Worker coverage validates recovery, safe unknown-account behavior, trend readiness, and the updated login controls.

### 2026-09-19 - Desktop and website data-safety parity **COMPLETED**
- Desktop tasks preserve urgent priority and can explicitly clear recurrence; message templates preserve custom/ALL schedules and active state.
- Message delivery matches website day codes case-insensitively and excludes paused templates. General and future custom check-in categories remain visible.
- Structured important-person profiles round-trip without flattening or dropping metadata. Focused validation passed 81 tests plus Ruff and compilation; 19 check-in UI tests are platform-skipped on Windows.

### 2026-09-19 - Domain cache invalidation no longer fans out from core **COMPLETED**
- Test-file cache lookups now use forward-slash paths, so Windows no longer treats cached unit tests as new whenever core changes. Keyword fallback uses the project-relative path so parent folders cannot steal extra domains.
- Core maps to `tests/core/` and `@pytest.mark.core` only; `domain_dependencies` no longer expands a core edit across the product.
- Targeted coverage-cache and suite-cache tests cover the new selection rules.
- Tier 2 error-handling, function-registry, package-exports, and module-imports now reuse the shared function-scan AST in-process instead of re-parsing (or spawning a subprocess) after `analyze_functions`.
- Function-registry still inventories excluded root key files (`run_mhm.py`, `run_tests.py`). Check-in start tests pin always-include questions so the leave-one-out min/max rule is deterministic.
- The shared-scan wrapper test patches `_module_import_analyzer_class` on the running wrapper's globals so xdist cannot miss a second `analyze_module_imports` copy.
- The hostile analyzer in that regression test no longer iterates an optional `parsed_modules` value, clearing the remaining Pyright error.

### 2026-09-19 - Website, task, check-in, and notebook consistency fixes **COMPLETED**
- Automated messages now stay disabled when category preferences are saved. Check-ins default to 2-3 questions, apply the variability constraint to Minimum instead of Maximum, and select a count within that range at runtime across the website and desktop app.
- Default task tags now populate creation/editing, notebook forms have working existing-tag selectors, notebook groups are retired from the website/API, and archived notebook entries cannot retain or display a pinned state.
- Custom task reminders accept a single date/time with an optional window end; relative reminders require a due date during creation and editing.
- Added the missing `get_default_tags` error boundary and registry entry. Focused Python/Node tests, Ruff, compilation, docs regeneration, and the error-handling analyzer pass; two stale Tier 3 expectations were corrected and their parallel/no-parallel suites pass.
- Removed `confcutdir` from `development_tools/pytest.ini`; pytest only accepts `--confcutdir` and `--strict-config` treated the INI key as unknown, so CI Tooling Policy Consistency ran zero tests.
- Isolation tests now require the CLI flag and forbid the INI assignment.
- Suite-cache helper edits always rerun the `development_tools` domain, even when a worker's domain map omitted that key.

### 2026-09-17 - Website account and settings corrections **COMPLETED**
- Account navigation no longer signs users out; profile lists accept lines, commas, or semicolons; clicking anywhere in date/time inputs opens the native picker; and disabled feature details are visibly unavailable.
- Personalized messages are split into check-in, Google Health, and profile sources, with source-dependent availability. Check-ins support custom questions, group standard questions by category with compact inline frequency controls, and default new check-in/task windows to 9:30-11:30 AM and 3:00-5:00 PM.
- Newly created accounts immediately require the current password for later changes. Discord connection failures now explain likely duplicate-account links, and account creation no longer silently starts Discord linking.
- Website settings now require the complete current response schema, and saved custom questions require the current full definition instead of being repaired from older partial shapes. Related legacy facades were removed, and focused Python/Node coverage rejects obsolete payloads.
- Website parity now includes the complete custom-question editor and structured important-people profiles; task completion details, recurrence intervals, relative reminders, bulk actions, and due-soon counts; fuller wellness analytics; notebook group/tag browsing; live message previews; and manual test-message and check-in requests. The task-level Remind now action was removed.
- Task recurrence now hides irrelevant controls for one-time tasks and uses clear presets plus a custom number/unit editor. Suggested and date-specific task reminders share one editor, choosing the blank template clears populated task fields, and task creation/editing provide an explicit existing-tag selector while still accepting new tags. Notebook tag and group fields continue suggesting existing values. Structured task links were removed from the website API; ordinary URLs belong in task Details.
- A Tier 3 timeout at 99% with no named failures no longer wipes the suite cache or forces a 348-file rerun; interrupted pytest keeps prior per-file results and useful worker-crash diagnostics. Website tests now cap aiohttp server shutdown at 1 second so leftover connections cannot stall workers for a minute each.
- The web-client shutdown test no longer triggers a Pyright optional-member warning on `runner._shutdown_timeout`.

## Archive Notes
Older detailed entries live in `development_docs/changelog_history/` and remain the historical source of truth. Use [CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md) for the latest detailed entries and the archive folder for month-split history.

