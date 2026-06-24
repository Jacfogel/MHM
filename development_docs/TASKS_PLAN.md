# Task System Improvements Plan

> **File**: `development_docs/TASKS_PLAN.md`  
> **Audience**: Human Developer & AI Collaborators  
> **Purpose**: Current roadmap for task-system usability, Discord task creation, follow-up flows, and advanced task features  
> **Style**: Actionable, checklist-focused, progress-tracked  
> **Last Updated**: 2026-05-27 (§3 task templates data model + commands shipped; Discord quick-add buttons deferred)  
> **Parent**: [PLANS.md](PLANS.md)  
> This plan is subordinate to `development_docs/PLANS.md` and must remain consistent with its standards and terminology.

**Use / fit**: Discord is the primary task interface. Tasks are not yet a daily habit, but they need to work well enough that creating, updating, and following up on tasks feels low-friction from a phone. Current priority is usability: natural-language creation, follow-up prompts, templates/quick actions, and useful task context. AI-based suggestions stay deferred until the AI/command-parsing overhaul.

---

## Current State

The task system is no longer just basic CRUD. As of the May 16 snapshot, the current implementation includes:

- `tasks/` package with `task_data_handlers.py`, `task_data_manager.py`, `task_schemas.py`, `task_service.py`, and `task_validation.py`.
- V2 task schema with `status`, `priority`, `due`, `reminders`, `recurrence`, and `completion` sections.
- Valid priorities: `low`, `medium`, `high`, `urgent`, `critical`.
- Task updates support fields including `title`, `description`, `category`, `group`, `status`, due fields, reminders, priority, tags, and recurrence fields.
- Task IDs and short IDs are supported for lookup/display.
- Recurring tasks are implemented and documented for Discord discoverability.
- Discord task creation can trigger follow-up flows for due date/time, priority, and reminders.
- Task list filtering supports due soon, overdue, high priority, priority, and tag filters.
- Task statistics/analytics entry points exist, but advanced analytics remain long-term.

**Not freshly verified here**: live Discord behaviour for task picker/detail UI. Automated unit coverage in [`test_task_list_ui.py`](../tests/communication/test_task_list_ui.py); live steps in [`MANUAL_DISCORD_TEST_GUIDE.md`](../tests/MANUAL_DISCORD_TEST_GUIDE.md) §6.1.D.

---

## Active Priorities

### 1. Live Discord validation for task creation follow-up flows

**Status**: Active validation  
**Priority**: High  
**Why it matters**: Follow-up flows are implemented in code, but the user experience needs manual validation in the actual Discord path.

**Validate**:
- [ ] Creating a task without a due date starts the due date/time follow-up.
- [ ] Due date follow-up supports skip, skip-all, cancel, and normal date/time input.
- [ ] Creating a task with a due date but no explicit priority starts the priority follow-up.
- [ ] Priority follow-up supports low, medium, high, critical, skip, and skip-all.
- [ ] Creating a task with enough due/priority data starts the reminder follow-up.
- [ ] Reminder follow-up suggestions are useful and not too noisy.
- [ ] Issuing a new task command while in a reminder follow-up clears or routes flow state correctly.
- [ ] Flow state does not get stuck after skip/cancel/completion.

**Acceptance**:
- Task creation can be completed quickly from Discord without needing the desktop UI.
- Optional follow-up questions are helpful but do not trap the user in a flow.

---

### 2. Broader natural-language task creation

**Status**: Planned  
**Priority**: High  
**Why it matters**: Discord task creation should accept ordinary phrasing, not just command-like syntax.

**Already done**:
- Recurring-task natural language basics for phrases such as daily/weekly/monthly/yearly, interval recurrence, weekdays, and time phrases.

