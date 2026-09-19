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

### 2026-09-15 - Website self-service expansion **COMPLETED**
- Added richer profile and phrase settings, personal message-template management, private check-in insights/history, Google Health controls, account connection removal, and a secret-scrubbed data export.
- Tasks support templates, snooze, skip, and simplify; notebook views include pinned and inbox filters. All operations reuse canonical MHM services and storage.
- Session, origin, allowlist, payload, and last-sign-in protections are covered by focused Python and Node tests. Check-in completion remains on the existing app interface by explicit request.
- Resolved all six reported website-account error-handling gaps; full-scope coverage is 2,520/2,520.
- Reproduced Tier 3's timeout: 5,513 tests completed without assertion failures and the remaining 67 passed separately. Full-audit concurrency remained productive past 30 minutes, so Tier 3 keeps a 60-minute phase ceiling plus a five-minute cleanup buffer; stalled Windows cleanup returns structured timeout diagnostics instead of crashing.
- Regenerated the function/dependency registries with zero missing entries and fixed the sole Pyright error; full Pyright, targeted tests, Ruff, docs checks, and the final Tier 3 full audit pass.

### 2026-09-15 - Dev-tools pytest isolation from host conftest **COMPLETED**
- Tools tests run with `development_tools/pytest.ini` (`confcutdir` stops `tests/conftest.py`). Host pytest ignores `tests/development_tools/`.
- Tier 3, coverage, and `run_tests.py --mode development_tools` pass the isolation flags. Host+tools pytest share one timeout budget so a slow host run cannot chain a second hour.
- Suite cache: runner/cache helper edits soft-invalidate (clear full snapshot + re-run `development_tools`); `domain_mapper`/config edits still bust all domains.
- Hour-long tools pytest root cause fixed: report tests mocked every `Path.exists()` call as true, trapping file rotation in an infinite collision loop that Windows' thread timeout could not terminate. Timeout diagnostics now survive cache merging, interrupted phases stop immediately, and quick audits have a 15-minute phase cap. The full tools phase now passes, and a clean full audit completes in about 7 minutes.
- Remaining extraction: report paths, optional install extra, then sibling repo.

### 2026-09-15 - Password and social website sign-in **COMPLETED**
- New accounts choose a 12-128 character password after one-time email verification; existing accounts can set or change one after signing in by code. Salted scrypt hashes are stored in the canonical account document, with rate-limited password login and code fallback.
- Added configurable Google, Facebook, and Apple sign-in/linking with one-time state, provider subject uniqueness, verified-email matching, no provider token storage, and Apple form-post/JWT verification support through the Worker.
- Updated the account UI, configuration examples, gateway/Worker routes, account schema, and focused Python/Node coverage.

### 2026-09-15 - Task reminder skip and simplify **COMPLETED**
- Discord reminder **Skip** and **Simplify** are live, separate from snooze.
- Skip rolls a repeating task to the next occurrence without marking it done; one-off tasks stay due and wait until tomorrow morning.
- Simplify rewrites the title to a smaller next step and keeps the due date.
- Hygiene: snooze helper now uses `@handle_errors`; spec ASCII; function registry regenerated.

### 2026-09-14 - Task reminder snooze **COMPLETED**
- Discord **Remind Me Later** snoozes the ping (1 hour / tonight or tomorrow morning / next week / custom) without changing the due date.
- Same path from typed `snooze` / `remind me later` commands. Skip and Simplify remain later, separate actions.

### 2026-09-14 - Website accounts, user settings, and integrated gateway **COMPLETED**
- Email-code accounts and Discord OAuth use the existing MHM user store with expiring HttpOnly sessions, origin checks, one-time state, and duplicate-link protection; signed-in users can safely edit Profile, Delivery, Messages, Tasks, and Check-ins settings.
- Added separate website workspaces for task CRUD and for notes, journal entries, and lists, including tags and scheduled task-reminder windows. The supplied bot icon now anchors the MHM / Motivational Health Messages branding and the site explains its randomized-message-window approach.
- The service-owned gateway, Cloudflare Worker routing, logout/session behavior, validation, typed errors, and error-handling boundaries were hardened. Function docs and registries are complete; the full audit reports clean docstrings/error handling, Ruff, Pyright, and Tier 3 tests.
- Tier 3 now has a 60-minute subprocess window instead of falsely crashing at 22 minutes. Real failures found after the timeout were fixed, stateful storage tests run serially, and newly identified long tests are marked `slow` so normal runs skip them while the existing nightly suite includes them.

