# Manual Testing Guide

> **File**: `tests/MANUAL_TESTING_GUIDE.md`  
> **Audience**: Developers and AI assistants performing manual testing  
> **Purpose**: Canonical manual testing flows and checklists across channels and features  
> **Style**: Checklist-first, concise but detailed  
> **Parent**: [TESTING_GUIDE.md](TESTING_GUIDE.md)  
> This document is subordinate to [TESTING_GUIDE.md](TESTING_GUIDE.md) and should be kept consistent with its standards and terminology.

---

## 1. Purpose and Scope

Automated tests are the primary safety net for MHM, but they cannot cover every scenario-especially those involving live inboxes, OAuth, visual layout, and nuanced user experience.

This guide defines:

- When manual testing is required.
- Which manual flows must be exercised.
- How those flows map to pytest (section 10).
- How to run remaining live checks across UI, scheduling, reminders, email, Discord, Google Health, and AI tone.
- How to record and report the results.

Use this guide:

- Before tagging a release.
- After significant changes to scheduling, messaging, AI behavior, or UI.
- When fixing bugs that are primarily UX or integration issues.

For the overall testing framework (layout, markers, automation, coverage), use:

- [TESTING_GUIDE.md](TESTING_GUIDE.md) (automation-focused).
- [AI_TESTING_GUIDE.md](../ai_development_docs/AI_TESTING_GUIDE.md) (AI routing and constraints).

---

## 2. Core Manual Flows

These flows should be validated in every full manual test pass, regardless of which channel or feature you are changing.

### 2.1. Application startup and shutdown

Checklist:

- [ ] Start the app using the documented entry point (for example, `python run_mhm.py` or equivalent).
- [ ] Confirm that:
  - [ ] The main window or headless service starts without uncaught exceptions.
  - [ ] Logs show a clean startup sequence (no critical or unexpected errors).
- [ ] Shut down the application using the normal mechanisms (UI exit button or service stop command).
- [ ] Confirm that:
  - [ ] No orphan processes remain.
  - [ ] Shutdown logs show a clean termination.

Notes:

- There is no tray icon today; skip tray shutdown until one exists.
- If any unexpected warnings or errors appear in logs, capture them and decide whether they are acceptable or must be fixed.
- If shutdown hangs or requires forced termination, file an issue.
- After startup/shutdown code changes, run the mapped pytest in section 10.1 before a live start/stop pass.

### 2.2. Basic configuration and environment

Checklist:

- [ ] Environment variables and `.env` configuration are loaded correctly (no missing mandatory settings). For detailed setting meanings and common failure modes, use [CONFIGURATION_REFERENCE.md](../CONFIGURATION_REFERENCE.md).
- [ ] The app detects required external tools or services (for example, Discord API credentials if enabled).
- [ ] Configuration error messages, if triggered, are clear and actionable.

If configuration changes are part of your work, you must explicitly verify that misconfiguration leads to clear, recoverable outcomes.

---

## 3. UI Manual Testing

This section applies when the Qt UI is used or changed. If you are running headless only, you can skip this section, but **any change to UI code requires these checks**.

### 3.1. Layout and visual checks

Checklist:

- [ ] All dialogs open without errors.
- [ ] Dialog sizes are reasonable on a normal desktop resolution.
- [ ] Labels and controls are aligned and readable.
- [ ] Buttons and controls use consistent naming and styling.

### 3.2. Navigation and interaction

Checklist:

- [ ] Tab order proceeds in a logical sequence for all major dialogs.
- [ ] Keyboard shortcuts (Enter, Escape, common accelerators) behave as expected.
- [ ] Close/cancel actions do not commit changes inadvertently.
- [ ] Menu items and toolbar buttons (if present) trigger the correct actions.

### 3.3. Validation and error feedback

Checklist:

- [ ] Invalid inputs (empty required fields, invalid time ranges, malformed values) are rejected.
- [ ] Error messages are:
  - [ ] Clear.
  - [ ] Specific.
  - [ ] Shown near the relevant UI elements where possible.
- [ ] Valid inputs are accepted without spurious warnings.

Record any confusing or misleading validation behavior and treat it as a UX defect.

---

## 4. Scheduling & Reminder Manual Tests

These flows cover the heart of MHM: schedule configuration and reminder behavior.

### 4.1. Creating and editing schedule periods

Checklist:

- [ ] Create at least one schedule period (for example, "Morning", "Afternoon").
- [ ] Verify:
  - [ ] Time ranges are correctly stored.
  - [ ] Overlapping or invalid ranges are handled according to design (either prevented or clearly warned).
- [ ] Edit an existing schedule period:
  - [ ] Change its name and time range.
  - [ ] Confirm changes persist after restart.
- [ ] Delete a schedule period:
  - [ ] Confirm it is removed from any views.
  - [ ] Confirm messages tied to it handle the removal correctly (no crashes, no orphan state).