**Remaining**:
- [x] Improve non-recurring due-date parsing, especially phrases like `this week`, `before Friday`, `after work` / `after school`, and `tonight` (2026-05-22: `command_parser._extract_task_entities`, `task_service.parse_relative_date`).
- [x] Improve title extraction so due dates, recurrence, priority, and tags are not accidentally included in task titles (2026-05-22: metadata stripped into `clean_title`).
- [x] Support natural priority phrases such as `important`, `urgent`, `low priority`, and `not urgent` (2026-05-22; `urgent` maps to priority `urgent`, not `high`).
- [x] Support tag/group extraction without making command parsing brittle (`#tag` via `parse_tags_from_text`, `group:name` / `in group:name`).
- [x] Add focused parser tests for common Discord-style messages (`test_command_parser_task_entities_expansion.py`).
- [ ] Live Discord validation that parsed due dates/titles feel right in follow-up flows (see §1).

---

### 2.1 Improve task command discovery

**Status**: Completed (2026-05-22)  
**Priority**: High

**Delivered**:
- [x] Expanded `TaskManagementHandler.get_help()` (`TASK_HELP_TEXT`) — create, list, complete/update, shortcuts, tags/groups, due phrases, follow-up note.
- [x] Expanded `get_examples()` with natural-language samples aligned with §2 parser.
- [x] `help tasks` / `examples tasks` route through the task handler (single source in `HelpHandler`).
- [x] Tests: `test_task_handler_behavior.py`, `test_command_discovery_help.py`.

**Acceptance**:
- A user can discover task use from `help tasks` without developer docs.

---

**§2 acceptance**:
- Messages like `I need to call the dentist this week` and `remind me to submit forms tomorrow morning` create useful structured tasks without manual cleanup.

---

### 3. Task templates and quick actions

**Status**: Partial (2026-05-27) — data model, built-ins, commands, and tests shipped; Discord quick-add buttons deferred  
**Priority**: Medium/High  
**Why it matters**: Templates reduce friction for repeated task types, especially health, household, appointments, and chores.

**Shipped (2026-05-27)**:
- [x] Template model in `tasks/task_templates.py` (`TaskTemplate`, aliases, five built-ins).
- [x] Built-in templates: medication, appointment, phone_call, cleaning, paperwork.
- [x] Prefill title, description, priority, due/time defaults, tags, group, recurrence (medication daily).
- [x] Service helpers: `build_task_data_from_template`, `create_task_from_template`, `list_task_templates`.
- [x] Commands: `task template <name>`, `create task from template <name>`, `list task templates`; help text updated.
- [x] Tests: `tests/unit/test_task_templates.py`, behavior tests in `test_task_handler_behavior.py`.

**Remaining**:
- [ ] Live Discord validation of create hub buttons and modals (2026-05-27: hub shipped in `create_item_ui.py`).
- [ ] Optional: user-defined custom templates (storage + settings UX).

**Acceptance**:
- Common tasks can be created with fewer words/clicks than a normal task.

---

### 4. Task notes, links, and lightweight attachments

**Status**: Planned  
**Priority**: Medium/High  
**Why it matters**: Many tasks need context: a link, a phone number, a screenshot reference, a form name, or short notes.

**Implement in stages**:
- [ ] Treat `description` as the first version of task notes; improve commands/help around it.
- [ ] Add `append note to task` / `add note to task` command support.
- [ ] Add URL/link capture as structured task metadata if `description` becomes insufficient.
- [ ] Defer file/image attachments until storage and Discord upload handling are designed.

**Acceptance**:
- A task can hold enough context that the user does not need to search chat history to remember what it means.

---

## Technical Backlog

### 5. Shared item organization with Notebook

**Status**: Planned  
**Priority**: Medium

Notebook and tasks both use concepts like tags, groups, short IDs, search/list views, and item mutation. Avoid creating separate incompatible systems.

**Tasks**:
- [ ] Confirm whether task `group` is fully supported in manager, parser, and display paths.
- [ ] Reuse or align with `core/tags.py` for tag normalization.
- [ ] Consider a shared ID helper if short-ID behavior diverges between tasks and notebook.
- [ ] Avoid moving task behaviour into notebook-specific modules.

---

### 5.1 User-customizable natural-language timeframes

**Status**: Planned  
**Priority**: Medium  
**Why it matters**: Parser and `parse_relative_date` currently use fixed defaults (for example `tonight` → 18:00, `after work` / `after school` → 17:00, weekend `this week` → end of the coming week). Different schedules and time zones need per-user settings.