### 2026-09-13 - Dev-tools logical split: host backup adapter and host import boundary **COMPLETED**
- Backup drill/health load `host.backup_manager_module` via `shared/host_hooks.py`; empty module skips. MHM config still points at `core.backup_manager`.
- Import boundary now forbids all host prefixes from `local_module_prefixes` except `development_tools`.
- Extraction remaining work (tests, report paths, later sibling repo) is in PLANS.md Section 6.4.
- Hygiene: Ruff SIM103/B009, ASCII Section replacements, regenerated function registry for `_combined_message`. Host-hook test asserts `list_backups()` so Pyright does not warn on a dummy `marker` attribute.

### 2026-09-12 - Google Health token expiry uses local time and 401 retries **COMPLETED**
- Access-token `expires_at` is stored from the local clock, matching the refresh check (UTC storage made a 1-hour token look valid for extra hours in Regina).
- HTTP 401 on health reads now force-refreshes once and retries instead of recording an empty successful sync.
- Targeted tests: 97 passed (`test_google_health_auth.py`, `client.py`, `sync_manager.py`, `notifications.py`).
- `DiscordReconnectNoiseFilter` drops discord.py reconnect/DNS ERROR spam from `errors.log`; MHM disconnect lines stay in `discord.log`.

### 2026-09-05 - Dev-tools report tests and trustworthy coverage refresh **COMPLETED**
- Added issue-payload tests for AI_STATUS / AI_PRIORITIES / CONSOLIDATED and remaining error-handling analyzer helpers (consolidated 31%->73%, status 42%->66%, priorities 54%->75%, error handling 54%->81%).
- Incomplete coverage runs no longer replace the published snapshot: keep `coverage_last_good.json` at 60%+, ignore stray Ctrl+C until 5 taps in 2s, and start Windows pytest with `CREATE_NO_WINDOW` so xdist workers are not killed.
- Refresh with `python development_tools/tests/run_test_coverage.py` (not `--no-domain-cache`, not the skipping `coverage` wrapper). Successful pass: overall 80.2%, `development_tools` 72.9%; then `audit`. Added the missing H2 `Recent Changes (Most Recent First)` to CHANGELOG_DETAIL so the pair matches.
- Cleared the 2 remaining Pyright warnings: `_percent_covered_from_totals` returns early when `percent_covered` is missing instead of passing `None` to `float()`.

### 2026-09-03 - Clear Pyright warnings on profile-settings tests **COMPLETED**
- The three remaining Pyright warnings were `reportAttributeAccessIssue` on `lineEdit_preferred_name` in `tests/ui/test_user_profile_settings_widget.py`.
- That field is created at runtime in `UserProfileSettingsWidget.__init__`, not in the generated UI class; the test file now uses the same Pyright suppression as the widget.
- `python -m pyright tests/ui/test_user_profile_settings_widget.py` should report 0 errors / 0 warnings after this.

### 2026-09-02 - UI coverage for Health, phrase settings, and admin actions **COMPLETED**
- Added behavior tests for the previously uncovered Google Health settings dialog, phrase-settings widget/dialog, and remaining admin-action helpers (log file, cache cleanup, config report, health check).
- Expanded coverage for dialog openers, channel-status log paths, request-file actions, channel-selection widget, and service force-stop.
- Added profile-settings load/save, task-completion AM/PM conversion, and dynamic-list field row helpers.
- Targeted UI tests passed (44, then 80, then 17 on the latest slice). Domain `ui` still needs a coverage refresh to update the 72.4% report figure.

### 2026-09-01 - Nightly safe JSON read no longer returns an empty object **COMPLETED**
- Linux `file_lock` now flocks a sidecar `.lock` file and opens the JSON after that, so a locked data fd cannot look empty.
- `safe_json_read` rereads the path when the locked handle is empty but the file still has bytes.
- Existing-file read tests use pytest `tmp_path`; added a stale-handle fallback case.

## Archive Notes
Older detailed entries live in `development_docs/changelog_history/` and remain the historical source of truth. Use [CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md) for the latest detailed entries and the archive folder for month-split history.