### 4.2. Creating and delivering reminders

Checklist:

- [ ] Create reminders associated with one or more schedule periods.
- [ ] Confirm:
  - [ ] Reminders are eligible to send only during valid periods.
  - [ ] Messages are not sent outside defined time windows.
- [ ] Trigger the reminder sending mechanism (real or simulated time; use tooling or configuration as available).
- [ ] Verify:
  - [ ] Messages are delivered on the expected channel(s).
  - [ ] Any UI reflecting reminder status is updated correctly.

### 4.3. Editing, snoozing, cancelling

Checklist:

- [ ] Edit an existing reminder (change text, schedule periods, or metadata).
- [ ] Confirm the updated reminder behaves correctly on the next send time.
- [ ] Snooze / "Remind Me Later" reschedule is **N/A** until that feature exists (the Discord button currently only acknowledges).
- [ ] Cancel/remove a reminder:
  - [ ] Confirm it no longer sends.
  - [ ] Confirm dependent UI and internal state are updated.

Any discrepancy (duplicates, missed reminders, reminders firing at the wrong time) must be treated as a priority defect.

---

## 5. Email Manual Tests

If email delivery is enabled in your environment, use this section. If not, skip it.

Subject/body formatting and SMTP failure handling are automated (section 10.4). Live inbox receipt stays manual.

### 5.1. Outbound email checks

Checklist:

- [ ] Configure a test destination email address.
- [ ] Trigger a reminder that should send via email.
- [ ] Confirm:
  - [ ] The email is received.
  - [ ] Subject and body are correct.
  - [ ] Any links or instructions in the email behave as expected.

### 5.2. Error handling

Checklist:

- [ ] Simulate or induce a misconfiguration (for example, invalid SMTP credentials) or a temporary failure.
- [ ] Confirm:
  - [ ] The app logs a clear error.
  - [ ] User-facing error messages (if any) are understandable.
  - [ ] The system does not crash or hang.

---

## 6. Discord Manual Tests

This section is a hub for Discord manual testing. The canonical, detailed task-reminder flow lives in [MANUAL_DISCORD_TEST_GUIDE.md](MANUAL_DISCORD_TEST_GUIDE.md).

### 6.1. When to run Discord tests

After Discord task, notebook, routing, or onboarding changes, run the mapped pytest files in [MANUAL_DISCORD_TEST_GUIDE.md](MANUAL_DISCORD_TEST_GUIDE.md) sections 4 and 6 (start with `pytest tests/behavior/test_discord_manual_checklist.py`). Live Discord is optional for tone and the real client.

### 6.2. High-level Discord checklist

These are automated. Run the named tests instead of walking Discord for connection, help, and error handling:

| Check | Automated test |
|---|---|
| Bot connects / reports ready | `test_discord_bot_is_actually_connected_checks_real_state`; ready/connect cases in `tests/behavior/test_discord_bot_behavior.py` |
| Help / status / basic commands | `test_general_help`; `test_commands_list`; slash/bang/natural cases in `tests/behavior/test_discord_automation_complete.py` |
| Invalid or incomplete input | `test_handle_missing_entities_gracefully`; notebook error cases in `tests/behavior/test_notebook_handler_behavior.py`; task reminder no-due-date errors |

Optional live check: the bot is actually online in your test server.

### 6.3. Detailed task-reminder flow

For the command cheat sheet and the automated map, use [MANUAL_DISCORD_TEST_GUIDE.md](MANUAL_DISCORD_TEST_GUIDE.md):

- Section 1. "Prerequisites" (operational: service running).
- Section 2. "Task Reminder Testing" (example commands).
- Section 4. "Automated checklist map".
- Section 6. "Task flows and notebook pagination".

Treat [MANUAL_DISCORD_TEST_GUIDE.md](MANUAL_DISCORD_TEST_GUIDE.md) as the authoritative source for Discord reminder and notebook checklist coverage.

---

## 7. AI Behavior Manual Tests

This section describes when to involve AI-specific testing and how it ties into automation.

### 7.1. When to run AI behavior tests

Run AI behavior tests when you change:

- How prompts are constructed.
- How conversation context is built, cached, or truncated.
- How AI decisions affect scheduling, reminders, or user messaging.
- How AI interacts with external tools or services.

### 7.2. Relationship to automated AI tests

Automated AI-oriented tests are described in:

   - [SYSTEM_AI_FUNCTIONALITY_TESTING_GUIDE.md](ai/SYSTEM_AI_FUNCTIONALITY_TESTING_GUIDE.md).

For a system-level description of the AI behavior covered by AI functionality tests, see [SYSTEM_AI_GUIDE.md](../ai/SYSTEM_AI_GUIDE.md).

This manual guide is part of the testing surface.

