# Manual Discord Testing Guide

> **File**: `tests/MANUAL_DISCORD_TEST_GUIDE.md`  
> **Audience**: Developers and AI assistants performing manual Discord testing  
> **Purpose**: Manual testing procedures for Discord bot task reminder flows  
> **Style**: Step-by-step, checklist-focused, actionable  
> **Parent**: [MANUAL_TESTING_GUIDE.md](tests/MANUAL_TESTING_GUIDE.md)  
> This document is subordinate to [MANUAL_TESTING_GUIDE.md](tests/MANUAL_TESTING_GUIDE.md) and should be kept consistent with its standards and terminology.

This guide focuses on **Discord-specific manual flows**, especially task reminder creation and follow-up.  
The high-level context and when to run these tests are described in section 6 of [MANUAL_TESTING_GUIDE.md](tests/MANUAL_TESTING_GUIDE.md).

---

## 1. Prerequisites

Before running manual Discord tests:

- [ ] Discord bot is running (`python run_headless_service.py start`)
- [ ] Bot is connected to your test server
- [ ] You have a test user account set up
- [ ] Task management is enabled for your user (if testing task features)

## 2. Task Reminder Follow-up Flow Testing

This section covers testing the reminder period follow-up flow that occurs after task creation.

### 2.1. Basic Test Scenarios

#### Test 1: Basic Reminder Flow - Minutes Before
1. Send: `create task to call dentist tomorrow at 2pm`
2. Bot should respond asking about reminder periods
3. Send: `30 minutes to an hour before`
4. Bot should confirm reminders were set

**Verify**:
- Task appears in task list (`show my tasks` or `/tasks`)
- Task has `reminder_periods` field populated
- Reminder times are approximately 30-60 minutes before 2pm (1:00-1:30 PM)

#### Test 2: Hours Before Reminder
1. Send: `create task to buy groceries tomorrow at 3pm`
2. Bot asks about reminders
3. Send: `3 to 5 hours before`
4. Bot confirms

**Expected**: Reminder periods set for 3-5 hours before 3pm (10 AM - 12 PM)

#### Test 3: Days Before Reminder
1. Send: `create task to prepare presentation next Friday`
2. Bot asks about reminders
3. Send: `1 to 2 days before`
4. Bot confirms

**Expected**: Reminder periods set for 1-2 days before due date

#### Test 4: No Reminders
1. Send: `create task to water plants tomorrow`
2. Bot asks about reminders
3. Send: `no reminders` (or `no`, `skip`, `none`, `not needed`)
4. Bot acknowledges

**Expected**: Task created, bot responds "Got it! No reminders will be set for this task."

#### Test 5: Task Without Due Date
1. Send: `create task to organize desk`
2. Bot asks about reminders
3. Send: `30 minutes before`

**Expected**: Bot responds that task doesn't have a due date, so reminders can't be set

#### Test 6: Unparseable Response
1. Send: `create task to call mom tomorrow at 1pm`
2. Bot asks about reminders
3. Send: `maybe sometime` (or `later`, `idk`, `whatever`)
4. Bot asks for clarification

**Expected**: Bot provides examples and asks for clearer response

#### Test 7: Flow Cancellation
1. Send: `create task to schedule appointment tomorrow`
2. Bot asks about reminders
3. Send: `/cancel` (or `cancel`)
4. Flow should be cancelled

**Expected**: Flow cancelled, task still exists, no reminder periods set

#### Test 8: Multiple Tasks in Sequence
1. Send: `create task to call dentist tomorrow at 2pm`
2. Bot asks about reminders
3. Send: `1 hour before`
4. Bot confirms
5. Immediately send: `create task to buy groceries tomorrow at 3pm`
6. Bot asks about reminders again
7. Send: `no reminders`

**Expected**: Both tasks created independently, no flow state conflicts

#### Test 9: Natural Language Variations
Test different ways to express reminder times:
- `30 minutes to an hour before` ✅
- `30 min to 1 hour before` ✅
- `3-5 hours before` ✅
- `3 to 5 hours before` ✅
- `1-2 days before` ✅
- `1 day before` ✅
- `2 hours before` ✅

**Expected**: Common variations work, unparseable variations ask for clarification

#### Test 10: Task Update After Creation
1. Send: `create task to call dentist tomorrow`
2. Bot asks about reminders
3. Send: `no reminders`
4. Bot confirms
5. Send: `update task call dentist due date tomorrow at 2pm`
6. Send: `update task call dentist reminder periods 30 minutes before`

**Expected**: Task updated with due date and reminder periods, reminders scheduled

#### Test 11: Reminder Follow-up with Due Time
1. Send: `create task to attend meeting tomorrow at 3pm`
2. Bot asks about reminders
3. Send: `30 minutes to an hour before`
4. Bot confirms

**Expected**: Reminder times calculated correctly based on due_time (2:00-2:30 PM)

#### Test 12: Reminder Follow-up Without Due Time
1. Send: `create task to finish report tomorrow`
2. Bot asks about reminders
3. Send: `1 hour before`
4. Bot confirms

**Expected**: Reminder times calculated based on default 9 AM time (8:00 AM)

### 2.2. Edge Cases

- **Very Short Time Window**: Create task due in 1 hour, try to set "30 minutes to an hour before" (should work if reminder time is still in the future)
- **Past Due Date**: Create task with past due date, try to set reminders (should handle gracefully)
- **Multiple Reminder Responses**: Send multiple responses before bot processes (only first response should be processed)
- **Special Characters**: Create task with special characters in title, set reminders (should work correctly)

## 3. Verification Commands

After each test, verify the results:

1. **Check task exists**: `show my tasks` or `/tasks`
2. **Check task details**: Look for `reminder_periods` in task display
3. **Check flow state**: Try another command to ensure flow is cleared
4. **Check logs**: Review `logs/errors.log` for any errors

## 4. Success Criteria

✅ **All tests pass if**:
- Task creation always triggers reminder follow-up (when task has due date)
- Natural language parsing works for common patterns
- Reminder periods are saved to task
- Flow completes correctly
- No flow state leaks between tasks
- Error handling is graceful

## 5. Known Issues to Watch For

⚠️ **If you see these, note them**:
- Reminder periods not saved to task
- Flow doesn't complete after setting reminders
- Flow state persists after completion
- Parsing fails for valid inputs
- Error messages are unclear
- Bot doesn't respond to reminder questions

## 6. Reporting Results

After testing, report:
- ✅ Which tests passed
- ❌ Which tests failed
- 🐛 Any bugs found
- 💡 Any improvements needed
- 📝 Screenshots/logs of issues

## 7. Quick Test Checklist

- [ ] Test 1: Basic minutes before
- [ ] Test 2: Hours before
- [ ] Test 3: Days before
- [ ] Test 4: No reminders
- [ ] Test 5: Task without due date
- [ ] Test 6: Unparseable response
- [ ] Test 7: Flow cancellation
- [ ] Test 8: Multiple tasks
- [ ] Test 9: Natural language variations
- [ ] Test 10: Task update after creation
- [ ] Test 11: With due time
- [ ] Test 12: Without due time

---

**Note**: This guide focuses on task reminder follow-up flow. For general Discord integration testing, see the "Discord integration" section in [TESTING_GUIDE.md](tests/TESTING_GUIDE.md) (section 9.2).

