# Manual Testing Guide

> **File**: `tests/MANUAL_TESTING_GUIDE.md`  
> **Audience**: Developers and AI assistants performing manual testing  
> **Purpose**: Canonical manual testing flows and checklists across channels and features  
> **Style**: Checklist-first, concise but detailed  
> **Parent**: [TESTING_GUIDE.md](tests/TESTING_GUIDE.md)  
> This document is subordinate to [TESTING_GUIDE.md](tests/TESTING_GUIDE.md) and should be kept consistent with its standards and terminology.

---

## 1. Purpose and Scope

Automated tests are the primary safety net for MHM, but they cannot cover every scenario—especially those involving UI, real integrations, and nuanced user experience.

This guide defines:

- When manual testing is required.
- Which manual flows must be exercised.
- How to run manual checks across UI, scheduling, reminders, email, Discord, and AI behavior.
- How to record and report the results.

Use this guide:

- Before tagging a release.
- After significant changes to scheduling, messaging, AI behavior, or UI.
- When fixing bugs that are primarily UX or integration issues.

For the overall testing framework (layout, markers, automation, coverage), use:

- [TESTING_GUIDE.md](tests/TESTING_GUIDE.md) (automation-focused).
- [AI_TESTING_GUIDE.md](ai_development_docs/AI_TESTING_GUIDE.md) (AI routing and constraints).

---

## 2. Core Manual Flows

These flows should be validated in every full manual test pass, regardless of which channel or feature you are changing.

### 2.1. Application startup and shutdown

Checklist:

- [ ] Start the app using the documented entry point (for example, `python run_mhm.py` or equivalent).
- [ ] Confirm that:
  - [ ] The main window or headless service starts without uncaught exceptions.
  - [ ] Logs show a clean startup sequence (no critical or unexpected errors).
- [ ] Shut down the application using the normal mechanisms (UI exit button, tray icon, or service stop command).
- [ ] Confirm that:
  - [ ] No orphan processes remain.
  - [ ] Shutdown logs show a clean termination.

Notes:

- If any unexpected warnings or errors appear in logs, capture them and decide whether they are acceptable or must be fixed.
- If shutdown hangs or requires forced termination, file an issue.

### 2.2. Basic configuration and environment

Checklist:

- [ ] Environment variables and `.env` configuration are loaded correctly (no missing mandatory settings).
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

- [ ] Create at least one schedule period (for example, “Morning”, “Afternoon”).
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
- [ ] If snooze is supported:
  - [ ] Trigger a reminder and snooze it.
  - [ ] Confirm it is re-scheduled correctly.
- [ ] Cancel/remove a reminder:
  - [ ] Confirm it no longer sends.
  - [ ] Confirm dependent UI and internal state are updated.

Any discrepancy (duplicates, missed reminders, reminders firing at the wrong time) must be treated as a priority defect.

---

## 5. Email Manual Tests

If email delivery is enabled in your environment, use this section. If not, skip it.

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

This section is a hub for Discord manual testing. The canonical, detailed task-reminder flow lives in [MANUAL_DISCORD_TEST_GUIDE.md](tests/MANUAL_DISCORD_TEST_GUIDE.md).

### 6.1. When to run Discord manual tests

Run Discord manual tests when you change:

- Task creation and parsing, especially natural language input.
- Reminder scheduling logic that interacts with Discord.
- Discord command routing, permissions, or channel selection.
- Any logic that affects how follow-up questions and confirmation messages are phrased.

### 6.2. High-level Discord checklist

High-level checks (before deep-dives):

- [ ] Bot connects successfully to the correct Discord server and channels.
- [ ] Basic commands (for example, help/status commands) respond as expected.
- [ ] Error conditions (invalid commands, incomplete inputs) produce clear messages.

### 6.3. Detailed task-reminder flow

For the full, step-by-step scenario coverage, use [MANUAL_DISCORD_TEST_GUIDE.md](tests/MANUAL_DISCORD_TEST_GUIDE.md):

- Section 1. "Prerequisites".
- Section 2. "Task Reminder Follow-up Flow Testing".
- Section 3. "Verification Commands".
- Section 4. "Success Criteria".
- Section 5. "Known Issues to Watch For".
- Section 7. "Quick Test Checklist".

Treat [MANUAL_DISCORD_TEST_GUIDE.md](tests/MANUAL_DISCORD_TEST_GUIDE.md) as the authoritative source for detailed Discord reminder flows.

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

   - [SYSTEM_AI_FUNCTIONALITY_TEST_GUIDE.md](tests/SYSTEM_AI_FUNCTIONALITY_TEST_GUIDE.md).

For a system-level description of the AI behavior covered by AI functionality tests, see [SYSTEM_AI_GUIDE.md](ai/SYSTEM_AI_GUIDE.md).

This manual guide is part of the testing surface.

Use that guide to:

- Run the AI functionality test suite.
- Inspect structured results and logs.
- Understand which AI behaviors are already covered by automation.

### 7.3. Manual AI behavior checks

In addition to automated tests:

- [ ] Perform a few realistic conversations that match current user journeys (for example, setting up reminders, responding to check-ins).
- [ ] Confirm:
  - [ ] The AI uses correct tone and phrasing.
  - [ ] The AI does not suggest unsafe or invalid actions.
  - [ ] The AI stays within documented capabilities and constraints.

Capture any unexpected or unsafe suggestions as high-priority issues.

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
- Changes to AI prompts or conversation-handling logic.
- Major UI reworks (any dialog that affects configuration, schedules, or messaging).

When in doubt:

1. Check section 1 of [TESTING_GUIDE.md](tests/TESTING_GUIDE.md) to understand the testing philosophy.
2. Decide which parts of this manual guide apply to your change.
3. Run at least the relevant subsets of sections 2–7 here, plus any detailed steps in subordinate guides:
   - [MANUAL_DISCORD_TEST_GUIDE.md](tests/MANUAL_DISCORD_TEST_GUIDE.md).
   - [SYSTEM_AI_FUNCTIONALITY_TEST_GUIDE.md](tests/SYSTEM_AI_FUNCTIONALITY_TEST_GUIDE.md).

This manual guide is part of the testing surface. Any significant behavior change must remain compatible with the flows and expectations described here, or this guide must be updated alongside the code.
