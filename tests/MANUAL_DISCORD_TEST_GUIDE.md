# Manual Discord Testing Guide

> **File**: `tests/MANUAL_DISCORD_TEST_GUIDE.md`  
> **Audience**: Developers and AI assistants performing manual Discord testing  
> **Purpose**: Quick reference for Discord bot manual testing  
> **Style**: Command-focused, concise examples

This guide provides quick test commands for Discord bot features. For detailed testing procedures, see [MANUAL_TESTING_GUIDE.md](tests/MANUAL_TESTING_GUIDE.md).

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
- [ ] Pagination buttons (known issue - state not preserved)

### 4.7. Verification
- [ ] Verify entries.json structure and data
- [ ] Check short IDs have no dashes
- [ ] Verify groups are set correctly
- [ ] Verify tags are normalized

---

## 5. Known Issues

- **Pagination Buttons**: "Show More" button click handler doesn't preserve pagination state. Users must re-run the original command to see more results.

---

**Note**: This guide focuses on Discord-specific manual testing. For general testing procedures, see [TESTING_GUIDE.md](tests/TESTING_GUIDE.md).
