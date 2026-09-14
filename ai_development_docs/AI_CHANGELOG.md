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

### 2026-09-14 - Website accounts, user settings, and integrated gateway **COMPLETED**
- Email-code login and account creation use the existing MHM user store; one account per email and expiring HttpOnly sessions. Discord OAuth2 links verified identities through server-side code exchange, one-time state bound to the original session, and duplicate-link rejection; SameSite=Lax permits the Discord return redirect while POST Origin checks remain enforced.
- Signed-in users can save Profile, Delivery, Messages, Tasks, and Check-ins settings with field validation, preserved unrelated data, stale-section detection, and mobile forms.
- `python run_headless_service.py start` starts the gateway with the background service; admin Start/Stop/Restart share that lifecycle. Wrangler defines the published gateway origin, preserves dashboard variables, and enables `global_fetch_strictly_public` for same-zone tunnel routing. The public tunnel responds, but the website currently catches a gateway-request failure; the routing change needs deployment and verification. Local Wrangler is not authenticated.
- Logout checks drafts before revocation, releases navigation guards on logout/session expiry, and restores the button after failures. Targeted Python tests, all 11 Node tests, and browser settings/logout checks passed.

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

### 2026-09-01 - Completing a task no longer leaves a duplicate active copy **COMPLETED**
- `complete_task` and `restore_task` now write active and completed lists in one save, so a leftover task cannot reappear as still active after a successful complete.
- "That" after completing a different recent task still resolves to no task, instead of the leftover.

### 2026-08-31 - Google Health coverage for connect, auth, and notices **COMPLETED**
- Unit tests now cover OAuth connect/refresh, user settings, health JSON recovery, reconnect notices, and the Google Health HTTP client (pagination, rollup fallback, parsers, sleep/steps/active-minute merges).
- Google Health tests: 156 passed; `integrations` measured at 95% on that set. `client.py` is 99%; remaining gap is mostly `signal_builder.py` / `sync_manager.py` edge cases.
- Coverage cache no longer treats a selective product-domain run as a full snapshot: missing cache does not imply a full run, tool/config invalidation keeps the merge base, and 0% `development_tools` from unrun tests is merged back from the prior JSON.
- Coverage pytest waits ignore spurious Windows SIGINT/control events (same multi-tap stop as audit: 5 Ctrl+C within 2s). A stray console event no longer aborts `--dev-tools-only` at 0%. Dev-tools coverage tests now stub `_run_pytest_wait`; changelog ASCII quotes restored.

### 2026-08-30 - Create hub splits tasks from notes **COMPLETED**
- Discord `create` hub first row is Call, Clean, Forms, Custom task; second row is green notes. Meds/Appt stay on `list task templates`.
- Call and Clean forms prefill title `Call` / `Clean` with due `this week`.
- Copy is "First row starts a task." (green note buttons are unlabeled).

### 2026-08-30 - Task CRUD multi-select and completed-task delete **COMPLETED**
- Completed-tab **Delete Permanently** failed because `delete_task` only searched active tasks.
- Task tables now allow Ctrl/Shift multi-select; delete, restore, and complete apply to all selected rows.
- Category column is filled in both tables.

### 2026-08-29 - Discord appointment form submit no longer fails silently **COMPLETED**
- `create` hub copy labels the first row as new-task buttons and green as notes; the template keyword list is not repeated under the buttons.
- Task-list Show More now attaches the picker dropdown on later pages (`deliver_handler_response` resolves `interaction_view`).
- Create-hub nested modal `__init__` methods use `@handle_errors`; function registry regenerated.
- Create-hub task modals use a stable `create_hub_modal_task:{template}` custom id, `timeout=None`, and the Discord interaction router handles `modal_submit` even after restart or the in-memory 3-minute modal timeout.

### 2026-08-28 - Chat follow-ups can update the task you just mentioned **COMPLETED**
- `make that due tomorrow`, `that's urgent`, and `mark that done` apply to the recently mentioned or created task.
- Ambiguous "that" asks which task; it does not jump to a leftover task after you complete a different one.
- Thinking-out-loud (`i should...`, `i gotta...`) asks before saving; `dont forget to` still creates immediately.
- Bot copy says "task list", not "list", so tasks stay distinct from notebook lists.
- After a which-task prompt, a number or name applies the remembered update (`1.` no longer gets the unclear-chat reply).
- Notes added during the due-date follow-up stay on that task and keep the due-date buttons.
- Function registry regenerated; yes/no offer matchers folded into `_matches_task_offer_reply`.

### 2026-08-27 - Tasks can store web links **COMPLETED**
- Tasks keep http(s) URLs in a `links` field, with add/remove commands and create-time URL capture.
- Labels are optional (`add the portal link to the dentist task: https://...`).
- Nested URL-strip callback lifted to `_replace_url_match` (docstring + error handling); function registry refreshed.
- File/image attachments are still deferred.

### 2026-08-26 - Chat follow-ups can create the task you just described **COMPLETED**
- Action planner includes up to two recent user turns so "yeah add that as a task" can reuse a title you already said.
- Titles still must match those recent words (example titles like "pack hiking bag" stay blocked).
- Compact planning prompt is unchanged besides that short recent-turn block.

## Archive Notes
Older detailed entries live in `development_docs/changelog_history/` and remain the historical source of truth. Use [CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md) for the latest detailed entries and the archive folder for month-split history.

