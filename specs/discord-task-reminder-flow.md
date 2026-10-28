# Discord task reminder flow

> **File**: `specs/discord-task-reminder-flow.md`  
> **Audience**: Developers, AI collaborators, and reviewers  
> **Purpose**: Behavior requirements for Discord task reminder delivery and task reminder action buttons  
> **Style**: Behavior requirements and scenarios (see [SPECS_GUIDE.md](SPECS_GUIDE.md))  
> **Last Updated**: 2026-10-27
> **Implementation**: `communication/communication_channels/discord/ui/task_reminder_view.py`, `tasks/task_focus.py`, `tasks/task_reminder_deferrals.py`, `tasks/task_reminder_snooze.py`, `tasks/task_occurrence_skip.py`, `tasks/task_simplify.py`, `core/message_pressure.py`, `communication/command_handlers/task_handler.py`, `communication/communication_channels/discord/bot.py`, `communication/reminders/reminder_dispatcher.py`, `scheduler/task_reminders.py`, `tasks/task_service.py`, `communication/message_processing/interaction_manager.py`
> **Related**: [COMMUNICATION_GUIDE.md](../communication/COMMUNICATION_GUIDE.md), [DISCORD_GUIDE.md](../communication/communication_channels/discord/DISCORD_GUIDE.md), [discord-message-and-command-routing.md](discord-message-and-command-routing.md)  
> **Automated tests**: `tests/unit/test_task_focus.py`, `tests/unit/test_task_reminder_deferrals.py`, `tests/unit/test_task_reminder_snooze.py`, `tests/unit/test_task_occurrence_skip.py`, `tests/unit/test_task_simplify.py`, `tests/unit/test_task_reminder_view.py`, `tests/unit/test_message_pressure.py`, `tests/behavior/test_task_handler_behavior.py`, `tests/behavior/test_discord_task_reminder_followup.py`, `tests/behavior/test_task_reminder_followup_behavior.py`, `tests/integration/test_task_reminder_integration.py`, `tests/behavior/test_discord_bot_behavior.py`, `tests/unit/test_task_service.py`
> **Coverage matrix**: [SPEC_COVERAGE_MATRIX.md](SPEC_COVERAGE_MATRIX.md#discord-task-reminder-flow)

## 1. Purpose

Discord task reminders notify linked Discord users about active tasks and provide quick actions to complete the task, snooze the reminder, skip this occurrence, break the task into smaller steps, or get help. Discord-specific code SHALL adapt the reminder into Discord UI but SHALL route actual task completion, reminder snooze, skip, and breakdown through channel-agnostic task handling. Reminder snooze SHALL NOT change the task due date. Skip on a one-off task SHALL NOT change the due date. Breaking a task down SHALL NOT change the original title or the due date.

## 2. Requirements

### 2.1. Requirement: Task reminders are sent only for eligible active tasks

Task reminder delivery SHALL respect task state and reminder scheduling rules before a Discord reminder is sent.

#### Scenario: Active task with due reminder

- **GIVEN** a task is active  
- **AND** the task has a due reminder configured for Discord delivery  
- **WHEN** the reminder dispatcher runs  
- **THEN** Discord receives a task reminder message  
- **AND** the reminder may include task reminder action buttons  

#### Scenario: Completed task is skipped

- **GIVEN** a task is already completed  
- **WHEN** reminder delivery evaluates the task  
- **THEN** no Discord reminder is sent for that completed task  

#### Scenario: Deleted task reminder cleanup

- **GIVEN** a task is deleted  
- **WHEN** task reminder cleanup runs  
- **THEN** reminders tied to the deleted task are removed or ignored  
- **AND** no future Discord reminder is sent for that deleted task  

#### Scenario: Updated reminder schedule

- **GIVEN** a task's reminder settings are changed  
- **WHEN** task reminder scheduling is refreshed  
- **THEN** old reminder jobs are replaced or ignored  
- **AND** future Discord reminders follow the updated task reminder settings  

#### Scenario: Scheduler marks reminder attempted after dispatch handoff

- **GIVEN** `scheduler/task_reminders.py` hands a task reminder to the delivery interface  
- **WHEN** the delivery call returns without raising an exception  
- **THEN** the scheduler sets `reminder_sent` and `reminder_sent_on` to the user's local date  
- **AND** another reminder for that same task is skipped for the rest of that local date  
- **AND** a later local date can send a reminder for that task again  
- **AND** the lower-level `TaskReminderDispatcher` still returns a `MessageSendResult` that records whether Discord delivery actually succeeded, failed, or was skipped  
- **AND** `reminder_sent_on` is written only when delivery returns `sent` or `unconfirmed`  

### 2.2. Requirement: Task reminder view provides persistent action buttons

`get_task_reminder_view(user_id, task_id, task_title)` SHALL create a persistent Discord `View` with Done, Snooze, Break down with AI, Leave me alone, and More buttons. These labels SHALL preserve the existing complete, reminder-snooze, breakdown, skip-occurrence, and help behavior.

#### Scenario: Task reminder view creation

- **GIVEN** Discord needs task reminder buttons  
- **WHEN** `get_task_reminder_view(user_id, task_id, task_title)` is called  
- **THEN** it returns a Discord `View`  
- **AND** the view uses `timeout=None`  
- **AND** each button custom ID includes the internal user ID and task ID  
- **AND** `Break down with AI` is a primary action on the first button row

#### Scenario: Shared focus policy selects the reminder task

- **GIVEN** a user has more than one active task
- **WHEN** a scheduled task-reminder period selects one task
- **THEN** selection uses the shared task-focus policy also used by chat suggestions
- **AND** current reminder snoozes are respected
- **AND** an open subtask is preferred over reminding on its parent as a whole
- **AND** a genuinely urgent task is not hidden by an easier, less urgent task

#### Scenario: Low energy changes effort preference but not urgency

- **GIVEN** today's check-in has a reliable energy score of 1 or 2
- **WHEN** several tasks have the same urgency band
- **THEN** a short task or unfinished subtask receives an effort preference
- **AND** overdue, critical, urgent, high-priority, or due-today work remains visible ahead of less urgent work

#### Scenario: Reminder wording follows reliable guidance

- **GIVEN** today's energy is low or reliable health guidance calls for a gentle tone
- **WHEN** a task reminder is formatted
- **THEN** its wording keeps expectations small and avoids productivity pressure
- **AND** it explains why the task was selected without exposing raw health measurements
- **AND** it points prominently to `Break down with AI`
- **WHEN** no reliable energy or health signal exists
- **THEN** the established direct reminder tone is preserved

#### Scenario: Repeated deferrals change reminder guidance

- **GIVEN** a task reminder has been snoozed or skipped repeatedly
- **WHEN** another reminder is formatted
- **THEN** only the five newest deferrals are retained
- **AND** an existing open subtask is named as the smaller next step when available
- **AND** otherwise `Break down with AI` is offered
- **AND** after at least three deferrals on a dated task, reconsidering the due date is offered

#### Scenario: Pressure guidance is coordinated across scheduled messages

- **GIVEN** reliable guidance includes `avoid_nagging_movement_prompts` or another gentle-pressure signal
- **WHEN** MHM prepares task, motivational, or Google Health messaging
- **THEN** the categories share one pressure policy
- **AND** motivational messages do not continue at normal pressure while health messages soften

#### Scenario: Done button

- **GIVEN** a task reminder includes a `Done` button
- **WHEN** the user clicks it  
- **THEN** the button handler defers the Discord interaction  
- **AND** looks up the internal user ID from the clicker's Discord ID  
- **AND** routes `complete task <task_id>` through `handle_user_message(..., "discord")`  
- **AND** sends the handler response ephemerally  

#### Scenario: Done button from unlinked user

- **GIVEN** a task reminder button interaction is received  
- **AND** the clicker's Discord ID cannot be mapped to an internal MHM user  
- **WHEN** the `Done` button handler runs
- **THEN** it sends an ephemeral account-not-found error  
- **AND** does not mark the task complete  

#### Scenario: Snooze button

- **GIVEN** a task reminder includes a `Snooze` button
- **WHEN** the user clicks it  
- **THEN** the button handler defers the Discord interaction  
- **AND** looks up the internal user ID from the clicker's Discord ID  
- **AND** routes `snooze task <task_id>` through `handle_user_message(..., "discord")`  
- **AND** if the task is active, Discord shows snooze choices: 1 hour, tonight or tomorrow morning, next week, and custom  
- **AND** the task due date is not changed by opening those choices  

#### Scenario: Snooze 1 hour

- **GIVEN** a linked user chooses `1 hour` after Snooze
- **WHEN** the snooze handler runs  
- **THEN** the task due date is unchanged  
- **AND** `reminder_snooze_until` is set about one hour from now  
- **AND** `reminder_sent` stays true and `reminder_sent_on` stays on today's local date so another period reminder does not fire the same day  
- **AND** the snooze reminder itself still sends at the snooze time, including when that time is later the same day  
- **AND** a one-time reminder is scheduled for that snooze time  

#### Scenario: Snooze tonight or tomorrow morning

- **GIVEN** a linked user chooses tonight / tomorrow morning  
- **WHEN** it is before the user's evening start  
- **THEN** the reminder is snoozed until the user's tonight time  
- **WHEN** it is already evening or night  
- **THEN** the reminder is snoozed until tomorrow morning  

#### Scenario: Snooze next week

- **GIVEN** a linked user chooses `Next week`  
- **WHEN** the snooze handler runs  
- **THEN** the reminder is snoozed until 7 days later at the user's morning time  
- **AND** the task due date is unchanged  

#### Scenario: Custom snooze time

- **GIVEN** a linked user chooses `Custom` and types a when-phrase such as `Friday 3pm`  
- **WHEN** the phrase can be parsed  
- **THEN** the reminder is snoozed until that time  
- **AND** the task due date is unchanged  

#### Scenario: Snooze from unlinked user

- **GIVEN** a task reminder button interaction is received  
- **AND** the clicker's Discord ID cannot be mapped to an internal MHM user  
- **WHEN** the `Snooze` button handler runs
- **THEN** it sends an ephemeral account-not-found error  
- **AND** does not change task reminder state  

#### Scenario: More button

- **GIVEN** a task reminder includes a `More` button  
- **WHEN** the user clicks it  
- **THEN** Discord sends ephemeral task help  
- **AND** the help includes a shortened task ID  
- **AND** the help shows both ID-based and title-based completion examples  
- **AND** the help includes skip and simplify command examples  

#### Scenario: Skip this occurrence (recurring)

- **GIVEN** a Discord reminder is for a repeating task  
- **WHEN** the linked user clicks `Leave me alone` or types `skip task <id>`
- **THEN** the current occurrence is not marked completed  
- **AND** the same task stays active  
- **AND** the due date moves to the next occurrence  
- **AND** MHM does not ping again until that next occurrence  

#### Scenario: Skip this occurrence (one-off)

- **GIVEN** a Discord reminder is for a one-off task  
- **WHEN** the linked user clicks `Leave me alone` or types `skip that`
- **THEN** the task stays on the list  
- **AND** the due date is unchanged  
- **AND** MHM does not ping again until tomorrow morning  

#### Scenario: Break the task into smaller steps

- **GIVEN** a Discord reminder includes a `Break down with AI` button
- **WHEN** the linked user clicks it, or types `simplify that`  
- **THEN** MHM suggests a few smaller steps  
- **AND** the original task title stays  
- **AND** the due date is unchanged  
- **WHEN** the user adds those steps, or types `simplify that to ...`  
- **THEN** the chosen steps are saved as subtasks under the original task  

#### Scenario: Reminder names the open step

- **GIVEN** the reminded task has an open step  
- **WHEN** the reminder is sent  
- **THEN** the message names that step and says which task it is part of  
- **AND** Done finishes that step
- **AND** the original task stays open  
- **AND** Later and Skip still apply to the original task's reminder  

## 3. 2.3. Requirement: Task completion follow-up uses normal task command behavior

Completing a task from Discord SHALL go through the same command flow as typed task completion.

#### Scenario: Complete by task ID from reminder

- **GIVEN** a linked user clicks `Done` on a Discord reminder
- **WHEN** the adapter routes `complete task <task_id>`  
- **THEN** the task handler marks the matching task complete if valid  
- **AND** the user receives the same kind of completion response they would receive after typing the command  
- **AND** reminder cleanup follows the task completion behavior  

#### Scenario: Complete by typed title after reminder

- **GIVEN** a user receives a task reminder  
- **WHEN** they type `complete task "<task title>"` instead of clicking the button  
- **THEN** Discord routes the typed message through `handle_user_message`  
- **AND** the task handler completes or disambiguates using normal task command behavior  

### 3.1. Requirement: Recurring task reminders continue from the next generated task instance

Recurring task completion SHALL create or expose the next task instance according to task recurrence rules, and reminders SHALL follow the next active instance.

#### Scenario: Recurring task is completed from Discord reminder

- **GIVEN** a Discord reminder is sent for a recurring task instance  
- **WHEN** the user completes the task from Discord  
- **THEN** the current instance is completed  
- **AND** the next recurring instance is created or scheduled according to recurrence rules  
- **AND** future reminders apply to the next active instance rather than the completed one  

### 3.2. Requirement: Explicit AI task breakdown is reviewed before saving

- **GIVEN** a linked user selects a task in the Discord task picker
- **WHEN** they press **Break down with AI**
- **THEN** MHM requests smaller steps through the task handler without AI command interpretation or response enhancement
- **AND** suggestions alone do not save subtasks or change the original task
- **AND** the user can add all, choose steps to add, add their own step, or cancel
- **AND** cancelling saves nothing and ends the matching pending text confirmation
- **AND** successful saving ends the review; another account cannot use it

#### Scenario: AI is disabled or unavailable

- **GIVEN** global AI is off, task-breakdown AI is disabled, or the model is unavailable
- **WHEN** the user requests a breakdown
- **THEN** MHM explains why suggestions are unavailable and offers **Add my own step**
- **AND** writing and saving that step requires no model request
- **AND** disabled AI is checked before model initialization or availability probing

## 4. Out of scope

- Asking why a reminder was skipped, or auto-creating a notebook blocker note (see [NOTES_PLAN.md](../development_docs/NOTES_PLAN.md) Section 5.5).
- Changing the task due date as a way to postpone work (that remains a normal due-date update).
- Exact text of task reminder messages generated outside the Discord view.
- Task CRUD validation rules beyond reminder-specific behavior.
- UI configuration screens for task reminder settings.
- Email task reminders.

## 5. Manual test checklist

Run after changing Discord task reminder behavior:

1. [ ] Create a task with a Discord reminder -> reminder is scheduled.
2. [ ] Reminder fires for active task -> Discord message appears with task action buttons.
3. [ ] Completed task reaches reminder time -> no Discord reminder is sent.
4. [ ] Deleted task reaches reminder time -> no Discord reminder is sent.
5. [ ] Update task reminder time -> future reminder follows new time.
6. [ ] Delivery returns sent or unconfirmed -> scheduler marks `reminder_sent` and today's `reminder_sent_on`; a later day can remind again; a pending snooze still sends.
7. [ ] Click `Done` -> task is completed through normal task handler behavior.
8. [ ] Click `Snooze` -> snooze choices appear (1 hour, tonight or tomorrow morning, next week, custom); due date unchanged.
8a. [ ] Choose `1 hour` -> a later reminder is scheduled; due date unchanged.
8b. [ ] Choose tonight before evening -> reminder is scheduled for tonight; after evening the choice is tomorrow morning.
8c. [ ] Choose `Next week` -> reminder is scheduled about 7 days later in the morning.
8d. [ ] Choose `Custom` with `Friday 3pm` -> reminder is scheduled for that time.
9. [ ] Click `More` -> short ID, title examples, skip, and simplify commands appear ephemerally.
10. [ ] Unlinked user clicks a task button -> account-not-found message appears; task remains unchanged.
11. [ ] Complete recurring task from reminder -> next instance/reminder behavior is correct.
12. [ ] Click `Leave me alone` on a repeating task -> task stays active, due date moves to the next occurrence, no shame-y completed copy.
13. [ ] Click `Leave me alone` on a one-off task -> due date unchanged; no ping until tomorrow morning.
14. [ ] Click `Break down with AI` -> suggested steps appear; adding them keeps the original title and due date.
14a. [ ] Select a task from the task picker, then `Break down with AI` -> review appears; Cancel saves nothing; adding selected steps saves only those steps.
14b. [ ] Turn AI off in desktop Admin > AI Controls, then request a breakdown -> explanatory fallback and `Add my own step` appear; saving a typed step works.
15. [ ] Snooze or skip the same task repeatedly -> reminder names an open step, offers Break down with AI, or suggests reconsidering the due date instead of repeating unchanged copy.

## 6. Related documentation

- [SPECS_GUIDE.md](SPECS_GUIDE.md) - how behavior specs fit the project  
- [COMMUNICATION_GUIDE.md](../communication/COMMUNICATION_GUIDE.md) - channel-agnostic architecture  
- [DISCORD_GUIDE.md](../communication/communication_channels/discord/DISCORD_GUIDE.md) - Discord adapter overview  
- [TESTING_GUIDE.md](../tests/TESTING_GUIDE.md) - running automated tests  