Use that guide to:

- Run the AI functionality test suite.
- Inspect structured results and logs.
- Understand which AI behaviors are already covered by automation.

### 7.3. Manual AI behavior checks

Safety, routing, and capability limits are automated in [test_ai_user_journeys.py](behavior/test_ai_user_journeys.py) (false CRUD sanitization, create-task persistence, ambiguous-task clarification, check-in honesty, disabled-task limits, numeric-only input). Run `pytest tests/behavior/test_ai_user_journeys.py` after AI prompt, routing, or sanitizer changes instead of walking those Discord flows by hand.

Manual review is **tone and phrasing only**:

- [ ] If you changed persona wording or care about how replies sound, run a few live LM Studio conversations and confirm the tone still fits.
- [ ] Capture any unexpected or unsafe suggestions as high-priority issues (those should also fail the journey tests).

---

## 8. Recording Results & Issue Creation

Manual testing outcomes must be recorded to be useful.

Checklist:

- [ ] For each run, capture:
  - [ ] Date, environment, and app version/commit.
  - [ ] Which sections of this guide were executed.
  - [ ] Any deviations or unexpected behavior.
- [ ] File issues for failures or confusing behavior with:
  - [ ] Exact steps to reproduce.
  - [ ] Screenshots or log excerpts where relevant.
  - [ ] Expected vs actual behavior.
- [ ] Link issues back to the sections and test cases in this guide or in subordinate guides (Discord, AI functionality).

Over time, you may extract structured templates (for example, GitHub issue templates) based on this section. This guide remains the canonical reference for what must be covered.

---

## 9. When Manual Testing Is Required

You do **not** need to run full manual tests for every small change. You **do** need manual testing when changes are:

- High impact (core scheduling, data handling, AI logic, or UI navigation).
- User-visible (new or significantly altered flows).
- Integration-heavy (Discord/email configuration, external services).
- Related to known fragile areas or past regressions.

Examples of triggers:

- Changes to how reminder windows are calculated or enforced.
- Changes to how tasks are created, parsed, or acknowledged in Discord.
- Changes to AI persona tone (run live LM Studio). Safety/routing/capability: run [test_ai_user_journeys.py](behavior/test_ai_user_journeys.py) first.
- Major UI reworks (any dialog that affects configuration, schedules, or messaging).

When in doubt:

1. Check section 1 of [TESTING_GUIDE.md](TESTING_GUIDE.md) to understand the testing philosophy.
2. Decide which parts of this manual guide apply to your change.
3. Run the mapped pytest in section 10 for the relevant subsets of sections 2-7, plus any detailed steps in subordinate guides:
   - [MANUAL_DISCORD_TEST_GUIDE.md](MANUAL_DISCORD_TEST_GUIDE.md).
   - [SYSTEM_AI_FUNCTIONALITY_TESTING_GUIDE.md](ai/SYSTEM_AI_FUNCTIONALITY_TESTING_GUIDE.md).

This manual guide is part of the testing surface. Any significant behavior change must remain compatible with the flows and expectations described here, or this guide must be updated alongside the code.

---

## 10. Automated checklist map

Behavior in sections 2-5 is automated unless marked **Live** or **N/A**. After startup, schedule, reminder, UI, email, or Google Health changes, run the named tests instead of walking the checklist by hand. Live checks remain for real inboxes, OAuth, visual layout, and AI tone.

Leftover gap tests live in:

- [test_manual_startup_shutdown.py](behavior/test_manual_startup_shutdown.py)
- [test_manual_schedule_reminder_checklist.py](behavior/test_manual_schedule_reminder_checklist.py)
- [test_manual_email_checklist.py](behavior/test_manual_email_checklist.py)
- [test_feature_restart_persistence.py](behavior/test_feature_restart_persistence.py)
- [test_run_mhm_launcher.py](unit/test_run_mhm_launcher.py)
- [test_run_headless_service_launcher.py](unit/test_run_headless_service_launcher.py)

### 10.1. Startup, shutdown, and configuration

| Checklist item | Automated test |
|---|---|
| Start via `run_mhm.py` | `test_main_launches_ui_with_venv_python_and_launch_env`; missing UI file: `test_main_returns_1_when_ui_app_missing` |
| Start via `run_headless_service.py` | `test_main_start_delegates_and_returns_0`; stop/status: `test_main_stop_delegates_and_returns_0`; `test_main_status_delegates_without_starting_a_process` |
| Headless/service start without uncaught exceptions | `test_start_logs_startup_sequence_without_errors`; manager-layer start/stop in `tests/behavior/test_service_behavior.py` and `tests/behavior/test_headless_service_behavior.py` |
| Clean startup logs | `test_start_logs_startup_sequence_without_errors` |
| UI exit | `test_ui_close_event_shuts_down_components_without_qt_window` |
| Tray-icon shutdown | **N/A** (no tray icon) |
| Service stop | `test_main_stop_delegates_and_returns_0`; `test_stop_service_real_behavior`; `test_shutdown_logs_clean_termination` |
| No orphan processes after stop | `test_get_service_processes_empty_after_mocked_stop` (mocked `psutil`). Live OS scan after a real start/stop stays manual. |
| Env / Discord credentials / config errors | `tests/unit/test_config.py`; `tests/unit/test_config_branch_coverage.py`; UI invalid-config in `tests/ui/test_ui_app_qt_core.py` |

