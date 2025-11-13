# Manual Discord Testing: Task Reminder Follow-up Flow

**Purpose**: Test the reminder period follow-up flow that occurs after task creation  
**Date**: 2025-11-12  
**Status**: Ready for Testing

---

## Prerequisites

- [ ] Discord bot is running (`python run_headless_service.py start`)
- [ ] Bot is connected to your test server
- [ ] You have a test user account set up
- [ ] Task management is enabled for your user

---

## Test Scenarios

### ✅ Test 1: Basic Reminder Flow - Minutes Before

**Steps**:
1. Send: `create task to call dentist tomorrow at 2pm`
2. Bot should respond asking about reminder periods
3. Send: `30 minutes to an hour before`
4. Bot should confirm reminders were set

**Expected Results**:
- ✅ Task is created successfully
- ✅ Bot asks: "Would you like to set reminder periods for this task?"
- ✅ Bot provides suggestion buttons/options
- ✅ After response, bot confirms: "✅ Reminder periods set for this task: [date] [time]-[time]"
- ✅ Task has reminder_periods saved (check via `/tasks` or `show my tasks`)

**Verify**:
- Task appears in task list
- Task has reminder_periods field populated
- Reminder times are approximately 30-60 minutes before 2pm (1:00-1:30 PM)

---

### ✅ Test 2: Hours Before Reminder

**Steps**:
1. Send: `create task to buy groceries tomorrow at 3pm`
2. Bot asks about reminders
3. Send: `3 to 5 hours before`
4. Bot confirms

**Expected Results**:
- ✅ Task created
- ✅ Reminder periods set for 3-5 hours before 3pm (10 AM - 12 PM)
- ✅ Confirmation message shows correct times

---

### ✅ Test 3: Days Before Reminder

**Steps**:
1. Send: `create task to prepare presentation next Friday`
2. Bot asks about reminders
3. Send: `1 to 2 days before`
4. Bot confirms

**Expected Results**:
- ✅ Task created with due date next Friday
- ✅ Reminder periods set for 1-2 days before due date
- ✅ Confirmation shows correct dates and times

---

### ✅ Test 4: No Reminders

**Steps**:
1. Send: `create task to water plants tomorrow`
2. Bot asks about reminders
3. Send: `no reminders` (or `no`, `skip`, `none`, `not needed`)
4. Bot acknowledges

**Expected Results**:
- ✅ Task created successfully
- ✅ Bot responds: "Got it! No reminders will be set for this task."
- ✅ Flow completes
- ✅ Task has no reminder_periods field (or empty list)

---

### ✅ Test 5: Task Without Due Date

**Steps**:
1. Send: `create task to organize desk`
2. Bot asks about reminders
3. Send: `30 minutes before`

**Expected Results**:
- ✅ Task created (no due date)
- ✅ Bot responds: "This task doesn't have a due date, so I can't set reminder periods. You can add a due date and reminders later by updating the task."
- ✅ Flow completes gracefully
- ✅ Task exists but has no reminder_periods

---

### ✅ Test 6: Unparseable Response

**Steps**:
1. Send: `create task to call mom tomorrow at 1pm`
2. Bot asks about reminders
3. Send: `maybe sometime` (or `later`, `idk`, `whatever`)
4. Bot asks for clarification

**Expected Results**:
- ✅ Bot responds: "I'm not sure what reminder timing you'd like. Please specify something like:"
- ✅ Bot provides examples: "30 minutes to an hour before", "3 to 5 hours before", etc.
- ✅ Flow continues (not completed)
- ✅ User can try again with clearer response

---

### ✅ Test 7: Flow Cancellation

**Steps**:
1. Send: `create task to schedule appointment tomorrow`
2. Bot asks about reminders
3. Send: `/cancel` (or `cancel`)
4. Flow should be cancelled

**Expected Results**:
- ✅ Flow is cancelled
- ✅ Task still exists (was created)
- ✅ No reminder periods set
- ✅ User can continue with other commands

---

### ✅ Test 8: Multiple Tasks in Sequence

**Steps**:
1. Send: `create task to call dentist tomorrow at 2pm`
2. Bot asks about reminders
3. Send: `1 hour before`
4. Bot confirms
5. Immediately send: `create task to buy groceries tomorrow at 3pm`
6. Bot asks about reminders again
7. Send: `no reminders`

