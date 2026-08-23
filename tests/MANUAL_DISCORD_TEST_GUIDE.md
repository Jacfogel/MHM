# Manual Discord Testing Guide

> **File**: `tests/MANUAL_DISCORD_TEST_GUIDE.md`  
> **Audience**: Developers and AI assistants performing manual Discord testing  
> **Purpose**: Quick reference for Discord bot manual testing  
> **Style**: Command-focused, concise examples

Checklist behavior is automated. After Discord task, notebook, routing, or onboarding changes, run the mapped pytest files instead of walking Discord by hand. Command examples below stay as a quick reference for live smoke if you want to see phrasing. For detailed testing procedures, see [MANUAL_TESTING_GUIDE.md](MANUAL_TESTING_GUIDE.md). For scenario-by-scenario coverage, see [SPEC_COVERAGE_MATRIX.md](../specs/SPEC_COVERAGE_MATRIX.md).

---

## 1. Prerequisites

- [ ] Discord bot is running (`python run_headless_service.py start`)
- [ ] Bot is connected to your test server
- [ ] Test user account set up

---

## 2. Task Reminder Testing

### 2.1. Basic Flows

**Create task with reminders:**
```
create task to call dentist tomorrow at 2pm
30 minutes to an hour before
```

**No reminders:**
```
create task to water plants tomorrow
no reminders
```

**Task without due date:**
```
create task to organize desk
30 minutes before
```
*Expected: Error - no due date*

**Flow cancellation:**
```
create task to schedule appointment tomorrow
cancel
```

**Verify**: Check task list with `show my tasks` or `/tasks`

---

## 3. Notebook Feature Testing

### 3.1. Important Notes

- **Data Location**: `data/users/<user_id>/notebook/entries.json`
- **Short IDs**: Format is `nxxxxxx` (no dashes)
- **Flow Buttons**: [Skip], [Cancel], [End List] can be clicked or typed as commands
- **Natural Language**: `create note about X` works; `new note: X` works (colon-separated now supported)

### 3.2. Note Creation

**Basic notes (prompts for body):**

```
!n Test note
[Skip]
```

```
/n Test note
/skip
```

```
create note about meeting tomorrow
[Skip]
```

---

**Notes with title and body:**

```
!n Title: Body text here
```

```
/n Title: Body text here
```

```
!n Multi-line
note
with body
```

```
create note titled "Meeting notes" with body "Discussed project timeline"
```

---

**Quick notes (no body, auto-grouped as "Quick Notes"):**

```
!qn
```

```
!qn Project idea
```

```
!qnote Reminder
```

```
!quickn Meeting notes
```

```
!quicknote Shopping list
```

```
!q note Quick thought
```

```
quick note Important reminder
```

---

**Notes with tags:**

```
!n Work task #work #urgent
[Skip]
```

```
!note project:alpha meeting notes
[Skip]
```

```
!qn Work task #work #urgent
```

### 3.3. Viewing Entries

```
!recent
```

```
!recent 10
```

```
/r 5
```

```
!show nxxxxxx
```

```
/show nxxxxxx
```

---

### 3.4. Editing Entries

```
!append nxxxxxx Additional text
```

```
!set nxxxxxx New body text
```

```
!tag nxxxxxx #work #urgent
```

```
!untag nxxxxxx work
```

---

### 3.5. Organization

```
!pin nxxxxxx
```

```
!unpin nxxxxxx
```

```
!archive nxxxxxx
```

```
!unarchive nxxxxxx
```

```
!group nxxxxxx work
```

```
!group Quick Notes
```

```
!inbox
```

```
!pinned
```

```
!archived
```

### 3.6. Lists

**Create list:**

```
!l Shopping list
[End List]
```

```
/l Shopping list
/end
```

```
!l Groceries
milk
eggs
bread
[End List]
```

---

**List operations:**

```
!l add lxxxxxx Buy milk
```

```
!l done lxxxxxx 1
```

```
!l undo lxxxxxx 1
```

```
!l remove lxxxxxx 2
```

---

### 3.7. Journal Entries

```
!j Today was productive
```

```
!journal Daily reflection
[Skip]
```

```
/j Morning thoughts
/skip
```

### 3.8. Search

```
!search project
```

```
/s project
```

```
!s meeting notes
```

```
find work tasks
```

---

### 3.9. Error Handling

