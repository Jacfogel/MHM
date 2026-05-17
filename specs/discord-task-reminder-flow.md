# Discord task reminder flow

> **File**: `specs/discord-task-reminder-flow.md`  
> **Audience**: Developers, AI collaborators, and reviewers  
> **Purpose**: Behavior requirements for Discord task reminder delivery and task reminder action buttons  
> **Style**: Behavior requirements and scenarios (see [SPECS_GUIDE.md](SPECS_GUIDE.md))  
> **Last Updated**: 2026-05-16  
> **Implementation**: `communication/communication_channels/discord/task_reminder_view.py`, `communication/communication_channels/discord/bot.py`, `communication/reminders/reminder_dispatcher.py`, `scheduler/task_reminders.py`, `tasks/task_service.py`, `communication/message_processing/interaction_manager.py`, `communication/command_handlers/task_handler.py`  
> **Related**: [COMMUNICATION_GUIDE.md](../communication/COMMUNICATION_GUIDE.md), [DISCORD_GUIDE.md](../communication/communication_channels/discord/DISCORD_GUIDE.md), [discord-message-and-command-routing.md](discord-message-and-command-routing.md)  
> **Automated tests**: `tests/behavior/test_discord_task_reminder_followup.py`, `tests/behavior/test_task_reminder_followup_behavior.py`, `tests/integration/test_task_reminder_integration.py`, `tests/behavior/test_discord_bot_behavior.py`, `tests/unit/test_task_service.py`  
> **Coverage matrix**: [SPEC_COVERAGE_MATRIX.md](SPEC_COVERAGE_MATRIX.md#discord-task-reminder-flow)

## Purpose

Discord task reminders notify linked Discord users about active tasks and provide quick actions to complete the task, defer action, or get help. Discord-specific code SHALL adapt the reminder into Discord UI but SHALL route actual task completion through channel-agnostic task handling.

## Requirements

### Requirement: Task reminders are sent only for eligible active tasks

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
- **THEN** the scheduler updates the task's `reminder_sent` flag  
- **AND** the lower-level `TaskReminderDispatcher` still returns a `MessageSendResult` that records whether Discord delivery actually succeeded, failed, or was skipped  
- **NOTE** this reflects current behavior; the scheduler does not currently gate `reminder_sent` on the returned delivery result  

### Requirement: Task reminder view provides persistent action buttons

`get_task_reminder_view(user_id, task_id, task_title)` SHALL create a persistent Discord `View` with Complete Task, Remind Me Later, and More buttons.

#### Scenario: Task reminder view creation

- **GIVEN** Discord needs task reminder buttons  
- **WHEN** `get_task_reminder_view(user_id, task_id, task_title)` is called  
- **THEN** it returns a Discord `View`  
- **AND** the view uses `timeout=None`  
- **AND** each button custom ID includes the internal user ID and task ID  

#### Scenario: Complete Task button

- **GIVEN** a task reminder includes a `Complete Task` button  
- **WHEN** the user clicks it  
- **THEN** the button handler defers the Discord interaction  
- **AND** looks up the internal user ID from the clicker's Discord ID  
- **AND** routes `complete task <task_id>` through `handle_user_message(..., "discord")`  
- **AND** sends the handler response ephemerally  

#### Scenario: Complete Task button from unlinked user

- **GIVEN** a task reminder button interaction is received  
- **AND** the clicker's Discord ID cannot be mapped to an internal MHM user  
- **WHEN** the `Complete Task` button handler runs  
- **THEN** it sends an ephemeral account-not-found error  
- **AND** does not mark the task complete  

#### Scenario: Remind Me Later button

- **GIVEN** a task reminder includes a `Remind Me Later` button  
- **WHEN** the user clicks it  
- **THEN** Discord acknowledges the click ephemerally  
- **AND** tells the user they can use `/tasks` to see all tasks  
- **AND** no task state is changed by the current implementation  

#### Scenario: More button

- **GIVEN** a task reminder includes a `More` button  
- **WHEN** the user clicks it  
- **THEN** Discord sends ephemeral task help  
- **AND** the help includes a shortened task ID  
- **AND** the help shows both ID-based and title-based completion examples  

### Requirement: Task completion follow-up uses normal task command behavior

Completing a task from Discord SHALL go through the same command flow as typed task completion.

#### Scenario: Complete by task ID from reminder

- **GIVEN** a linked user clicks `Complete Task` on a Discord reminder  
- **WHEN** the adapter routes `complete task <task_id>`  
- **THEN** the task handler marks the matching task complete if valid  
- **AND** the user receives the same kind of completion response they would receive after typing the command  
- **AND** reminder cleanup follows the task completion behavior  

#### Scenario: Complete by typed title after reminder

- **GIVEN** a user receives a task reminder  
- **WHEN** they type `complete task "<task title>"` instead of clicking the button  
- **THEN** Discord routes the typed message through `handle_user_message`  
- **AND** the task handler completes or disambiguates using normal task command behavior  

### Requirement: Recurring task reminders continue from the next generated task instance

Recurring task completion SHALL create or expose the next task instance according to task recurrence rules, and reminders SHALL follow the next active instance.

#### Scenario: Recurring task is completed from Discord reminder

- **GIVEN** a Discord reminder is sent for a recurring task instance  
- **WHEN** the user completes the task from Discord  
- **THEN** the current instance is completed  
- **AND** the next recurring instance is created or scheduled according to recurrence rules  
- **AND** future reminders apply to the next active instance rather than the completed one  

## Out of scope

- Implementing snooze/reschedule logic for `Remind Me Later`; the current button only acknowledges.
- Exact text of task reminder messages generated outside the Discord view.
- Task CRUD validation rules beyond reminder-specific behavior.
- UI configuration screens for task reminder settings.
- Email task reminders.

## Manual test checklist

Run after changing Discord task reminder behavior:

1. [ ] Create a task with a Discord reminder -> reminder is scheduled.
2. [ ] Reminder fires for active task -> Discord message appears with task action buttons.
3. [ ] Completed task reaches reminder time -> no Discord reminder is sent.
4. [ ] Deleted task reaches reminder time -> no Discord reminder is sent.
5. [ ] Update task reminder time -> future reminder follows new time.
6. [ ] Delivery handoff returns without exception -> scheduler marks `reminder_sent`; dispatcher result still reflects actual Discord delivery outcome.
7. [ ] Click `Complete Task` -> task is completed through normal task handler behavior.
8. [ ] Click `Remind Me Later` -> only acknowledgement appears; task remains active.
9. [ ] Click `More` -> short ID and title examples appear ephemerally.
10. [ ] Unlinked user clicks a task button -> account-not-found message appears; task remains unchanged.
11. [ ] Complete recurring task from reminder -> next instance/reminder behavior is correct.

## Related documentation

- [SPECS_GUIDE.md](SPECS_GUIDE.md) - how behavior specs fit the project  
- [COMMUNICATION_GUIDE.md](../communication/COMMUNICATION_GUIDE.md) - channel-agnostic architecture  
- [DISCORD_GUIDE.md](../communication/communication_channels/discord/DISCORD_GUIDE.md) - Discord adapter overview  
- [TESTING_GUIDE.md](../tests/TESTING_GUIDE.md) - running automated tests  