**Expected Results**:
- ✅ First task created with reminders
- ✅ Flow completes for first task
- ✅ Second task creation starts new flow
- ✅ Second task created without reminders
- ✅ Both tasks exist independently
- ✅ No flow state conflicts

---

### ✅ Test 9: Natural Language Variations

**Test different ways to express reminder times**:

**Variations to try**:
- `30 minutes to an hour before` ✅
- `30 min to 1 hour before` ✅
- `half hour to an hour before` (may not work)
- `3-5 hours before` ✅
- `3 to 5 hours before` ✅
- `1-2 days before` ✅
- `one to two days before` (may not work)
- `1 day before` ✅
- `2 hours before` ✅

**Expected Results**:
- ✅ Common variations work
- ✅ Bot handles variations gracefully
- ✅ Unparseable variations ask for clarification

---

### ✅ Test 10: Task Update After Creation

**Steps**:
1. Send: `create task to call dentist tomorrow`
2. Bot asks about reminders
3. Send: `no reminders`
4. Bot confirms
5. Send: `update task call dentist due date tomorrow at 2pm`
6. Send: `update task call dentist reminder periods 30 minutes before`

**Expected Results**:
- ✅ Task created without reminders
- ✅ Task updated with due date
- ✅ Task updated with reminder periods
- ✅ Reminders are scheduled for updated task

---

### ✅ Test 11: Reminder Follow-up with Due Time

**Steps**:
1. Send: `create task to attend meeting tomorrow at 3pm`
2. Bot asks about reminders
3. Send: `30 minutes to an hour before`
4. Bot confirms

**Expected Results**:
- ✅ Task has both due_date and due_time
- ✅ Reminder periods calculated correctly based on due_time
- ✅ Reminder times are approximately 2:00-2:30 PM (30-60 min before 3pm)

---

### ✅ Test 12: Reminder Follow-up Without Due Time

**Steps**:
1. Send: `create task to finish report tomorrow`
2. Bot asks about reminders
3. Send: `1 hour before`
4. Bot confirms

**Expected Results**:
- ✅ Task has due_date but no due_time (defaults to 9 AM)
- ✅ Reminder periods calculated based on default 9 AM time
- ✅ Reminder times are approximately 8:00 AM (1 hour before 9 AM)

---

## Edge Cases to Test

### Edge Case 1: Very Short Time Window
- Create task due in 1 hour
- Try to set "30 minutes to an hour before"
- **Expected**: Should work if reminder time is still in the future

### Edge Case 2: Past Due Date
- Create task with past due date
- Try to set reminders
- **Expected**: Should handle gracefully (reminder times would be in the past)

### Edge Case 3: Multiple Reminder Responses
- Create task
- Bot asks about reminders
- Send multiple responses before bot processes
- **Expected**: Only first response processed, flow completes

### Edge Case 4: Special Characters in Task Title
- Create task with special characters: `create task "Call Dr. Smith's office" tomorrow`
- Set reminders
- **Expected**: Task created and reminders set correctly

---

## Verification Commands

After each test, verify the results:

1. **Check task exists**: `show my tasks` or `/tasks`
2. **Check task details**: Look for reminder_periods in task display
3. **Check flow state**: Try another command to ensure flow is cleared
4. **Check logs**: Review `logs/errors.log` for any errors

---

## Success Criteria

✅ **All tests pass if**:
- Task creation always triggers reminder follow-up (when task has due date)
- Natural language parsing works for common patterns
- Reminder periods are saved to task
- Flow completes correctly
- No flow state leaks between tasks
- Error handling is graceful

---

## Known Issues to Watch For

⚠️ **If you see these, note them**:
- Reminder periods not saved to task
- Flow doesn't complete after setting reminders
- Flow state persists after completion
- Parsing fails for valid inputs
- Error messages are unclear
- Bot doesn't respond to reminder questions

---

## Reporting Results

After testing, report:
- ✅ Which tests passed
- ❌ Which tests failed
- 🐛 Any bugs found
- 💡 Any improvements needed
- 📝 Screenshots/logs of issues

---

## Quick Test Checklist

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

**Happy Testing! 🧪**

