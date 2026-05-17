# Task System Improvements Plan

> **File**: `development_docs/TASKS_PLAN.md`  
> **Audience**: Human Developer & AI Collaborators  
> **Purpose**: Current roadmap for task-system usability, Discord task creation, follow-up flows, and advanced task features  
> **Style**: Actionable, checklist-focused, progress-tracked  
> **Last Updated**: 2026-05-17 (condensed completed history; aligned with May 16 code snapshot)  
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

**Not freshly verified here**: full audit status, live Discord behaviour, and current coverage numbers. Re-run focused task tests and a full audit before treating this as runtime validation.

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
- [ ] Improve non-recurring due-date parsing, especially phrases like `this week`, `before Friday`, `after work`, and `tonight`.
- [ ] Improve title extraction so due dates, recurrence, priority, and tags are not accidentally included in task titles.
- [ ] Support natural priority phrases such as `important`, `urgent`, `low priority`, and `not urgent`.
- [ ] Support tag/group extraction without making command parsing brittle.
- [ ] Add focused parser tests for common Discord-style messages.

**Acceptance**:
- Messages like `I need to call the dentist this week` and `remind me to submit forms tomorrow morning` create useful structured tasks without manual cleanup.

---

### 3. Task templates and quick actions

**Status**: Planned  
**Priority**: Medium/High  
**Why it matters**: Templates reduce friction for repeated task types, especially health, household, appointments, and chores.

**Implement**:
- [ ] Define a small template model before adding UI/button complexity.
- [ ] Add built-in templates for common categories:
  - medication
  - appointment
  - phone call
  - cleaning/chores
  - paperwork/forms
- [ ] Allow templates to prefill title, description, priority, due/reminder defaults, tags, and group.
- [ ] Add Discord quick-add options only after the template data model is stable.
- [ ] Add tests for creating a task from a template.

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