```
!show invalidid
```
*Expected: Error message*

```
!tag invalidid with work
```
*Expected: Error message*

```
!l done lxxxxxx 99
```
*Expected: Error for invalid item index*

---

## 4. Automated checklist map

Run `pytest tests/behavior/test_discord_manual_checklist.py` plus the files named below. Live Discord is only for tone and the actual client (bot online, expired buttons).

### 4.1. Task Reminders

| Checklist item | Automated test |
|---|---|
| Create task with minutes/hours/days before reminders | `test_discord_reminder_followup_complete_flow`; minutes/hours/days in `tests/behavior/test_task_reminder_followup_behavior.py` |
| Create task with no reminders | `test_discord_reminder_followup_no_reminders` |
| Task without due date (reminder errors) | `test_discord_task_without_due_date_reminder_errors`; `test_reminder_followup_handles_task_without_due_date` |
| Flow cancellation | `test_discord_flow_cancel_clears_created_task`; `test_due_date_undo_deletes_task` |
| Multiple tasks in sequence | `test_discord_multiple_tasks_in_sequence` |

### 4.2. Notebook - Notes

| Checklist item | Automated test |
|---|---|
| Basic note creation (bang, slash, natural language) | `test_note_creation_command_variations_end_to_end`; `test_command_parser_recognizes_note_commands` |
| Note with title and body (colon, newline, natural language) | `test_create_note_with_title_and_body`; `test_extract_title_and_body_*` |
| Quick notes (qn, qnote, quickn, quicknote, q note, quick note) | `test_quick_note_aliases_create_quick_notes_group` |
| Notes with tags (`#hash` and `key:value`) | `test_create_note_with_tags`; `test_extract_tags_from_note_command` |
| View recent entries | `test_list_recent_entries`; `test_recent_command_variations` |
| Show entry by ID | `test_show_entry` |
| Append to entry | `test_append_to_entry` |
| Set entry body | `test_set_entry_body_replaces_text` |
| Add/remove tags | `test_add_tags_to_entry`; `test_remove_tags_from_entry` |
| Pin/unpin | `test_pin_entry`; `test_unpin_and_archive_unarchive` |
| Archive/unarchive | `test_unpin_and_archive_unarchive` |
| Set group | `test_set_group_and_list_inbox` |
| View by group/inbox/pinned/archived | `test_paginated_notebook_views_include_pagination_action`; `test_list_pinned_entries` |

### 4.3. Notebook - Lists

| Checklist item | Automated test |
|---|---|
| Create list (title only) | `test_create_list_with_title_only` |
| Create list with items | `test_create_list_with_items` |
| Add list item | `test_add_list_item` |
| Toggle item done/undone | `test_toggle_list_item_done`; `test_toggle_list_item_undone_and_remove_item` |
| Remove list item | `test_toggle_list_item_undone_and_remove_item` |

### 4.4. Notebook - Journals

| Checklist item | Automated test |
|---|---|
| Create journal entry | `test_create_journal_with_body`; `test_journal_body_flow_skip_saves_title_only` |

### 4.5. Notebook - Search & Organization

| Checklist item | Automated test |
|---|---|
| Search entries | `test_search_entries` |
| Group management | `test_set_group_and_list_inbox` |
| Organization views (inbox, pinned, archived, by group) | `test_paginated_notebook_views_include_pagination_action` |

### 4.6. Notebook - Edge Cases

| Checklist item | Automated test |
|---|---|
| Empty commands | `test_handle_missing_entities_gracefully`; `test_handle_empty_entities` |
| Special characters | `test_create_entry_with_special_characters` |
| Very long content | `test_create_entry_with_very_long_title` |
| Invalid entry references | `test_invalid_entry_reference`; `test_show_entry_not_found` |
| Invalid list item indices | `test_toggle_invalid_item_index` |
| Pagination buttons preserve query/filter/offset | `test_paginated_notebook_views_include_pagination_action`; `test_recent_pagination_exhausts_without_stale_show_more` |

### 4.7. Verification

| Checklist item | Automated test |
|---|---|
| entries.json structure | `test_entries_json_short_ids_groups_and_normalized_tags` |
| Short IDs have no dashes | same |
| Groups are set correctly | same; `test_set_group_and_list_inbox` |
| Tags are normalized | same (`#Work` / `URGENT` -> `work`, `urgent`) |