**Implement later**:
- [ ] Add preference fields under task settings (for example in `preferences.json` / `task_settings`): `tonight_start_time`, `after_work_school_time` (shared default for “after work” and “after school”), `time_of_day_defaults` (morning/afternoon/evening/night), and optionally `weekend_this_week_means_coming_week` (boolean, default true).
- [ ] Load preferences in `task_service.parse_relative_date` and `command_parser._extract_task_entities` (or a shared `task_natural_language_defaults(user_id)` helper) instead of hard-coded constants.
- [ ] Expose settings via Discord command and/or desktop task settings when UX is defined (defer UI until data model is stable).
- [ ] Document new fields in [USER_DATA_MODEL.md](../core/USER_DATA_MODEL.md) and [CONFIGURATION_REFERENCE.md](../CONFIGURATION_REFERENCE.md).
- [ ] Add unit tests with mocked per-user preference payloads.

**Acceptance**:
- A user can change what “tonight” and “after work/school” mean without code changes.
- Defaults remain sensible when preferences are unset.

**Note (2026-05-22)**: Current shipped defaults — `tonight` 18:00, `after work` / `after school` 17:00, Sat/Sun `this week` → Sunday at end of the coming week.

---

### 6. Task dependencies / blocked-by relationships

**Status**: Planned  
**Priority**: Medium

**Implement later**:
- [ ] Add `blocked_by` and `blocks` relationships.
- [ ] Show blocked status in task lists.
- [ ] Automatically unblock when prerequisite tasks are completed.
- [ ] Add tests for circular dependency prevention.

---

### 7. Batch task operations

**Status**: Planned  
**Priority**: Low/Medium

**Implement later if task usage grows**:
- [ ] Batch complete/delete/archive.
- [ ] Bulk priority changes.
- [ ] Bulk tag/group assignment.
- [ ] Clear confirmation UX for destructive operations.

---

## Deferred / Long-Term

### Context-aware and mood-aware reminders

**Status**: Deferred  
**Reason**: Overlaps with the broader mood-aware support plan and should wait until foundational task usage is stronger.

Future ideas:
- location-aware reminders
- calendar-linked reminders
- low-energy mode
- difficulty/energy matching
- gentler reminders when overwhelmed

### Smart task suggestions and AI optimization

**Status**: Deferred  
**Reason**: Wait for AI/command-parsing overhaul.

Future ideas:
- suggested tasks based on patterns
- breaking down complex tasks into subtasks
- task ordering suggestions
- conflict detection

### Advanced views and analytics

**Status**: Deferred  
**Reason**: Useful later, not needed before Discord task creation is reliable.

Future ideas:
- calendar view
- kanban view
- focus mode
- completion trends
- recurring-task streaks
- overdue priority escalation

### Sync, export, and backup enhancements

**Status**: Deferred  
**Reason**: Basic task persistence exists; broader sync/backup should align with the storage/user-data roadmap.

Future ideas:
- export/import task data
- cloud sync
- cross-device access
- backup confidence checks specific to task data

---

## Completed / Removed from Active Planning

These are no longer active roadmap items. Keep details in changelog/test history instead of expanding them here.

- Recurring task model and runtime support.
- Recurring-task Discord discoverability and help examples.
- Recurring natural-language basics.
- Core task CRUD.
- Task reminder system foundations.
- Task V2 schema foundation.
- Task service facade foundation.
- Task due date, priority, and reminder follow-up flow implementation in code.

---

## Suggested Validation Commands

Use focused tests before and after task-system changes:

```powershell
pytest tests/behavior/test_task_handler_behavior.py tests/behavior/test_command_discovery_help.py tests/unit/test_command_parser_rule_based_patterns_expansion.py -q
pytest tests/unit/test_recurring_tasks.py tests/unit/test_task_service.py tests/unit/test_task_short_ids.py -q
pytest tests/behavior/test_task_reminder_followup_behavior.py tests/integration/test_task_reminder_integration.py -q
```

Before a larger merge, run the normal full project validation/audit path.