### 10.2. UI cancel, save, and validation

| Checklist item | Automated test |
|---|---|
| Dialogs open without errors | Instantiation/open tests in `tests/ui/test_dialogs.py`, `tests/ui/test_dialog_behavior.py`, `tests/ui/test_ui_app_qt_main.py` |
| Layout / alignment / styling | **Live** (visual) |
| Tab order | **Live** |
| Escape / Enter | `test_return_and_enter_keys_ignore_event`; Escape cases in `tests/unit/test_dialog_helpers.py`; account/profile key handlers |
| Cancel does not commit | `test_cancel_does_not_persist_schedule`; `test_reject_does_not_persist_dirty_category_changes`; `test_category_save_persists_and_is_separate_from_reject`; `test_channel_save_is_not_reject` |
| Invalid time range rejected | `test_save_schedule_invalid_time_range_does_not_persist`; `tests/unit/test_validation.py` (`TestSchedulePeriodsValidation`) |
| Valid save accepted | `test_save_schedule_success_persists_clears_cache_triggers_and_calls_callback` plus existing account/channel/category save tests |

### 10.3. Scheduling and reminders

| Checklist item | Automated test |
|---|---|
| Create / store schedule periods | `test_schedule_period_lifecycle`; `test_set_schedule_periods_persists_complete_data`; `test_schedule_handler_add_schedule_period_success` |
| Overlapping ranges | `test_validate_schedule_periods_allows_overlapping_ranges` (current design: overlap is allowed) |
| Invalid times | `tests/unit/test_validation.py` (`test_validate_schedule_periods_invalid_time_order`, `_invalid_time_format`) |
| Persist after restart | `test_schedule_edits_persist_across_cache_clear_and_reload`; `test_schedule_survives_cache_clear_and_reload` |
| Delete period; messages/tasks do not crash | `test_delete_schedule_period_with_message_refs_does_not_crash` |
| Eligible only in valid windows | `test_scheduled_message_not_scheduled_for_wrong_day`; `test_is_schedule_active_time_before_range` / `_after_range`; `test_schedule_all_task_reminders_skips_inactive_period` |
| Trigger sending | `test_handle_sending_scheduled_message_success`; `test_handle_task_reminder_success` |
| Edit reminder text used on next send | `test_task_reminder_update_text_used_on_next_send` |
| Duplicate prevention | `test_task_reminder_already_sent_is_not_delivered_again`; `test_task_reminder_sent_flag_persists_and_blocks_duplicate` |
| Cancel / complete / delete cleanup | `tests/integration/test_orphaned_reminder_cleanup.py`; `test_task_completion_cleans_up_reminders` |
| Snooze / Remind Me Later reschedule | **N/A** until implemented |

### 10.4. Email

| Checklist item | Automated test |
|---|---|
| Reminder routes to email with subject/body | `test_task_reminder_email_smtp_payload_has_subject_and_body` |
| SMTP timeout (no hang) | `test_email_send_uses_smtp_timeout` |
| Invalid SMTP / auth failure, no crash | `test_email_send_smtp_auth_failure_logs_and_does_not_raise`; `test_email_bot_error_handling_preserves_system_stability` |
| Live inbox receipt | **Live** |

### 10.5. Google Health and restart persistence

| Checklist item | Automated test |
|---|---|
| Auth pause + one reconnect notice | `tests/unit/test_google_health_auth.py`; `tests/unit/test_google_health_notifications.py` |
| Non-auth API failure (no reconnect notice) | `test_sync_api_error_increments_failures_without_reconnect_notice` |
| Timeout / network failure | `test_sync_timeout_returns_false_without_crash`; `test_list_data_points_timeout_is_handled` |
| Success clears failures and reconnect flag | `test_sync_success_clears_reconnect_notice_and_failures` |
| Sync state survives reload | `test_google_health_sync_state_survives_reload` |
| Preferences / check-in / notebook survive reload | `test_preferences_channel_survives_new_loader`; `test_completed_checkin_survives_reload`; `test_notebook_entry_survives_reload` |
| Live OAuth, empty Fitbit payloads, 7-14 day confidence | **Live** ([GOOGLE_HEALTH_GUIDE.md](../integrations/google_health/GOOGLE_HEALTH_GUIDE.md)) |