---

## 5. Known Issues

- **Expired Discord buttons**: Automated tests cover payload and paging metadata. If a live button expires, re-run the original command. That client timeout is not a pytest case.

---

## 6. Task flows and notebook pagination

Behavior is automated. Grey vs blue button **styles** are asserted in `test_discord_button_style_for_flow_suggestions` (secondary/danger vs primary). Optional live check: bot online and the real client still looks right.

### 6.1. Task creation follow-up flows

**A. `nt call dentist` -> Skip due date -> priority buttons**

| Check | Automated test |
|---|---|
| Bot asks for due date/time | `test_nt_call_dentist_skip_due_date_shows_priority_buttons` |
| Control suggestions are Skip Question / Skip All / Undo Task Creation | same; `test_nt_skip_due_date_high_saves_without_reminder_prompt` |
| Skip Question then priority buttons | same |
| High / typed `high` saves with no reminder prompt | `test_nt_skip_due_date_high_saves_without_reminder_prompt`; `test_skip_due_date_then_priority_skips_reminders_without_due_date` |

**B. Full flow with due date**

| Check | Automated test |
|---|---|
| Title is `buy groceries`; due includes `14:00` | `test_discord_tomorrow_at_2pm_reminder_uses_due_time` |
| Priority then reminder steps | same |
| `30 minutes to an hour before` -> 13:00-13:30 | same |
| `show my tasks` lists once; Show More after 10 | `test_task_handler_list_tasks_pagination_and_due_time` (`type` omitted from rich_data; page 2 has no stale Show More) |

**C. Flow control edge cases**

| Check | Automated test |
|---|---|
| Undo Task Creation removes the task | `test_due_date_undo_deletes_task`; `test_discord_flow_cancel_clears_created_task` |
| `back` from priority returns to due date | `test_priority_back_returns_to_due_date_flow` |
| Timeout / unrelated message completes like Skip All | `test_priority_timeout_unrelated_skips_all_without_priority` |

**D. Task list picker and detail view**

| Check | Automated test |
|---|---|
| List once (no duplicate embed type) | `test_task_handler_list_tasks_pagination_and_due_time` |
| Dropdown title + short ID | `test_task_list_select_includes_title_and_short_id` |
| Show More after 10 tasks | `test_task_handler_list_tasks_pagination_and_due_time`; `test_get_task_list_view_adds_show_more_button` |
| Detail shows title, priority, due, reminders, ID | `test_format_task_detail_display_includes_due_time_and_reminders` |
| Due Date / Priority start follow-up | `test_task_flow_response_due_date_starts_flow`; `test_task_flow_response_priority_asks_reminders_when_due_set` |
| Reminders without due date (no trap) | `test_task_flow_response_reminders_requires_due_date` |
| Reminders with due date start follow-up | `test_task_flow_response_reminders_starts_followup` |
| Complete confirmation | `test_detail_complete_button_runs_handler` |
| More shows update/delete hints | `test_more_button_shows_update_and_delete_hints` |

### 6.2. Notebook Show More pagination

| Command | Automated test |
|---|---|
| `!recent` page 1 + Show More | `test_paginated_notebook_views_include_pagination_action` (`list_recent_entries`); `test_recent_pagination_exhausts_without_stale_show_more` |
| `!s` query preserved | same parametrize (`search_entries`) |
| `!inbox` filter preserved | same (`list_inbox_entries`) |
| `!pinned` filter preserved | same (`list_pinned_entries`) |
| `!archived` filter preserved | same (`list_archived_entries`) |
| `!t <tag>` filter preserved | same (`list_entries_by_tag`) |
| `!group <group>` filter preserved | same (`list_entries_by_group`) |
| Page 2 is different; last page has no Show More | `test_recent_pagination_exhausts_without_stale_show_more` |

### 6.3. Sign-off

Behavior coverage for this guide is in pytest. [TASKS_PLAN.md](../development_docs/TASKS_PLAN.md) section 1 and [NOTES_PLAN.md](../development_docs/NOTES_PLAN.md) section 4.1 now point at those tests. Optional live Discord is visual/tone only.

Record any live failures with the exact message sent, what the bot replied, and whether buttons appeared.

---

**Note**: This guide focuses on Discord-specific manual testing. For general testing procedures, see [TESTING_GUIDE.md](TESTING_GUIDE.md).
