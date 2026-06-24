# Manual Discord Testing Guide

> **File**: `tests/MANUAL_DISCORD_TEST_GUIDE.md`  
> **Audience**: Developers and AI assistants performing manual Discord testing  
> **Purpose**: Quick reference for Discord bot manual testing  
> **Style**: Command-focused, concise examples

This guide provides quick test commands for Discord bot features. For detailed testing procedures, see [MANUAL_TESTING_GUIDE.md](MANUAL_TESTING_GUIDE.md). For scenario-by-scenario automated/manual/gap coverage, see [SPEC_COVERAGE_MATRIX.md](../specs/SPEC_COVERAGE_MATRIX.md).

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

## 4. Quick Test Checklist

### 4.1. Task Reminders
- [ ] Create task with minutes/hours/days before reminders
- [ ] Create task with no reminders
- [ ] Task without due date (should error)
- [ ] Flow cancellation
- [ ] Multiple tasks in sequence

### 4.2. Notebook - Notes
- [ ] Basic note creation (bang, slash, natural language)
- [ ] Note with title and body (colon, newline, natural language)
- [ ] Quick notes (all aliases: qn, qnote, quickn, quicknote, q note, quick note)
- [ ] Notes with tags (#hash and key:value)
- [ ] View recent entries
- [ ] Show entry by ID
- [ ] Append to entry
- [ ] Set entry body
- [ ] Add/remove tags
- [ ] Pin/unpin
- [ ] Archive/unarchive
- [ ] Set group
- [ ] View by group/inbox/pinned/archived

### 4.3. Notebook - Lists
- [ ] Create list (title only)
- [ ] Create list with items
- [ ] Add list item
- [ ] Toggle item done/undone
- [ ] Remove list item

### 4.4. Notebook - Journals
- [ ] Create journal entry

### 4.5. Notebook - Search & Organization
- [ ] Search entries
- [ ] Group management
- [ ] Organization views (inbox, pinned, archived, by group)

### 4.6. Notebook - Edge Cases
- [ ] Empty commands
- [ ] Special characters
- [ ] Very long content
- [ ] Invalid entry references
- [ ] Invalid list item indices
- [ ] Pagination buttons (Show More preserves query/filter/offset; re-run original command if button missing)

### 4.7. Verification
- [ ] Verify entries.json structure and data
- [ ] Check short IDs have no dashes
- [ ] Verify groups are set correctly
- [ ] Verify tags are normalized

---

## 5. Known Issues

- **Pagination Buttons**: Implemented via generic pagination metadata and Show More buttons. Validate live that repeated clicks preserve the original query/filter. If a button expires, re-run the original command.

---

## 6. Live Validation Session (task flows + notebook pagination)

Use this checklist after flow-control or pagination changes. Prerequisites: headless service running (`python run_headless_service.py start`), bot online in your test server.

**Tip**: Grey buttons = flow controls (Skip, Undo). Blue buttons = suggestions (priority levels, reminder options).

### 6.1. Task creation follow-up flows

**A. `nt call dentist` -> Skip due date -> priority buttons** (June 2026 regression)

```
nt call dentist
```
- [ ] Bot asks for due date/time
- [ ] Grey buttons: **Skip Question**, **Skip All**, **Undo Task Creation** (not plain `[Skip]` text)
- [ ] Tap **Skip Question**
- [ ] Bot asks for priority
- [ ] Blue priority buttons: **Low**, **Medium**, **High**, **Critical**
- [ ] Grey buttons again: **Skip Question**, **Skip All**, **Undo Task Creation**
- [ ] Tap **High** (or type `high`) -> task saved, **no** reminder prompt (no due date)

**B. Full flow with due date**

```
create task to buy groceries tomorrow at 2pm
```
- [ ] Task created as **buy groceries** (not "buy groceries at 2pm"); due shows date **and time** (e.g. `at 14:00`)
- [ ] Priority step appears (skip or pick one)
- [ ] Reminder step appears after priority
- [ ] `30 minutes to an hour before` sets reminder **13:00-13:30** (not 08:00-08:30)
- [ ] `show my tasks` lists the new task **once** (no duplicate embed + text); **Show More** when more than 10 tasks

**C. Flow control edge cases**

```
nt organize desk
```
- [ ] Due-date step -> tap **Undo Task Creation** -> task removed, flow cleared

```
nt test back flow
```
- [ ] Skip due date -> at priority step type `back` -> returns to due-date question

```
nt timeout test
```
- [ ] Start flow, wait 10+ minutes (or send unrelated message) -> flow auto-completes like Skip All

### 6.2. Notebook Show More pagination

Create enough entries first (run several `!qn pagination-test-1` through `!qn pagination-test-8` or use existing data).

| Command | Check |
|---------|-------|
| `!recent` | [ ] Page 1 shows entries; **Show More** appears if more exist |
| `!s pagination` | [ ] Search query preserved on page 2 |
| `!inbox` | [ ] Inbox filter preserved |
| `!pinned` | [ ] Pinned filter preserved |
| `!archived` | [ ] Archived filter preserved |
| `!t <tag>` | [ ] Tag filter preserved |
| `!group <group>` | [ ] Group filter preserved |

For each command that shows **Show More**:
- [ ] Tap **Show More** -> page 2 shows different entries (not a repeat of page 1)
- [ ] Tap **Show More** again until exhausted -> final page has **no** stale Show More button
- [ ] Run a different notebook command, then return -> pagination still works

### 6.3. Sign-off

When all boxes pass, update:
- [ ] [TASKS_PLAN.md](../development_docs/TASKS_PLAN.md) section 1 checkboxes
- [ ] [NOTES_PLAN.md](../development_docs/NOTES_PLAN.md) section 4.1 checkboxes
- [ ] Changelog follow-up note in [CHANGELOG_DETAIL.md](../development_docs/CHANGELOG_DETAIL.md) if this closes the June 2026 validation slice

Record any failures with the exact message sent, what the bot replied, and whether buttons appeared.

---

**Note**: This guide focuses on Discord-specific manual testing. For general testing procedures, see [TESTING_GUIDE.md](TESTING_GUIDE.md).
