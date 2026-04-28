# Legacy Reference Cleanup Report

> **File**: `development_docs/LEGACY_REFERENCE_REPORT.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2026-04-28 03:36:13
> **Source**: `python development_tools/generate_legacy_reference_report.py` - Legacy Reference Report Generator
**Total Files with Issues**: 95
**Legacy Compatibility Markers Detected**: 1599

## Summary
- Scan mode only: no automated fixes were applied.
- Changelogs, archive folders, and planning documents are intentionally historical and excluded from this report.
- Legacy compatibility markers remain in 4 file(s) (11 total markers).
- Remaining counts come from legacy inventory tracking categories (91 file(s), 1588 marker(s)).

## Recommended Follow-Up
- Additional guidance: [AI_LEGACY_COMPATIBILITY_GUIDE.md](ai_development_docs/AI_LEGACY_COMPATIBILITY_GUIDE.md)
1. Identify active legacy compatibility behavior and migrate all callers/dependencies to current implementations before deleting markers.
2. Add or update regression tests that prove migrated flows work without legacy compatibility code paths. See [AI_TESTING_GUIDE.md](ai_development_docs/AI_TESTING_GUIDE.md) for additional guidance.
3. Only after migration is verified, remove legacy markers/comments/docs evidence and rerun `python development_tools/run_development_tools.py legacy --clean --dry-run` until this report returns zero issues.

## Deprecation Inventory
- Inventory file: `development_tools/config/jsons/DEPRECATION_INVENTORY.json`
- Active/candidate entries: 2
- Removed entries: 9
- Active search terms: 9
- Current inventory-term hits in scan: 75 file(s), 1183 marker(s)

## Deprecation Inventory Terms
**Files Affected**: 75

### communication\command_handlers\analytics_handler.py
**Issues Found**: 7

- **Line 950**: `completed_tasks`
  ```
  load_completed_tasks,
  ```

- **Line 957**: `completed_tasks`
  ```
  load_completed_tasks(user_id)
  ```

- **Line 1049**: `completed_tasks`
  ```
  load_completed_tasks,
  ```

- **Line 1055**: `completed_tasks`
  ```
  completed_tasks = load_completed_tasks(user_id)
  ```

- **Line 1055**: `completed_tasks`
  ```
  completed_tasks = load_completed_tasks(user_id)
  ```

- **Line 1093**: `completed_tasks`
  ```
  if completed_tasks:
  ```

- **Line 1095**: `completed_tasks`
  ```
  recent_completed = completed_tasks[:5]  # Show last 5
  ```

### communication\command_handlers\task_handler.py
**Issues Found**: 63

- **Line 264**: `task_id`
  ```
  task_id = _get_tasks().create_task(user_id=user_id, **task_data)
  ```

- **Line 266**: `task_id`
  ```
  if task_id:
  ```

- **Line 297**: `task_id`
  ```
  f"Task {task_id} has no valid due date (valid_due_date={valid_due_date}), starting due date flow"
  ```

- **Line 299**: `task_id`
  ```
  conversation_manager.start_task_due_date_flow(user_id, task_id)
  ```

- **Line 307**: `task_id`
  ```
  f"Task {task_id} has valid due date ({valid_due_date}), starting reminder flow"
  ```

- **Line 309**: `task_id`
  ```
  conversation_manager.start_task_reminder_followup(user_id, task_id)
  ```

- **Line 312**: `task_id`
  ```
  user_id, task_id
  ```

- **Line 775**: `task_id`
  ```
  task_identifier = entities.get("task_identifier")
  ```

- **Line 775**: `task_id`
  ```
  task_identifier = entities.get("task_identifier")
  ```

- **Line 776**: `task_id`
  ```
  if not task_identifier:
  ```

- **Line 793**: `task_id`
  ```
  task_id = suggested_task.get("task_id", "")
  ```

- **Line 793**: `task_id`
  ```
  task_id = suggested_task.get("task_id", "")
  ```

- **Line 794**: `task_id`
  ```
  short_id = task_id[:8] if task_id else ""
  ```

- **Line 794**: `task_id`
  ```
  short_id = task_id[:8] if task_id else ""
  ```

- **Line 819**: `task_id`
  ```
  candidates = self._get_task_candidates(tasks, task_identifier)
  ```

- **Line 836**: `task_id`
  ```
  if _get_tasks().complete_task(user_id, task.get("task_id", task.get("id"))):
  ```

- **Line 853**: `task_id`
  ```
  task_identifier = entities.get("task_identifier")
  ```

- **Line 853**: `task_id`
  ```
  task_identifier = entities.get("task_identifier")
  ```

- **Line 854**: `task_id`
  ```
  if not task_identifier:
  ```

- **Line 855**: `completed_tasks`
  ```
  completed_tasks = _get_tasks().load_completed_tasks(user_id)
  ```

- **Line 855**: `completed_tasks`
  ```
  completed_tasks = _get_tasks().load_completed_tasks(user_id)
  ```

- **Line 856**: `completed_tasks`
  ```
  if not completed_tasks:
  ```

- **Line 864**: `completed_tasks`
  ```
  completed_tasks = _get_tasks().load_completed_tasks(user_id)
  ```

- **Line 864**: `completed_tasks`
  ```
  completed_tasks = _get_tasks().load_completed_tasks(user_id)
  ```

- **Line 867**: `completed_tasks`
  ```
  for t in completed_tasks
  ```

- **Line 868**: `task_id`
  ```
  if str(task_identifier).strip().lower()
  ```

- **Line 870**: `task_id`
  ```
  str(t.get("task_id", "")).lower(),
  ```

- **Line 875**: `task_id`
  ```
  str(task_identifier).isdigit()
  ```

- **Line 876**: `task_id`
  ```
  and str(t.get("task_id", "")) == str(task_identifier)
  ```

- **Line 876**: `task_id`
  ```
  and str(t.get("task_id", "")) == str(task_identifier)
  ```

- **Line 882**: `completed_tasks`
  ```
  for t in completed_tasks
  ```

- **Line 883**: `task_id`
  ```
  if task_identifier.lower() in (t.get("title") or "").lower()
  ```

- **Line 892**: `task_id`
  ```
  task_id = task.get("task_id", task.get("id"))
  ```

- **Line 892**: `task_id`
  ```
  task_id = task.get("task_id", task.get("id"))
  ```

- **Line 893**: `task_id`
  ```
  if _get_tasks().restore_task(user_id, task_id):
  ```

- **Line 904**: `task_id`
  ```
  task_identifier = entities.get("task_identifier")
  ```

- **Line 904**: `task_id`
  ```
  task_identifier = entities.get("task_identifier")
  ```

- **Line 905**: `task_id`
  ```
  if not task_identifier:
  ```

- **Line 922**: `task_id`
  ```
  candidates = self._get_task_candidates(tasks, task_identifier)
  ```

- **Line 940**: `task_id`
  ```
  identifier_str = str(task_identifier).strip().lower()
  ```

- **Line 943**: `task_id`
  ```
  str(task.get("task_id", "")).lower(),
  ```

- **Line 948**: `task_id`
  ```
  PENDING_DELETIONS[user_id] = task.get("task_id", task.get("id"))
  ```

- **Line 956**: `task_id`
  ```
  if _get_tasks().delete_task(user_id, task.get("task_id", task.get("id"))):
  ```

- **Line 968**: `task_id`
  ```
  task_identifier = entities.get("task_identifier")
  ```

- **Line 968**: `task_id`
  ```
  task_identifier = entities.get("task_identifier")
  ```

- **Line 969**: `task_id`
  ```
  if not task_identifier:
  ```

- **Line 977**: `task_id`
  ```
  candidates = self._get_task_candidates(tasks, task_identifier)
  ```

- **Line 1016**: `task_id`
  ```
  f"{task_identifier}"
  ```

- **Line 1019**: `task_id`
  ```
  f"{task_identifier}"
  ```

- **Line 1022**: `task_id`
  ```
  f"{task_identifier}"
  ```

- **Line 1028**: `task_id`
  ```
  if _get_tasks().update_task(user_id, task.get("task_id", task.get("id")), updates):
  ```

- **Line 1085**: `completed_tasks`
  ```
  completed_tasks = overall_stats.get("completed_tasks", 0)
  ```

- **Line 1085**: `completed_tasks`
  ```
  completed_tasks = overall_stats.get("completed_tasks", 0)
  ```

- **Line 1086**: `completed_tasks`
  ```
  total_tasks = active_tasks + completed_tasks
  ```

- **Line 1089**: `completed_tasks`
  ```
  overall_completion_rate = (completed_tasks / total_tasks) * 100
  ```

- **Line 1092**: `completed_tasks`
  ```
  response += f"✅ **Completed Tasks:** {completed_tasks}\n"
  ```

- **Line 1111**: `task_id`
  ```
  Find a task by number, name, or task_id.
  ```

- **Line 1117**: `task_id`
  ```
  identifier: Task identifier (number, name, or task_id)
  ```

- **Line 1125**: `task_id`
  ```
  # Try as task_id first (UUID)
  ```

- **Line 1127**: `task_id`
  ```
  if task.get("task_id") == identifier or task.get("id") == identifier:
  ```

- **Line 1133**: `task_id`
  ```
  tid = task.get("task_id", "")
  ```

- **Line 1193**: `task_id`
  ```
  if identifier == t.get("task_id") or identifier == t.get("id"):
  ```

- **Line 1198**: `task_id`
  ```
  tid = t.get("task_id", "")
  ```

### communication\communication_channels\discord\api_client.py
**Issues Found**: 1

- **Line 24**: `message_id`
  ```
  message_id: str
  ```

### communication\communication_channels\discord\event_handler.py
**Issues Found**: 4

- **Line 41**: `message_id`
  ```
  message_id: str | None = None
  ```

- **Line 169**: `message_id`
  ```
  message_id=str(message.id),
  ```

- **Line 271**: `message_id`
  ```
  message_id=str(reaction.message.id),
  ```

- **Line 292**: `message_id`
  ```
  message_id=str(reaction.message.id),
  ```

### communication\communication_channels\discord\task_reminder_view.py
**Issues Found**: 15

- **Line 17**: `task_id`
  ```
  user_id: str, task_id: str, task_title: str
  ```

- **Line 24**: `task_id`
  ```
  task_id: The task ID
  ```

- **Line 33**: `task_id`
  ```
  def __init__(self, user_id: str, task_id: str, task_title: str):
  ```

- **Line 39**: `task_id`
  ```
  task_id: The task ID to display in the reminder
  ```

- **Line 44**: `task_id`
  ```
  self.task_id = task_id
  ```

- **Line 44**: `task_id`
  ```
  self.task_id = task_id
  ```

- **Line 50**: `task_id`
  ```
  custom_id=f"task_complete_{user_id}_{task_id}",
  ```

- **Line 73**: `task_id`
  ```
  # Try task_id first, then fall back to task title
  ```

- **Line 74**: `task_id`
  ```
  message = f"complete task {self.task_id}"
  ```

- **Line 85**: `task_id`
  ```
  custom_id=f"task_remind_later_{user_id}_{task_id}",
  ```

- **Line 103**: `task_id`
  ```
  custom_id=f"task_more_{user_id}_{task_id}",
  ```

- **Line 110**: `task_id`
  ```
  short_id = self.task_id[:8] if len(self.task_id) > 8 else self.task_id
  ```

- **Line 110**: `task_id`
  ```
  short_id = self.task_id[:8] if len(self.task_id) > 8 else self.task_id
  ```

- **Line 110**: `task_id`
  ```
  short_id = self.task_id[:8] if len(self.task_id) > 8 else self.task_id
  ```

- **Line 121**: `task_id`
  ```
  return TaskReminderView(user_id, task_id, task_title)
  ```

### communication\communication_channels\email\bot.py
**Issues Found**: 4

- **Line 223**: `message_id`
  ```
  status, message_ids = mail.search(None, "UNSEEN")
  ```

- **Line 225**: `message_id`
  ```
  if status != "OK" or not message_ids[0]:
  ```

- **Line 231**: `message_id`
  ```
  email_ids = message_ids[0].split()
  ```

- **Line 266**: `message_id`
  ```
  "message_id": email_id.decode(),
  ```

### communication\core\channel_orchestrator.py
**Issues Found**: 25

- **Line 81**: `task_id`
  ```
  )  # Track last task reminder per user: {user_id: task_id}
  ```

- **Line 291**: `message_id`
  ```
  email_id = email_msg.get("message_id")
  ```

- **Line 1638**: `message_id`
  ```
  message_id = str(uuid.uuid4())
  ```

- **Line 1656**: `message_id`
  ```
  message_id,
  ```

- **Line 1792**: `message_id`
  ```
  message_to_send["message_id"],
  ```

- **Line 1935**: `task_id`
  ```
  def handle_task_reminder(self, user_id: str, task_id: str):
  ```

- **Line 1951**: `task_id`
  ```
  # Validate task_id
  ```

- **Line 1952**: `task_id`
  ```
  if not task_id or not isinstance(task_id, str):
  ```

- **Line 1952**: `task_id`
  ```
  if not task_id or not isinstance(task_id, str):
  ```

- **Line 1953**: `task_id`
  ```
  logger.error(f"Invalid task_id: {task_id}")
  ```

- **Line 1953**: `task_id`
  ```
  logger.error(f"Invalid task_id: {task_id}")
  ```

- **Line 1956**: `task_id`
  ```
  if not task_id.strip():
  ```

- **Line 1957**: `task_id`
  ```
  logger.error("Empty task_id provided")
  ```

- **Line 1963**: `task_id`
  ```
  f"Handling task reminder for user_id: {user_id}, task_id: {task_id}"
  ```

- **Line 1963**: `task_id`
  ```
  f"Handling task reminder for user_id: {user_id}, task_id: {task_id}"
  ```

- **Line 1966**: `task_id`
  ```
  if not user_id or not task_id:
  ```

- **Line 1979**: `task_id`
  ```
  task = get_task_by_id(user_id, task_id)
  ```

- **Line 1981**: `task_id`
  ```
  logger.error(f"Task {task_id} not found for user {user_id}")
  ```

- **Line 1986**: `task_id`
  ```
  logger.debug(f"Task {task_id} is already completed, skipping reminder")
  ```

- **Line 2031**: `task_id`
  ```
  custom_view = get_task_reminder_view(user_id, task_id, task_title)
  ```

- **Line 2037**: `task_id`
  ```
  return get_task_reminder_view(user_id, task_id, task_title)
  ```

- **Line 2050**: `task_id`
  ```
  f"Task reminder sent successfully for user {user_id}, task {task_id}"
  ```

- **Line 2053**: `task_id`
  ```
  self._last_task_reminders[user_id] = task_id
  ```

- **Line 2056**: `task_id`
  ```
  f"Failed to send task reminder for user {user_id}, task {task_id}"
  ```

- **Line 2105**: `task_id`
  ```
  task.get("task_id", "")
  ```

### communication\message_processing\command_parser.py
**Issues Found**: 4

- **Line 1188**: `task_id`
  ```
  entities["task_identifier"] = value
  ```

- **Line 1231**: `task_id`
  ```
  entities["task_identifier"] = task_name or identifier
  ```

- **Line 1233**: `task_id`
  ```
  entities["task_identifier"] = identifier
  ```

- **Line 1818**: `task_id`
  ```
  entities["task_identifier"] = number_match.group(1)
  ```

### communication\message_processing\conversation_flow_manager.py
**Issues Found**: 48

- **Line 1361**: `task_id`
  ```
  task_id = user_state.get("data", {}).get("task_id")
  ```

- **Line 1361**: `task_id`
  ```
  task_id = user_state.get("data", {}).get("task_id")
  ```

- **Line 1362**: `task_id`
  ```
  if not task_id:
  ```

- **Line 1364**: `task_id`
  ```
  f"Task reminder follow-up for user {user_id} but no task_id in state"
  ```

- **Line 1424**: `task_id`
  ```
  user_id, task_id, message_text
  ```

- **Line 1427**: `task_id`
  ```
  f"Parsed reminder_periods for task {task_id}: {reminder_periods}"
  ```

- **Line 1433**: `task_id`
  ```
  task = get_task_by_id(user_id, task_id)
  ```

- **Line 1452**: `task_id`
  ```
  task = get_task_by_id(user_id, task_id)
  ```

- **Line 1455**: `task_id`
  ```
  f"Task {task_id} not found when trying to set reminder periods"
  ```

- **Line 1476**: `task_id`
  ```
  f"Task {task_id} has invalid due_date format '{due_date_str}', cannot set reminders"
  ```

- **Line 1489**: `task_id`
  ```
  f"Updating task {task_id} with reminder periods: {reminder_periods}"
  ```

- **Line 1496**: `task_id`
  ```
  user_id, task_id, {"reminder_periods": reminder_periods}
  ```

- **Line 1501**: `task_id`
  ```
  f"update_task returned False for task {task_id} with reminder periods for user {user_id}"
  ```

- **Line 1510**: `task_id`
  ```
  updated_task = get_task_by_id(user_id, task_id)
  ```

- **Line 1513**: `task_id`
  ```
  f"Task {task_id} was not updated with reminder_periods after update_task returned True"
  ```

- **Line 1536**: `task_id`
  ```
  f"Exception in update_task for task {task_id}: {update_error}",
  ```

- **Line 1562**: `task_id`
  ```
  if "task_id" in str(e).lower() or "not found" in str(e).lower():
  ```

- **Line 1581**: `task_id`
  ```
  self, user_id: str, task_id: str, text: str
  ```

- **Line 1595**: `task_id`
  ```
  due_datetime = self._get_task_due_datetime_for_reminders(user_id, task_id)
  ```

- **Line 1602**: `task_id`
  ```
  f"for task {task_id} with due_datetime {due_datetime}"
  ```

- **Line 1629**: `task_id`
  ```
  f"Parsed reminder period for task {task_id}: "
  ```

- **Line 1640**: `task_id`
  ```
  logger.debug(f"Final reminder_periods for task {task_id}: {reminder_periods}")
  ```

- **Line 1645**: `task_id`
  ```
  self, user_id: str, task_id: str
  ```

- **Line 1650**: `task_id`
  ```
  task = get_task_by_id(user_id, task_id)
  ```

- **Line 1652**: `task_id`
  ```
  logger.debug(f"Task {task_id} has no due_date, cannot parse reminder periods")
  ```

- **Line 1661**: `task_id`
  ```
  logger.debug(f"Parsed due datetime for task {task_id}: {due_datetime}")
  ```

- **Line 1667**: `task_id`
  ```
  f"Could not parse due date/time for task {task_id}: {due_date_str} {due_time_str}"
  ```

- **Line 1672**: `task_id`
  ```
  logger.debug(f"Parsed due date only for task {task_id}: {due_datetime}")
  ```

- **Line 1751**: `task_id`
  ```
  def start_task_due_date_flow(self, user_id: str, task_id: str) -> None:
  ```

- **Line 1759**: `task_id`
  ```
  "data": {"task_id": task_id},
  ```

- **Line 1759**: `task_id`
  ```
  "data": {"task_id": task_id},
  ```

- **Line 1763**: `task_id`
  ```
  logger.debug(f"Started task due date flow for user {user_id}, task {task_id}")
  ```

- **Line 1766**: `task_id`
  ```
  def start_task_reminder_followup(self, user_id: str, task_id: str) -> None:
  ```

- **Line 1774**: `task_id`
  ```
  "data": {"task_id": task_id},
  ```

- **Line 1774**: `task_id`
  ```
  "data": {"task_id": task_id},
  ```

- **Line 1779**: `task_id`
  ```
  f"Started task reminder follow-up flow for user {user_id}, task {task_id}"
  ```

- **Line 1786**: `task_id`
  ```
  self, user_id: str, task_id: str
  ```

- **Line 1797**: `task_id`
  ```
  task = get_task_by_id(user_id, task_id)
  ```

- **Line 1924**: `task_id`
  ```
  task_id = user_state.get("data", {}).get("task_id")
  ```

- **Line 1924**: `task_id`
  ```
  task_id = user_state.get("data", {}).get("task_id")
  ```

- **Line 1936**: `task_id`
  ```
  task_id = user_state.get("data", {}).get("task_id")
  ```

- **Line 1936**: `task_id`
  ```
  task_id = user_state.get("data", {}).get("task_id")
  ```

- **Line 1961**: `task_id`
  ```
  task_id = user_state.get("data", {}).get("task_id")
  ```

- **Line 1961**: `task_id`
  ```
  task_id = user_state.get("data", {}).get("task_id")
  ```

- **Line 1962**: `task_id`
  ```
  if not task_id:
  ```

- **Line 1987**: `task_id`
  ```
  update_result = update_task(user_id, task_id, update_data)
  ```

- **Line 1999**: `task_id`
  ```
  self.start_task_reminder_followup(user_id, task_id)
  ```

- **Line 2000**: `task_id`
  ```
  self._generate_context_aware_reminder_suggestions(user_id, task_id)
  ```

### communication\message_processing\interaction_manager.py
**Issues Found**: 9

- **Line 621**: `task_id`
  ```
  task_id = updated_user_state.get("data", {}).get("task_id")
  ```

- **Line 621**: `task_id`
  ```
  task_id = updated_user_state.get("data", {}).get("task_id")
  ```

- **Line 622**: `task_id`
  ```
  if task_id:
  ```

- **Line 624**: `task_id`
  ```
  user_id, task_id
  ```

- **Line 644**: `task_id`
  ```
  resp = handler._handle_delete_task(user_id, {"task_identifier": None})
  ```

- **Line 728**: `task_id`
  ```
  coerced_entities["task_identifier"] = ident
  ```

- **Line 749**: `task_id`
  ```
  if coerced_entities.get("task_identifier") and any(
  ```

- **Line 782**: `task_id`
  ```
  if "task_identifier" not in coerced_entities:
  ```

- **Line 791**: `task_id`
  ```
  coerced_entities["task_identifier"] = ident
  ```

### core\file_operations.py
**Issues Found**: 1

- **Line 667**: `completed_tasks`
  ```
  task_files = {"active_tasks": [], "completed_tasks": [], "task_schedules": {}}
  ```

### core\message_analytics.py
**Issues Found**: 1

- **Line 149**: `delivery_status`
  ```
  status = msg.get("delivery_status", "unknown")
  ```

### core\message_management.py
**Issues Found**: 43

- **Line 94**: `message_id`
  ```
  message_id = message.get("id") or message.get("message_id")
  ```

- **Line 94**: `message_id`
  ```
  message_id = message.get("id") or message.get("message_id")
  ```

- **Line 96**: `message_id`
  ```
  "id": message_id,
  ```

- **Line 97**: `message_id`
  ```
  "message_id": message_id,
  ```

- **Line 97**: `message_id`
  ```
  "message_id": message_id,
  ```

- **Line 117**: `delivery_status`
  ```
  if delivery.get("message") is not None or delivery.get("delivery_status") is not None or delivery.get("timestamp") is not None:
  ```

- **Line 119**: `message_id`
  ```
  message_id = delivery.get("message_template_id") or delivery.get("message_id")
  ```

- **Line 119**: `message_id`
  ```
  message_id = delivery.get("message_template_id") or delivery.get("message_id")
  ```

- **Line 121**: `delivery_status`
  ```
  status = delivery.get("status") or delivery.get("delivery_status", "")
  ```

- **Line 123**: `message_id`
  ```
  "message_template_id": message_id,
  ```

- **Line 124**: `message_id`
  ```
  "message_id": message_id,
  ```

- **Line 124**: `message_id`
  ```
  "message_id": message_id,
  ```

- **Line 131**: `delivery_status`
  ```
  "delivery_status": status,
  ```

- **Line 139**: `message_id`
  ```
  message_id = str(message.get("id") or message.get("message_id") or uuid.uuid4())
  ```

- **Line 139**: `message_id`
  ```
  message_id = str(message.get("id") or message.get("message_id") or uuid.uuid4())
  ```

- **Line 146**: `message_id`
  ```
  "id": message_id,
  ```

- **Line 161**: `message_id`
  ```
  template["metadata"].setdefault("short_id", message.get("short_id") or generate_short_id(message_id, "message"))
  ```

- **Line 364**: `message_id`
  ```
  def edit_message(user_id, category, message_id, updated_data):
  ```

- **Line 371**: `message_id`
  ```
  message_id: The ID of the message to edit
  ```

- **Line 395**: `message_id`
  ```
  if (msg.get("id") or msg.get("message_id")) == message_id
  ```

- **Line 395**: `message_id`
  ```
  if (msg.get("id") or msg.get("message_id")) == message_id
  ```

- **Line 420**: `message_id`
  ```
  f"Edited message with ID {message_id} in category {category} for user {user_id}."
  ```

- **Line 425**: `message_id`
  ```
  def update_message(user_id, category, message_id, new_message_data):
  ```

- **Line 427**: `message_id`
  ```
  Update a message by its message_id.
  ```

- **Line 432**: `message_id`
  ```
  message_id: The ID of the message to update
  ```

- **Line 451**: `message_id`
  ```
  if (msg.get("id") or msg.get("message_id")) == message_id:
  ```

- **Line 451**: `message_id`
  ```
  if (msg.get("id") or msg.get("message_id")) == message_id:
  ```

- **Line 454**: `message_id`
  ```
  normalized_new_data["id"] = message_id
  ```

- **Line 459**: `message_id`
  ```
  f"Updated message with ID {message_id} in category {category} for user {user_id}"
  ```

- **Line 467**: `message_id`
  ```
  def delete_message(user_id, category, message_id):
  ```

- **Line 474**: `message_id`
  ```
  message_id: The ID of the message to delete
  ```

- **Line 495**: `message_id`
  ```
  (msg for msg in data["messages"] if (msg.get("id") or msg.get("message_id")) == message_id), None
  ```

- **Line 495**: `message_id`
  ```
  (msg for msg in data["messages"] if (msg.get("id") or msg.get("message_id")) == message_id), None
  ```

- **Line 521**: `message_id`
  ```
  f"Deleted message with ID {message_id} in category {category} for user {user_id}."
  ```

- **Line 577**: `message_id`
  ```
  msg.get("message_id"): msg.get("category")
  ```

- **Line 579**: `message_id`
  ```
  if isinstance(msg, dict) and msg.get("message_id")
  ```

- **Line 583**: `message_id`
  ```
  category_value = id_to_category.get(message.get("message_id"))
  ```

- **Line 643**: `message_id`
  ```
  message_id: str,
  ```

- **Line 645**: `delivery_status`
  ```
  delivery_status: str = "sent",
  ```

- **Line 657**: `message_id`
  ```
  message_id: The message ID
  ```

- **Line 659**: `delivery_status`
  ```
  delivery_status: Delivery status (default: "sent")
  ```

- **Line 677**: `message_id`
  ```
  "message_template_id": message_id,
  ```

- **Line 681**: `delivery_status`
  ```
  "status": delivery_status,
  ```

### core\scheduler.py
**Issues Found**: 54

- **Line 1069**: `task_id`
  ```
  def handle_task_reminder(self, user_id, task_id, retry_attempts=3, retry_delay=30):
  ```

- **Line 1084**: `task_id`
  ```
  task = get_task_by_id(user_id, task_id)
  ```

- **Line 1086**: `task_id`
  ```
  logger.error(f"Task {task_id} not found for user {user_id}")
  ```

- **Line 1092**: `task_id`
  ```
  f"Task {task_id} is already completed, skipping reminder"
  ```

- **Line 1097**: `task_id`
  ```
  self.communication_manager.handle_task_reminder(user_id, task_id)
  ```

- **Line 1100**: `task_id`
  ```
  update_task(user_id, task_id, {"reminder_sent": True})
  ```

- **Line 1103**: `task_id`
  ```
  f"Task reminder sent successfully for user {user_id}, task {task_id}"
  ```

- **Line 1109**: `task_id`
  ```
  f"Error sending task reminder for user {user_id}, task {task_id}: {e}"
  ```

- **Line 1391**: `task_id`
  ```
  user_id, selected_task["task_id"], random_time
  ```

- **Line 1504**: `task_id`
  ```
  str(task.get("task_id") or "").strip(),
  ```

- **Line 1643**: `task_id`
  ```
  def schedule_task_reminder_at_time(self, user_id, task_id, reminder_time):
  ```

- **Line 1651**: `task_id`
  ```
  task = get_task_by_id(user_id, task_id)
  ```

- **Line 1653**: `task_id`
  ```
  logger.error(f"Task {task_id} not found for user {user_id}")
  ```

- **Line 1658**: `task_id`
  ```
  f"Task {task_id} is already completed, skipping reminder scheduling"
  ```

- **Line 1672**: `task_id`
  ```
  self.handle_task_reminder, user_id=user_id, task_id=task_id
  ```

- **Line 1672**: `task_id`
  ```
  self.handle_task_reminder, user_id=user_id, task_id=task_id
  ```

- **Line 1699**: `task_id`
  ```
  f"Scheduled daily task reminder for user {user_id}, task {task_id} at {time_str}"
  ```

- **Line 1705**: `task_id`
  ```
  f"Error scheduling task reminder for user {user_id}, task {task_id}: {e}"
  ```

- **Line 1710**: `task_id`
  ```
  def schedule_task_reminder_at_datetime(self, user_id, task_id, date_str, time_str):
  ```

- **Line 1718**: `task_id`
  ```
  task = get_task_by_id(user_id, task_id)
  ```

- **Line 1720**: `task_id`
  ```
  logger.error(f"Task {task_id} not found for user {user_id}")
  ```

- **Line 1725**: `task_id`
  ```
  f"Task {task_id} is already completed, skipping reminder scheduling"
  ```

- **Line 1748**: `task_id`
  ```
  self.handle_task_reminder, user_id=user_id, task_id=task_id
  ```

- **Line 1748**: `task_id`
  ```
  self.handle_task_reminder, user_id=user_id, task_id=task_id
  ```

- **Line 1752**: `task_id`
  ```
  f"Scheduled one-time task reminder for user {user_id}, task {task_id} at {reminder_datetime}"
  ```

- **Line 1758**: `task_id`
  ```
  f"Error scheduling task reminder for user {user_id}, task {task_id}: {e}"
  ```

- **Line 1763**: `task_id`
  ```
  def cleanup_task_reminders(self, user_id, task_id):
  ```

- **Line 1767**: `task_id`
  ```
  Finds and removes all APScheduler jobs that call handle_task_reminder for the given task_id.
  ```

- **Line 1772**: `task_id`
  ```
  task_id: The task ID to clean up reminders for
  ```

- **Line 1778**: `task_id`
  ```
  if not user_id or not task_id:
  ```

- **Line 1780**: `task_id`
  ```
  f"Invalid parameters for cleanup_task_reminders: user_id={user_id}, task_id={task_id}"
  ```

- **Line 1780**: `task_id`
  ```
  f"Invalid parameters for cleanup_task_reminders: user_id={user_id}, task_id={task_id}"
  ```

- **Line 1788**: `task_id`
  ```
  # Find all jobs that call handle_task_reminder with this user_id and task_id
  ```

- **Line 1792**: `task_id`
  ```
  # Jobs created by schedule_task_reminder_at_datetime use: schedule.every(delay).seconds.do(handle_task_reminder, user_id=..., task_id=...)
  ```

- **Line 1793**: `task_id`
  ```
  # Jobs created by schedule_task_reminder_at_time use: schedule.every().day.at(time).do(handle_task_reminder, user_id=..., task_id=...)
  ```

- **Line 1803**: `task_id`
  ```
  # Check keyword arguments for user_id and task_id
  ```

- **Line 1808**: `task_id`
  ```
  and kwargs.get("task_id") == task_id
  ```

- **Line 1808**: `task_id`
  ```
  and kwargs.get("task_id") == task_id
  ```

- **Line 1812**: `task_id`
  ```
  f"Found reminder job for task {task_id}, user {user_id}"
  ```

- **Line 1819**: `task_id`
  ```
  # handle_task_reminder signature: (self, user_id, task_id, ...)
  ```

- **Line 1823**: `task_id`
  ```
  and args[1] == task_id
  ```

- **Line 1832**: `task_id`
  ```
  f"Found reminder job for task {task_id}, user {user_id} (positional args)"
  ```

- **Line 1847**: `task_id`
  ```
  f"Removed reminder job for task {task_id}, user {user_id}"
  ```

- **Line 1855**: `task_id`
  ```
  f"Cleaned up {jobs_removed} reminder job(s) for task {task_id}, user {user_id} "
  ```

- **Line 1863**: `task_id`
  ```
  f"Error cleaning up task reminders for task {task_id}, user {user_id}: {e}"
  ```

- **Line 1901**: `task_id`
  ```
  task_id = kwargs.get("task_id")
  ```

- **Line 1901**: `task_id`
  ```
  task_id = kwargs.get("task_id")
  ```

- **Line 1902**: `task_id`
  ```
  if user_id and task_id:
  ```

- **Line 1903**: `task_id`
  ```
  jobs_to_check.append((job, user_id, task_id))
  ```

- **Line 1912**: `task_id`
  ```
  for job, user_id, task_id in jobs_to_check:
  ```

- **Line 1914**: `task_id`
  ```
  task = get_task_by_id(user_id, task_id)
  ```

- **Line 1921**: `task_id`
  ```
  f"Removed orphaned reminder for non-existent task {task_id}, user {user_id}"
  ```

- **Line 1932**: `task_id`
  ```
  f"Removed reminder for completed task {task_id}, user {user_id}"
  ```

- **Line 1939**: `task_id`
  ```
  f"Error checking task {task_id} for user {user_id}: {e}"
  ```

### core\schemas.py
**Issues Found**: 1

- **Line 430**: `message_id`
  ```
  message_id: str
  ```

### core\service.py
**Issues Found**: 5

- **Line 1024**: `task_id`
  ```
  task_id = request_data.get("task_id")
  ```

- **Line 1024**: `task_id`
  ```
  task_id = request_data.get("task_id")
  ```

- **Line 1025**: `task_id`
  ```
  if user_id and task_id and self.communication_manager:
  ```

- **Line 1027**: `task_id`
  ```
  user_id, task_id
  ```

- **Line 1030**: `task_id`
  ```
  f"Task reminder sent successfully for {user_id}, task {task_id}"
  ```

### core\user_data_read.py
**Issues Found**: 4

- **Line 51**: `message_id`
  ```
  if "message_id" not in message or message["message_id"] in existing_ids:
  ```

- **Line 51**: `message_id`
  ```
  if "message_id" not in message or message["message_id"] in existing_ids:
  ```

- **Line 52**: `message_id`
  ```
  message["message_id"] = str(uuid.uuid4())
  ```

- **Line 53**: `message_id`
  ```
  existing_ids.add(message["message_id"])
  ```

### core\user_data_v2.py
**Issues Found**: 4

- **Line 29**: `task_id`
  ```
  "task_id",
  ```

- **Line 45**: `message_id`
  ```
  "message": {"message_id", "message", "days", "time_periods", "timestamp"},
  ```

- **Line 46**: `message_id`
  ```
  "delivery": {"message_id", "message", "delivery_status", "timestamp"},
  ```

- **Line 46**: `delivery_status`
  ```
  "delivery": {"message_id", "message", "delivery_status", "timestamp"},
  ```

### core\user_item_storage.py
**Issues Found**: 2

- **Line 53**: `active_tasks.json`
  ```
  Files are created only if missing (e.g. {"active_tasks.json": {"tasks": []}}).
  ```

- **Line 85**: `active_tasks.json`
  ```
  filename: JSON filename (e.g. 'entries.json', 'active_tasks.json').
  ```

### development_tools\imports\analyze_unused_imports.py
**Issues Found**: 2

- **Line 318**: `message_id`
  ```
  message_id = issue.get("message-id")
  ```

- **Line 319**: `message_id`
  ```
  if message_id != "W0611":
  ```

### tasks\__init__.py
**Issues Found**: 4

- **Line 15**: `completed_tasks`
  ```
  load_completed_tasks,
  ```

- **Line 16**: `completed_tasks`
  ```
  save_completed_tasks,
  ```

- **Line 57**: `completed_tasks`
  ```
  "load_completed_tasks",
  ```

- **Line 61**: `completed_tasks`
  ```
  "save_completed_tasks",
  ```

### tasks\task_data_handlers.py
**Issues Found**: 14

- **Line 100**: `completed_tasks`
  ```
  completed_tasks = [task for task in v2_tasks if task.get("status") == "completed"]
  ```

- **Line 102**: `completed_tasks`
  ```
  return _save_v2_tasks(user_id, active_v2 + completed_tasks)
  ```

- **Line 106**: `completed_tasks`
  ```
  def load_completed_tasks(user_id: str) -> list[dict[str, Any]]:
  ```

- **Line 114**: `completed_tasks`
  ```
  logger.error(f"Invalid user_id for load_completed_tasks: {user_id}")
  ```

- **Line 122**: `completed_tasks`
  ```
  def save_completed_tasks(user_id: str, tasks: list[dict[str, Any]]) -> bool:
  ```

- **Line 125**: `completed_tasks`
  ```
  logger.error(f"Invalid user_id for save_completed_tasks: {user_id}")
  ```

- **Line 174**: `task_id`
  ```
  task_id = str(task.get("id") or task.get("task_id") or "")
  ```

- **Line 174**: `task_id`
  ```
  task_id = str(task.get("id") or task.get("task_id") or "")
  ```

- **Line 175**: `task_id`
  ```
  if not task_id:
  ```

- **Line 176**: `task_id`
  ```
  task_id = generate_short_id(now_timestamp_full(), "task", length=12)
  ```

- **Line 196**: `task_id`
  ```
  "id": task_id,
  ```

- **Line 197**: `task_id`
  ```
  "short_id": task.get("short_id") or generate_short_id(task_id, "task"),
  ```

- **Line 242**: `task_id`
  ```
  "task_id": task.get("id"),
  ```

- **Line 299**: `task_id`
  ```
  "task_id",
  ```

### tasks\task_data_manager.py
**Issues Found**: 87

- **Line 26**: `completed_tasks`
  ```
  load_completed_tasks,
  ```

- **Line 27**: `completed_tasks`
  ```
  save_completed_tasks,
  ```

- **Line 35**: `task_id`
  ```
  def _task_id(task: dict[str, Any]) -> str:
  ```

- **Line 40**: `task_id`
  ```
  if task.get("task_id"):
  ```

- **Line 41**: `task_id`
  ```
  logger.warning("LEGACY COMPATIBILITY: task runtime fallback used for task_id key.")
  ```

- **Line 42**: `task_id`
  ```
  return str(task.get("task_id"))
  ```

- **Line 156**: `task_id`
  ```
  task_id = str(uuid.uuid4())
  ```

- **Line 158**: `task_id`
  ```
  "id": task_id,
  ```

- **Line 183**: `task_id`
  ```
  logger.info(f"Created task '{title}' for user {user_id} with ID {task_id}")
  ```

- **Line 185**: `task_id`
  ```
  schedule_task_reminders(user_id, task_id, reminder_periods)
  ```

- **Line 186**: `task_id`
  ```
  return task_id
  ```

- **Line 190**: `task_id`
  ```
  def update_task(user_id: str, task_id: str, updates: dict[str, Any]) -> bool:
  ```

- **Line 192**: `task_id`
  ```
  if not user_id or not task_id:
  ```

- **Line 197**: `task_id`
  ```
  if _task_id(task) == task_id:
  ```

- **Line 197**: `task_id`
  ```
  if _task_id(task) == task_id:
  ```

- **Line 203**: `task_id`
  ```
  logger.warning(f"Task {task_id}: {reason}")
  ```

- **Line 212**: `task_id`
  ```
  logger.info(f"Updated task {task_id} for user {user_id} | Fields: {', '.join(updated_fields)}")
  ```

- **Line 214**: `task_id`
  ```
  cleanup_task_reminders(user_id, task_id)
  ```

- **Line 218**: `task_id`
  ```
  schedule_task_reminders(user_id, task_id, new_reminder_periods)
  ```

- **Line 221**: `task_id`
  ```
  f"Failed to schedule reminders for task {task_id}, but task was updated: {schedule_error}"
  ```

- **Line 224**: `task_id`
  ```
  logger.warning(f"Task {task_id} not found for user {user_id}")
  ```

- **Line 230**: `task_id`
  ```
  user_id: str, task_id: str, completion_data: dict[str, Any] | None = None
  ```

- **Line 233**: `task_id`
  ```
  if not user_id or not task_id:
  ```

- **Line 240**: `task_id`
  ```
  if _task_id(task) == task_id:
  ```

- **Line 240**: `task_id`
  ```
  if _task_id(task) == task_id:
  ```

- **Line 269**: `task_id`
  ```
  logger.warning(f"Task {task_id} not found for user {user_id}")
  ```

- **Line 272**: `completed_tasks`
  ```
  completed_tasks = load_completed_tasks(user_id)
  ```

- **Line 272**: `completed_tasks`
  ```
  completed_tasks = load_completed_tasks(user_id)
  ```

- **Line 273**: `completed_tasks`
  ```
  completed_tasks.append(task_to_complete)
  ```

- **Line 274**: `completed_tasks`
  ```
  if not (save_active_tasks(user_id, updated_active_tasks) and save_completed_tasks(user_id, completed_tasks)):
  ```

- **Line 274**: `completed_tasks`
  ```
  if not (save_active_tasks(user_id, updated_active_tasks) and save_completed_tasks(user_id, completed_tasks)):
  ```

- **Line 280**: `task_id`
  ```
  logger.info(f"Completed task '{task_title}' (ID: {task_id}) for user {user_id} at {completion_time_str}")
  ```

- **Line 281**: `task_id`
  ```
  cleanup_task_reminders(user_id, task_id)
  ```

- **Line 284**: `task_id`
  ```
  logger.info(f"Created next recurring task instance for task '{task_title}' (ID: {task_id})")
  ```

- **Line 289**: `task_id`
  ```
  def restore_task(user_id: str, task_id: str) -> bool:
  ```

- **Line 291**: `task_id`
  ```
  if not user_id or not task_id:
  ```

- **Line 294**: `completed_tasks`
  ```
  completed_tasks = load_completed_tasks(user_id)
  ```

- **Line 294**: `completed_tasks`
  ```
  completed_tasks = load_completed_tasks(user_id)
  ```

- **Line 296**: `completed_tasks`
  ```
  updated_completed_tasks = []
  ```

- **Line 297**: `completed_tasks`
  ```
  for task in completed_tasks:
  ```

- **Line 298**: `task_id`
  ```
  if _task_id(task) == task_id:
  ```

- **Line 298**: `task_id`
  ```
  if _task_id(task) == task_id:
  ```

- **Line 303**: `completed_tasks`
  ```
  updated_completed_tasks.append(task)
  ```

- **Line 305**: `task_id`
  ```
  logger.warning(f"Completed task {task_id} not found for user {user_id}")
  ```

- **Line 309**: `completed_tasks`
  ```
  if not (save_completed_tasks(user_id, updated_completed_tasks) and save_active_tasks(user_id, active_tasks)):
  ```

- **Line 309**: `completed_tasks`
  ```
  if not (save_completed_tasks(user_id, updated_completed_tasks) and save_active_tasks(user_id, active_tasks)):
  ```

- **Line 312**: `task_id`
  ```
  logger.info(f"Restored task {task_id} for user {user_id}")
  ```

- **Line 315**: `task_id`
  ```
  schedule_task_reminders(user_id, task_id, reminder_periods)
  ```

- **Line 320**: `task_id`
  ```
  def delete_task(user_id: str, task_id: str) -> bool:
  ```

- **Line 322**: `task_id`
  ```
  if not user_id or not task_id:
  ```

- **Line 328**: `task_id`
  ```
  if _task_id(task) == task_id:
  ```

- **Line 328**: `task_id`
  ```
  if _task_id(task) == task_id:
  ```

- **Line 332**: `task_id`
  ```
  tasks = [t for t in tasks if _task_id(t) != task_id]
  ```

- **Line 332**: `task_id`
  ```
  tasks = [t for t in tasks if _task_id(t) != task_id]
  ```

- **Line 334**: `task_id`
  ```
  logger.warning(f"Task {task_id} not found for deletion for user {user_id}")
  ```

- **Line 340**: `task_id`
  ```
  logger.info(f"Deleted task '{task_title}' (ID: {task_id}) for user {user_id}")
  ```

- **Line 341**: `task_id`
  ```
  cleanup_task_reminders(user_id, task_id)
  ```

- **Line 346**: `task_id`
  ```
  def get_task_by_id(user_id: str, task_id: str) -> dict[str, Any] | None:
  ```

- **Line 348**: `task_id`
  ```
  if not user_id or not task_id:
  ```

- **Line 352**: `task_id`
  ```
  if _task_id(task) == task_id:
  ```

- **Line 352**: `task_id`
  ```
  if _task_id(task) == task_id:
  ```

- **Line 354**: `completed_tasks`
  ```
  for task in load_completed_tasks(user_id):
  ```

- **Line 355**: `task_id`
  ```
  if _task_id(task) == task_id:
  ```

- **Line 355**: `task_id`
  ```
  if _task_id(task) == task_id:
  ```

- **Line 357**: `task_id`
  ```
  logger.debug(f"Task {task_id} not found for user {user_id}")
  ```

- **Line 376**: `task_id`
  ```
  logger.warning(f"Invalid due date format for task {_task_id(task)}")
  ```

- **Line 397**: `task_id`
  ```
  user_id: str, task_id: str, reminder_periods: list[dict[str, Any]]
  ```

- **Line 400**: `task_id`
  ```
  if not user_id or not task_id or not reminder_periods:
  ```

- **Line 401**: `task_id`
  ```
  logger.debug(f"No reminder periods to schedule for task {task_id}")
  ```

- **Line 414**: `task_id`
  ```
  logger.warning(f"Incomplete reminder period data for task {task_id}: {period}")
  ```

- **Line 416**: `task_id`
  ```
  if scheduler_manager.schedule_task_reminder_at_datetime(user_id, task_id, date, start_time):
  ```

- **Line 418**: `task_id`
  ```
  logger.info(f"Scheduled reminder for task {task_id} at {date} {start_time}")
  ```

- **Line 420**: `task_id`
  ```
  logger.warning(f"Failed to schedule reminder for task {task_id} at {date} {start_time}")
  ```

- **Line 421**: `task_id`
  ```
  logger.info(f"Scheduled {scheduled_count} reminders for task {task_id}")
  ```

- **Line 426**: `task_id`
  ```
  def cleanup_task_reminders(user_id: str, task_id: str) -> bool:
  ```

- **Line 431**: `task_id`
  ```
  logger.warning(f"Scheduler manager not available for cleaning up task reminders for task {task_id}, user {user_id}")
  ```

- **Line 433**: `task_id`
  ```
  result = scheduler_manager.cleanup_task_reminders(user_id, task_id)
  ```

- **Line 435**: `task_id`
  ```
  logger.info(f"Successfully cleaned up reminders for task {task_id}, user {user_id}")
  ```

- **Line 437**: `task_id`
  ```
  logger.warning(f"Failed to clean up reminders for task {task_id}, user {user_id} - cleanup returned False")
  ```

- **Line 483**: `completed_tasks`
  ```
  completed_tasks = load_completed_tasks(user_id)
  ```

- **Line 483**: `completed_tasks`
  ```
  completed_tasks = load_completed_tasks(user_id)
  ```

- **Line 486**: `completed_tasks`
  ```
  "completed_count": len(completed_tasks),
  ```

- **Line 487**: `completed_tasks`
  ```
  "total_count": len(active_tasks) + len(completed_tasks),
  ```

- **Line 512**: `task_id`
  ```
  logger.warning(f"Could not parse completion date '{completion_date_str}' for recurring task {_task_id(completed_task)}")
  ```

- **Line 519**: `task_id`
  ```
  logger.warning(f"Could not calculate next due date for recurring task {_task_id(completed_task)}")
  ```

- **Line 551**: `task_id`
  ```
  logger.info(f"Created next recurring task instance for task {_task_id(completed_task)} with due date {next_due_date_str}")
  ```

- **Line 553**: `task_id`
  ```
  schedule_task_reminders(user_id, _task_id(next_task), next_task["reminder_periods"])
  ```

### tasks\task_schemas.py
**Issues Found**: 4

- **Line 35**: `active_tasks.json`
  ```
  ACTIVE_TASKS_FILENAME = "active_tasks.json"
  ```

- **Line 36**: `completed_tasks.json`
  ```
  COMPLETED_TASKS_FILENAME = "completed_tasks.json"
  ```

- **Line 36**: `completed_tasks`
  ```
  COMPLETED_TASKS_FILENAME = "completed_tasks.json"
  ```

- **Line 37**: `task_schedules.json`
  ```
  TASK_SCHEDULES_FILENAME = "task_schedules.json"
  ```

### tests\ai\test_context_includes_recent_messages.py
**Issues Found**: 6

- **Line 34**: `message_id`
  ```
  message_id="m1",
  ```

- **Line 36**: `delivery_status`
  ```
  delivery_status="sent",
  ```

- **Line 45**: `message_id`
  ```
  message_id="c1",
  ```

- **Line 47**: `delivery_status`
  ```
  delivery_status="sent",
  ```

- **Line 92**: `message_id`
  ```
  message_id="t1",
  ```

- **Line 94**: `delivery_status`
  ```
  delivery_status="sent",
  ```

### tests\behavior\test_analytics_handler_behavior.py
**Issues Found**: 1

- **Line 554**: `completed_tasks`
  ```
  @patch('tasks.load_completed_tasks')
  ```

### tests\behavior\test_communication_manager_coverage_expansion.py
**Issues Found**: 3

- **Line 798**: `task_id`
  ```
  task_id = "test_task_123"
  ```

- **Line 799**: `task_id`
  ```
  comm_manager._last_task_reminders[user_id] = task_id
  ```

- **Line 805**: `task_id`
  ```
  assert last_reminder == task_id, "Should return last task reminder"
  ```

### tests\behavior\test_conversation_flow_manager_behavior.py
**Issues Found**: 1

- **Line 705**: `task_id`
  ```
  "data": {"task_id": "task-1"},
  ```

### tests\behavior\test_core_message_management_coverage_expansion.py
**Issues Found**: 2

- **Line 102**: `message_id`
  ```
  {"message_id": "a", "timestamp": "2023-02-03T04:05:06Z"},
  ```

- **Line 103**: `message_id`
  ```
  {"message_id": "b", "timestamp": "2023-02-03 04:05:06"},
  ```

### tests\behavior\test_discord_bot_behavior.py
**Issues Found**: 1

- **Line 568**: `task_id`
  ```
  assert not any(t.get("task_id") == t_id for t in tasks)
  ```

### tests\behavior\test_email_bot_behavior.py
**Issues Found**: 2

- **Line 257**: `message_id`
  ```
  assert 'message_id' in messages[0], "Should have message_id field if messages exist"
  ```

- **Line 257**: `message_id`
  ```
  assert 'message_id' in messages[0], "Should have message_id field if messages exist"
  ```

### tests\behavior\test_enhanced_command_parser_behavior.py
**Issues Found**: 4

- **Line 178**: `task_id`
  ```
  assert "task_identifier" in result.parsed_command.entities, "Should extract task identifier"
  ```

- **Line 179**: `task_id`
  ```
  assert result.parsed_command.entities["task_identifier"] == "123", "Should extract correct task identifier"
  ```

- **Line 184**: `task_id`
  ```
  assert "task_identifier" in result.parsed_command.entities, "Should extract task identifier"
  ```

- **Line 185**: `task_id`
  ```
  assert result.parsed_command.entities["task_identifier"] == "456", "Should extract correct task identifier"
  ```

### tests\behavior\test_interaction_handlers_behavior.py
**Issues Found**: 9

- **Line 286**: `task_id`
  ```
  task_id = create_task(actual_user_id, "Task to complete", "2025-08-02")
  ```

- **Line 287**: `task_id`
  ```
  assert task_id is not None, "Task creation should succeed"
  ```

- **Line 291**: `task_id`
  ```
  assert any(task.get('task_id') == task_id for task in tasks), "Task should exist before completion"
  ```

- **Line 291**: `task_id`
  ```
  assert any(task.get('task_id') == task_id for task in tasks), "Task should exist before completion"
  ```

- **Line 296**: `task_id`
  ```
  entities={"task_identifier": str(task_id)},
  ```

- **Line 296**: `task_id`
  ```
  entities={"task_identifier": str(task_id)},
  ```

- **Line 298**: `task_id`
  ```
  original_message=f"complete task {task_id}"
  ```

- **Line 310**: `task_id`
  ```
  assert not any(task.get('task_id') == task_id for task in tasks), "Task should be removed from active tasks"
  ```

- **Line 310**: `task_id`
  ```
  assert not any(task.get('task_id') == task_id for task in tasks), "Task should be removed from active tasks"
  ```

### tests\behavior\test_interaction_handlers_coverage_expansion.py
**Issues Found**: 13

- **Line 315**: `task_id`
  ```
  entities={"task_identifier": "1"},
  ```

- **Line 358**: `task_id`
  ```
  entities={"task_identifier": "999"},
  ```

- **Line 380**: `task_id`
  ```
  entities={"task_identifier": "1"},
  ```

- **Line 427**: `task_id`
  ```
  "task_identifier": "1",
  ```

- **Line 458**: `task_id`
  ```
  entities={"task_identifier": "1"},
  ```

- **Line 1232**: `task_id`
  ```
  def test_handle_edit_task_with_invalid_task_id(self, test_data_dir):
  ```

- **Line 1241**: `task_id`
  ```
  entities={"task_id": "invalid_task_id", "title": "New Title"},
  ```

- **Line 1241**: `task_id`
  ```
  entities={"task_id": "invalid_task_id", "title": "New Title"},
  ```

- **Line 1243**: `task_id`
  ```
  original_message="edit task invalid_task_id",
  ```

- **Line 1255**: `task_id`
  ```
  def test_handle_delete_task_with_invalid_task_id(self, test_data_dir):
  ```

- **Line 1264**: `task_id`
  ```
  entities={"task_id": "invalid_task_id"},
  ```

- **Line 1264**: `task_id`
  ```
  entities={"task_id": "invalid_task_id"},
  ```

- **Line 1266**: `task_id`
  ```
  original_message="delete task invalid_task_id",
  ```

### tests\behavior\test_message_analytics_behavior.py
**Issues Found**: 6

- **Line 64**: `message_id`
  ```
  "message_id": f"msg-{i}",
  ```

- **Line 68**: `delivery_status`
  ```
  "delivery_status": "sent",
  ```

- **Line 167**: `message_id`
  ```
  "message_id": f"msg-{i}",
  ```

- **Line 171**: `delivery_status`
  ```
  "delivery_status": status,
  ```

- **Line 235**: `message_id`
  ```
  "message_id": f"msg-{i}",
  ```

- **Line 239**: `delivery_status`
  ```
  "delivery_status": "sent",
  ```

### tests\behavior\test_message_behavior.py
**Issues Found**: 45

- **Line 89**: `message_id`
  ```
  'message_id': 'motivational_001'
  ```

- **Line 95**: `message_id`
  ```
  'message_id': 'motivational_002'
  ```

- **Line 217**: `message_id`
  ```
  message_id = "test-msg-1"
  ```

- **Line 234**: `message_id`
  ```
  "message_id": "test-msg-1",
  ```

- **Line 251**: `message_id`
  ```
  result = edit_message(user_id, category, message_id, updated_data)
  ```

- **Line 282**: `message_id`
  ```
  message_id = "nonexistent"
  ```

- **Line 288**: `message_id`
  ```
  "message_id": "test-msg-1",
  ```

- **Line 299**: `message_id`
  ```
  result = edit_message(user_id, category, message_id, updated_data)
  ```

- **Line 311**: `message_id`
  ```
  message_id = "test-msg-1"
  ```

- **Line 320**: `message_id`
  ```
  "message_id": "test-msg-1",
  ```

- **Line 334**: `message_id`
  ```
  result = update_message(user_id, category, message_id, updates)
  ```

- **Line 348**: `message_id`
  ```
  message_id = "test-msg-1"
  ```

- **Line 360**: `message_id`
  ```
  "message_id": "test-msg-1",
  ```

- **Line 366**: `message_id`
  ```
  "message_id": "test-msg-2",
  ```

- **Line 379**: `message_id`
  ```
  result = delete_message(user_id, category, message_id)
  ```

- **Line 403**: `message_id`
  ```
  message_id = "nonexistent"
  ```

- **Line 408**: `message_id`
  ```
  "message_id": "test-msg-1",
  ```

- **Line 419**: `message_id`
  ```
  result = delete_message(user_id, category, message_id)
  ```

- **Line 437**: `message_id`
  ```
  message_id = "test_msg"
  ```

- **Line 447**: `message_id`
  ```
  result = store_sent_message(user_id, category, message_id, message)
  ```

- **Line 473**: `message_id`
  ```
  {"message_id": "msg1", "message": "Test message 1", "category": category, "timestamp": "2025-01-01 10:00:00", "delivery_status": "sent"},
  ```

- **Line 473**: `delivery_status`
  ```
  {"message_id": "msg1", "message": "Test message 1", "category": category, "timestamp": "2025-01-01 10:00:00", "delivery_status": "sent"},
  ```

- **Line 474**: `message_id`
  ```
  {"message_id": "msg2", "message": "Test message 2", "category": category, "timestamp": "2025-01-01 11:00:00", "delivery_status": "sent"},
  ```

- **Line 474**: `delivery_status`
  ```
  {"message_id": "msg2", "message": "Test message 2", "category": category, "timestamp": "2025-01-01 11:00:00", "delivery_status": "sent"},
  ```

- **Line 475**: `message_id`
  ```
  {"message_id": "msg3", "message": "Test message 3", "category": category, "timestamp": "2025-01-01 12:00:00", "delivery_status": "sent"}
  ```

- **Line 475**: `delivery_status`
  ```
  {"message_id": "msg3", "message": "Test message 3", "category": category, "timestamp": "2025-01-01 12:00:00", "delivery_status": "sent"}
  ```

- **Line 487**: `message_id`
  ```
  assert messages[0]['message_id'] == 'msg3'
  ```

- **Line 488**: `message_id`
  ```
  assert messages[1]['message_id'] == 'msg2'
  ```

- **Line 489**: `message_id`
  ```
  assert messages[2]['message_id'] == 'msg1'
  ```

- **Line 523**: `message_id`
  ```
  "message_id": "msg-good",
  ```

- **Line 531**: `message_id`
  ```
  # Missing message_id should be dropped by normalization
  ```

- **Line 545**: `message_id`
  ```
  assert messages[0]['message_id'] == 'msg-good'
  ```

- **Line 563**: `message_id`
  ```
  {"message_id": "default1", "message": "Default message 1", "days": ["monday"], "time_periods": ["morning"]},
  ```

- **Line 564**: `message_id`
  ```
  {"message_id": "default2", "message": "Default message 2", "days": ["tuesday"], "time_periods": ["evening"]}
  ```

- **Line 612**: `message_id`
  ```
  message_data = {"message_id": "test_msg", "message": "Test message", "days": ["monday"], "time_periods": ["morning"]}
  ```

- **Line 628**: `message_id`
  ```
  message_id = "test_msg"
  ```

- **Line 629**: `message_id`
  ```
  updated_data = {"message_id": "test_msg", "message": "Updated message", "days": ["monday"], "time_periods": ["morning"]}
  ```

- **Line 635**: `message_id`
  ```
  result = edit_message(user_id, category, message_id, updated_data)
  ```

- **Line 645**: `message_id`
  ```
  message_id = "test_msg"
  ```

- **Line 651**: `message_id`
  ```
  result = delete_message(user_id, category, message_id)
  ```

- **Line 661**: `message_id`
  ```
  message_id = "test_msg"
  ```

- **Line 668**: `message_id`
  ```
  result = store_sent_message(user_id, category, message_id, message)
  ```

- **Line 735**: `message_id`
  ```
  message_id = data['messages'][0]['id']
  ```

- **Line 738**: `message_id`
  ```
  result2 = edit_message(user_id, category, message_id, updated_message)
  ```

- **Line 750**: `message_id`
  ```
  result3 = delete_message(user_id, category, message_id)
  ```

### tests\behavior\test_scheduler_coverage_expansion.py
**Issues Found**: 29

- **Line 424**: `task_id`
  ```
  "task_id": "task-1",
  ```

- **Line 429**: `task_id`
  ```
  "task_id": "task-2",
  ```

- **Line 490**: `task_id`
  ```
  task_id = "task-1"
  ```

- **Line 495**: `task_id`
  ```
  "task_id": task_id,
  ```

- **Line 495**: `task_id`
  ```
  "task_id": task_id,
  ```

- **Line 504**: `task_id`
  ```
  user_id, task_id, reminder_time
  ```

- **Line 509**: `task_id`
  ```
  mock_get_task.assert_called_once_with(user_id, task_id)
  ```

- **Line 518**: `task_id`
  ```
  task_id = "task-1"
  ```

- **Line 523**: `task_id`
  ```
  "task_id": task_id,
  ```

- **Line 523**: `task_id`
  ```
  "task_id": task_id,
  ```

- **Line 530**: `task_id`
  ```
  user_id, task_id, reminder_time
  ```

- **Line 535**: `task_id`
  ```
  mock_get_task.assert_called_once_with(user_id, task_id)
  ```

- **Line 796**: `task_id`
  ```
  task_id = "task-1"
  ```

- **Line 800**: `task_id`
  ```
  "task_id": task_id,
  ```

- **Line 800**: `task_id`
  ```
  "task_id": task_id,
  ```

- **Line 807**: `task_id`
  ```
  scheduler_manager.handle_task_reminder(user_id, task_id)
  ```

- **Line 810**: `task_id`
  ```
  mock_get_task.assert_called_once_with(user_id, task_id)
  ```

- **Line 812**: `task_id`
  ```
  user_id, task_id
  ```

- **Line 815**: `task_id`
  ```
  user_id, task_id, {"reminder_sent": True}
  ```

- **Line 823**: `task_id`
  ```
  task_id = "task-1"
  ```

- **Line 827**: `task_id`
  ```
  "task_id": task_id,
  ```

- **Line 827**: `task_id`
  ```
  "task_id": task_id,
  ```

- **Line 834**: `task_id`
  ```
  scheduler_manager.handle_task_reminder(user_id, task_id)
  ```

- **Line 837**: `task_id`
  ```
  mock_get_task.assert_called_once_with(user_id, task_id)
  ```

- **Line 1380**: `task_id`
  ```
  {"task_id": "task1", "completed": False, "title": "Test Task 1"},
  ```

- **Line 1381**: `task_id`
  ```
  {"task_id": "task2", "completed": False, "title": "Test Task 2"},
  ```

- **Line 1385**: `task_id`
  ```
  mock_select_task.return_value = {"task_id": "task1", "title": "Test Task 1"}
  ```

- **Line 1453**: `task_id`
  ```
  {"task_id": "task1", "completed": False, "title": "Test Task 1"}
  ```

- **Line 1456**: `task_id`
  ```
  mock_select_task.return_value = {"task_id": "task1", "title": "Test Task 1"}
  ```

### tests\behavior\test_task_behavior.py
**Issues Found**: 34

- **Line 28**: `completed_tasks`
  ```
  load_completed_tasks,
  ```

- **Line 77**: `active_tasks.json`
  ```
  assert not os.path.exists(os.path.join(task_dir, "active_tasks.json"))
  ```

- **Line 78**: `completed_tasks.json`
  ```
  assert not os.path.exists(os.path.join(task_dir, "completed_tasks.json"))
  ```

- **Line 78**: `completed_tasks`
  ```
  assert not os.path.exists(os.path.join(task_dir, "completed_tasks.json"))
  ```

- **Line 79**: `task_schedules.json`
  ```
  assert not os.path.exists(os.path.join(task_dir, "task_schedules.json"))
  ```

- **Line 109**: `task_id`
  ```
  {"task_id": "1", "title": "Test Task 1", "completed": False},
  ```

- **Line 110**: `task_id`
  ```
  {"task_id": "2", "title": "Test Task 2", "completed": False},
  ```

- **Line 128**: `task_id`
  ```
  assert all("task_id" not in task for task in saved_data["tasks"])
  ```

- **Line 136**: `task_id`
  ```
  task_id = create_task(
  ```

- **Line 144**: `task_id`
  ```
  assert task_id is not None
  ```

- **Line 160**: `task_id`
  ```
  assert any(t["id"] == task_id and t["status"] == "active" for t in data["tasks"])
  ```

- **Line 168**: `task_id`
  ```
  task_id = create_task(user_id, "Original Title", "Original Description")
  ```

- **Line 175**: `task_id`
  ```
  result = update_task(user_id, task_id, updates)
  ```

- **Line 189**: `task_id`
  ```
  t["id"] == task_id and t["title"] == "Updated Title"
  ```

- **Line 200**: `task_id`
  ```
  task_id = create_task(user_id, "Test Task")
  ```

- **Line 203**: `task_id`
  ```
  result = complete_task(user_id, task_id)
  ```

- **Line 210**: `completed_tasks`
  ```
  completed_tasks = load_completed_tasks(user_id)
  ```

- **Line 210**: `completed_tasks`
  ```
  completed_tasks = load_completed_tasks(user_id)
  ```

- **Line 211**: `completed_tasks`
  ```
  assert len(completed_tasks) == 1
  ```

- **Line 212**: `completed_tasks`
  ```
  assert completed_tasks[0]["completed"] is True
  ```

- **Line 213**: `completed_tasks`
  ```
  assert completed_tasks[0]["completed_at"] is not None
  ```

- **Line 221**: `task_id`
  ```
  t["id"] == task_id and t["status"] == "completed" and t["completion"]["completed"]
  ```

- **Line 231**: `task_id`
  ```
  task_id = create_task(user_id, "Test Task")
  ```

- **Line 233**: `task_id`
  ```
  result = delete_task(user_id, task_id)
  ```

- **Line 237**: `task_id`
  ```
  assert all(t["task_id"] != task_id for t in tasks)
  ```

- **Line 237**: `task_id`
  ```
  assert all(t["task_id"] != task_id for t in tasks)
  ```

- **Line 243**: `task_id`
  ```
  assert all(t["id"] != task_id for t in data["tasks"])
  ```

- **Line 251**: `task_id`
  ```
  task_id = create_task(user_id, "Test Task", "Desc")
  ```

- **Line 253**: `task_id`
  ```
  task = get_task_by_id(user_id, task_id)
  ```

- **Line 255**: `task_id`
  ```
  assert task["task_id"] == task_id
  ```

- **Line 255**: `task_id`
  ```
  assert task["task_id"] == task_id
  ```

- **Line 262**: `task_id`
  ```
  assert any(t["id"] == task_id for t in data["tasks"])
  ```

- **Line 291**: `task_id`
  ```
  assert any(t["task_id"] == id_soon for t in due_soon_tasks)
  ```

- **Line 292**: `task_id`
  ```
  assert all(t["task_id"] != id_late for t in due_soon_tasks)
  ```

### tests\behavior\test_task_cleanup_bug.py
**Issues Found**: 4

- **Line 60**: `task_id`
  ```
  task_id = create_task(
  ```

- **Line 66**: `task_id`
  ```
  assert task_id is not None, "Task should be created"
  ```

- **Line 73**: `task_id`
  ```
  cleanup_task_reminders(user_id, task_id)
  ```

- **Line 76**: `task_id`
  ```
  user_id, task_id
  ```

### tests\behavior\test_task_crud_disambiguation.py
**Issues Found**: 14

- **Line 24**: `task_id`
  ```
  tasks.append({"title": "Wash dishes", "task_id": "tdishes"})
  ```

- **Line 25**: `task_id`
  ```
  tasks.append({"title": "Wash laundry", "task_id": "tlaundry"})
  ```

- **Line 41**: `task_id`
  ```
  tasks.append({"title": "Task A", "task_id": "taskaaaa"})
  ```

- **Line 42**: `task_id`
  ```
  tasks.append({"title": "Task B", "task_id": "taskbbbb"})
  ```

- **Line 56**: `task_id`
  ```
  tasks.append({"title": "Brush teeth", "task_id": "teeth123"})
  ```

- **Line 76**: `task_id`
  ```
  tasks.append({"title": "Wash dishes", "task_id": "wash0001"})
  ```

- **Line 83**: `task_id`
  ```
  updated = [t for t in tasks2 if t.get('task_id') == 'wash0001']
  ```

- **Line 91**: `task_id`
  ```
  tasks.append({"title": "Change me", "task_id": "chg001"})
  ```

- **Line 106**: `task_id`
  ```
  tasks.append({"title": "Take a walk", "task_id": "walk001"})
  ```

- **Line 122**: `task_id`
  ```
  tasks.append({"title": "Wash dishes", "task_id": "washA"})
  ```

- **Line 123**: `task_id`
  ```
  tasks.append({"title": "Wash laundry", "task_id": "washB"})
  ```

- **Line 136**: `task_id`
  ```
  tasks.append({"title": "Rename me", "task_id": "rename01"})
  ```

- **Line 142**: `task_id`
  ```
  t1 = [t for t in tasks1 if t.get('task_id') == 'rename01'][0]
  ```

- **Line 150**: `task_id`
  ```
  still_exists = any(t.get('task_id') == 'rename01' for t in tasks_after)
  ```

### tests\behavior\test_task_error_handling.py
**Issues Found**: 31

- **Line 77**: `task_id`
  ```
  task_id = create_task(
  ```

- **Line 80**: `task_id`
  ```
  assert task_id is not None, "Task should be created"
  ```

- **Line 82**: `task_id`
  ```
  task = get_task_by_id(user_id, task_id)
  ```

- **Line 97**: `task_id`
  ```
  task_id = create_task(
  ```

- **Line 100**: `task_id`
  ```
  assert task_id is not None, "Task should be created even with invalid date"
  ```

- **Line 102**: `task_id`
  ```
  task = get_task_by_id(user_id, task_id)
  ```

- **Line 159**: `task_id`
  ```
  task_id = create_task(user_id=user_id, title="Test Task")
  ```

- **Line 172**: `task_id`
  ```
  result = schedule_task_reminders(user_id, task_id, reminder_periods)
  ```

- **Line 186**: `task_id`
  ```
  task_id = create_task(user_id=user_id, title="Test Task")
  ```

- **Line 209**: `task_id`
  ```
  result = schedule_task_reminders(user_id, task_id, incomplete_periods)
  ```

- **Line 234**: `active_tasks.json`
  ```
  task_file = user_dir / "tasks" / "active_tasks.json"
  ```

- **Line 298**: `task_id`
  ```
  task_id = create_task(
  ```

- **Line 304**: `task_id`
  ```
  assert task_id is not None, "Task should be created"
  ```

- **Line 305**: `task_id`
  ```
  task = get_task_by_id(user_id, task_id)
  ```

- **Line 328**: `task_id`
  ```
  task_id = create_task(user_id=user_id, title="Overdue Task", due_date=past_date)
  ```

- **Line 330**: `task_id`
  ```
  assert task_id is not None, "Task should be created even with past due_date"
  ```

- **Line 333**: `task_id`
  ```
  task = get_task_by_id(user_id, task_id)
  ```

- **Line 335**: `task_id`
  ```
  assert task is not None, f"Task should be retrievable. Task ID: {task_id}"
  ```

- **Line 350**: `task_id`
  ```
  task_id = create_task(user_id=user_id, title=long_title)
  ```

- **Line 352**: `task_id`
  ```
  assert task_id is not None, "Task should be created even with very long title"
  ```

- **Line 353**: `task_id`
  ```
  task = get_task_by_id(user_id, task_id)
  ```

- **Line 368**: `task_id`
  ```
  task_id = create_task(user_id=user_id, title=unicode_title)
  ```

- **Line 370**: `task_id`
  ```
  assert task_id is not None, "Task should be created with unicode"
  ```

- **Line 371**: `task_id`
  ```
  task = get_task_by_id(user_id, task_id)
  ```

- **Line 388**: `task_id`
  ```
  task_id = create_task(
  ```

- **Line 392**: `task_id`
  ```
  assert task_id is not None, "Task should be created"
  ```

- **Line 393**: `task_id`
  ```
  task = get_task_by_id(user_id, task_id)
  ```

- **Line 410**: `task_id`
  ```
  task_id1 = create_task(user_id=user_id, title=title)
  ```

- **Line 411**: `task_id`
  ```
  task_id2 = create_task(user_id=user_id, title=title)
  ```

- **Line 413**: `task_id`
  ```
  assert task_id1 != task_id2, "Tasks should have different IDs"
  ```

- **Line 413**: `task_id`
  ```
  assert task_id1 != task_id2, "Tasks should have different IDs"
  ```

### tests\behavior\test_task_handler_behavior.py
**Issues Found**: 33

- **Line 352**: `task_id`
  ```
  "task_id": "task_1",
  ```

- **Line 358**: `task_id`
  ```
  "task_id": "task_2",
  ```

- **Line 434**: `task_id`
  ```
  "task_id": "task_1",
  ```

- **Line 442**: `task_id`
  ```
  "task_id": "task_2",
  ```

- **Line 477**: `task_id`
  ```
  {"title": "Task 1", "priority": "high", "task_id": "task_1"},
  ```

- **Line 478**: `task_id`
  ```
  {"title": "Task 2", "priority": "medium", "task_id": "task_2"},
  ```

- **Line 484**: `task_id`
  ```
  entities={"task_identifier": "1"},
  ```

- **Line 518**: `task_id`
  ```
  {"title": "Task 1", "priority": "high", "task_id": "task_1"}
  ```

- **Line 523**: `task_id`
  ```
  entities={"task_identifier": "999"},
  ```

- **Line 574**: `task_id`
  ```
  {"title": "Task 1", "priority": "high", "task_id": "task_1"}
  ```

- **Line 581**: `task_id`
  ```
  "task_identifier": "1"
  ```

- **Line 617**: `task_id`
  ```
  {"title": "Task 1", "priority": "medium", "task_id": "task_1"}
  ```

- **Line 623**: `task_id`
  ```
  entities={"task_identifier": "1", "priority": "high"},
  ```

- **Line 637**: `task_id`
  ```
  # update_task is called with positional args: (user_id, task_id, updates)
  ```

- **Line 640**: `task_id`
  ```
  call_task_id = (
  ```

- **Line 641**: `task_id`
  ```
  call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("task_id")
  ```

- **Line 650**: `task_id`
  ```
  assert call_task_id == "task_1", "Should update correct task"
  ```

- **Line 670**: `task_id`
  ```
  {"title": "Task 1", "priority": "medium", "task_id": "task_1"}
  ```

- **Line 675**: `task_id`
  ```
  entities={"task_identifier": "1"},
  ```

- **Line 707**: `completed_tasks`
  ```
  "completed_tasks": 10,
  ```

- **Line 751**: `task_id`
  ```
  {"title": "Task 1", "task_id": "task_1"},
  ```

- **Line 752**: `task_id`
  ```
  {"title": "Task 2", "task_id": "task_2"},
  ```

- **Line 753**: `task_id`
  ```
  {"title": "Task 3", "task_id": "task_3"},
  ```

- **Line 767**: `task_id`
  ```
  {"title": "Brush Teeth", "task_id": "task_1"},
  ```

- **Line 768**: `task_id`
  ```
  {"title": "Wash Dishes", "task_id": "task_2"},
  ```

- **Line 782**: `task_id`
  ```
  {"title": "Brush Teeth Every Morning", "task_id": "task_1"},
  ```

- **Line 783**: `task_id`
  ```
  {"title": "Wash Dishes After Dinner", "task_id": "task_2"},
  ```

- **Line 793**: `task_id`
  ```
  def test_task_handler_find_task_by_task_id(self):
  ```

- **Line 794**: `task_id`
  ```
  """Test that TaskManagementHandler finds tasks by task_id."""
  ```

- **Line 797**: `task_id`
  ```
  {"title": "Task 1", "task_id": "task_123"},
  ```

- **Line 798**: `task_id`
  ```
  {"title": "Task 2", "task_id": "task_456"},
  ```

- **Line 802**: `task_id`
  ```
  assert task is not None, "Should find task by task_id"
  ```

- **Line 803**: `task_id`
  ```
  assert task["task_id"] == "task_123", "Should find correct task"
  ```

### tests\behavior\test_task_management_coverage_expansion.py
**Issues Found**: 156

- **Line 32**: `completed_tasks`
  ```
  load_completed_tasks,
  ```

- **Line 33**: `completed_tasks`
  ```
  save_completed_tasks,
  ```

- **Line 98**: `active_tasks.json`
  ```
  assert not (task_dir / "active_tasks.json").exists()
  ```

- **Line 99**: `completed_tasks.json`
  ```
  assert not (task_dir / "completed_tasks.json").exists()
  ```

- **Line 99**: `completed_tasks`
  ```
  assert not (task_dir / "completed_tasks.json").exists()
  ```

- **Line 100**: `task_schedules.json`
  ```
  assert not (task_dir / "task_schedules.json").exists()
  ```

- **Line 128**: `active_tasks.json`
  ```
  "active_tasks.json": {"tasks": [{"existing": "task"}]},
  ```

- **Line 129**: `completed_tasks.json`
  ```
  "completed_tasks.json": {"completed_tasks": []},
  ```

- **Line 129**: `completed_tasks`
  ```
  "completed_tasks.json": {"completed_tasks": []},
  ```

- **Line 129**: `completed_tasks`
  ```
  "completed_tasks.json": {"completed_tasks": []},
  ```

- **Line 130**: `task_schedules.json`
  ```
  "task_schedules.json": {"task_schedules": {}},
  ```

- **Line 144**: `active_tasks.json`
  ```
  active_file = task_dir / "active_tasks.json"
  ```

- **Line 184**: `active_tasks.json`
  ```
  active_file = task_dir / "active_tasks.json"
  ```

- **Line 204**: `task_id`
  ```
  {"task_id": "1", "title": "Task 1", "completed": False},
  ```

- **Line 205**: `task_id`
  ```
  {"task_id": "2", "title": "Task 2", "completed": False},
  ```

- **Line 221**: `active_tasks.json`
  ```
  assert not (task_dir / "active_tasks.json").exists()
  ```

- **Line 231**: `completed_tasks`
  ```
  def test_load_completed_tasks_real_behavior(self, mock_user_data_dir, user_id):
  ```

- **Line 247**: `completed_tasks`
  ```
  tasks = load_completed_tasks(user_id)
  ```

- **Line 254**: `completed_tasks`
  ```
  def test_save_completed_tasks_real_behavior(self, mock_user_data_dir, user_id):
  ```

- **Line 257**: `task_id`
  ```
  {"task_id": "1", "title": "Completed Task 1", "completed": True},
  ```

- **Line 258**: `task_id`
  ```
  {"task_id": "2", "title": "Completed Task 2", "completed": True},
  ```

- **Line 261**: `completed_tasks`
  ```
  result = save_completed_tasks(user_id, test_tasks)
  ```

- **Line 277**: `completed_tasks.json`
  ```
  assert not (task_dir / "completed_tasks.json").exists()
  ```

- **Line 277**: `completed_tasks`
  ```
  assert not (task_dir / "completed_tasks.json").exists()
  ```

- **Line 287**: `task_id`
  ```
  task_id = create_task(
  ```

- **Line 301**: `task_id`
  ```
  assert task_id is not None
  ```

- **Line 308**: `task_id`
  ```
  assert task["task_id"] == task_id
  ```

- **Line 308**: `task_id`
  ```
  assert task["task_id"] == task_id
  ```

- **Line 326**: `task_id`
  ```
  task_id = create_task(user_id=user_id, title="Minimal Task")
  ```

- **Line 328**: `task_id`
  ```
  assert task_id is not None
  ```

- **Line 343**: `task_id`
  ```
  task_id = create_task(user_id="", title="Test Task")
  ```

- **Line 345**: `task_id`
  ```
  assert task_id is None
  ```

- **Line 351**: `task_id`
  ```
  task_id = create_task(user_id=user_id, title="")
  ```

- **Line 353**: `task_id`
  ```
  assert task_id is None
  ```

- **Line 358**: `task_id`
  ```
  task_id = create_task(user_id, "Original Title", "Original Description")
  ```

- **Line 369**: `task_id`
  ```
  result = update_task(user_id, task_id, updates)
  ```

- **Line 390**: `task_id`
  ```
  task_id = create_task(user_id, "Test Task")
  ```

- **Line 404**: `task_id`
  ```
  result = update_task(user_id, task_id, updates)
  ```

- **Line 407**: `task_id`
  ```
  mock_cleanup.assert_called_once_with(user_id, task_id)
  ```

- **Line 409**: `task_id`
  ```
  user_id, task_id, updates["reminder_periods"]
  ```

- **Line 423**: `task_id`
  ```
  task_id = create_task(user_id, "Test Task", "Original Description")
  ```

- **Line 425**: `task_id`
  ```
  # Update with disallowed field (task_id, completed, created_at are not in allowed_fields)
  ```

- **Line 428**: `task_id`
  ```
  "task_id": "new-id",  # Disallowed - should be skipped
  ```

- **Line 433**: `task_id`
  ```
  result = update_task(user_id, task_id, updates)
  ```

- **Line 441**: `task_id`
  ```
  assert task["task_id"] == task_id  # Disallowed field not updated
  ```

- **Line 441**: `task_id`
  ```
  assert task["task_id"] == task_id  # Disallowed field not updated
  ```

- **Line 450**: `task_id`
  ```
  task_id = create_task(user_id, "Test Task", priority="medium")
  ```

- **Line 459**: `task_id`
  ```
  result = update_task(user_id, task_id, updates)
  ```

- **Line 475**: `task_id`
  ```
  task_id = create_task(user_id, "Test Task", priority="medium")
  ```

- **Line 480**: `task_id`
  ```
  result = update_task(user_id, task_id, updates)
  ```

- **Line 494**: `task_id`
  ```
  task_id = create_task(user_id, "Test Task", due_date="2024-12-31")
  ```

- **Line 502**: `task_id`
  ```
  result = update_task(user_id, task_id, updates)
  ```

- **Line 507**: `task_id`
  ```
  task = get_task_by_id(user_id, task_id)
  ```

- **Line 515**: `task_id`
  ```
  task_id = create_task(user_id, "Original Title", "Original Description")
  ```

- **Line 523**: `task_id`
  ```
  result = update_task(user_id, task_id, updates)
  ```

- **Line 538**: `task_id`
  ```
  task_id = create_task(user_id, "Original Title")
  ```

- **Line 543**: `task_id`
  ```
  result = update_task(user_id, task_id, updates)
  ```

- **Line 558**: `task_id`
  ```
  task_id = create_task(user_id, "Test Task")
  ```

- **Line 577**: `task_id`
  ```
  result = update_task(user_id, task_id, updates)
  ```

- **Line 581**: `task_id`
  ```
  mock_cleanup.assert_called_once_with(user_id, task_id)
  ```

- **Line 583**: `task_id`
  ```
  user_id, task_id, updates["reminder_periods"]
  ```

- **Line 597**: `task_id`
  ```
  task_id = create_task(user_id, "Test Task")
  ```

- **Line 602**: `task_id`
  ```
  result = update_task(user_id, task_id, updates)
  ```

- **Line 616**: `task_id`
  ```
  task_id = create_task(user_id, "Test Task")
  ```

- **Line 626**: `task_id`
  ```
  result = complete_task(user_id, task_id, completion_data)
  ```

- **Line 629**: `task_id`
  ```
  mock_cleanup.assert_called_once_with(user_id, task_id)
  ```

- **Line 635**: `completed_tasks`
  ```
  completed_tasks = load_completed_tasks(user_id)
  ```

- **Line 635**: `completed_tasks`
  ```
  completed_tasks = load_completed_tasks(user_id)
  ```

- **Line 636**: `completed_tasks`
  ```
  assert len(completed_tasks) == 1
  ```

- **Line 638**: `completed_tasks`
  ```
  task = completed_tasks[0]
  ```

- **Line 648**: `task_id`
  ```
  task_id = create_task(user_id, "Test Task")
  ```

- **Line 651**: `task_id`
  ```
  result = complete_task(user_id, task_id)
  ```

- **Line 654**: `task_id`
  ```
  mock_cleanup.assert_called_once_with(user_id, task_id)
  ```

- **Line 657**: `completed_tasks`
  ```
  completed_tasks = load_completed_tasks(user_id)
  ```

- **Line 657**: `completed_tasks`
  ```
  completed_tasks = load_completed_tasks(user_id)
  ```

- **Line 658**: `completed_tasks`
  ```
  assert len(completed_tasks) == 1
  ```

- **Line 660**: `completed_tasks`
  ```
  task = completed_tasks[0]
  ```

- **Line 676**: `task_id`
  ```
  task_id = create_task(user_id, "Test Task")
  ```

- **Line 685**: `task_id`
  ```
  result = complete_task(user_id, task_id, completion_data)
  ```

- **Line 688**: `task_id`
  ```
  mock_cleanup.assert_called_once_with(user_id, task_id)
  ```

- **Line 691**: `completed_tasks`
  ```
  completed_tasks = load_completed_tasks(user_id)
  ```

- **Line 691**: `completed_tasks`
  ```
  completed_tasks = load_completed_tasks(user_id)
  ```

- **Line 692**: `completed_tasks`
  ```
  assert len(completed_tasks) == 1
  ```

- **Line 694**: `completed_tasks`
  ```
  task = completed_tasks[0]
  ```

- **Line 704**: `task_id`
  ```
  task_id = create_task(user_id, "Test Task")
  ```

- **Line 711**: `task_id`
  ```
  result = complete_task(user_id, task_id)
  ```

- **Line 718**: `task_id`
  ```
  assert active_tasks[0]["task_id"] == task_id
  ```

- **Line 718**: `task_id`
  ```
  assert active_tasks[0]["task_id"] == task_id
  ```

- **Line 726**: `task_id`
  ```
  task_id = create_task(user_id, "Test Task")
  ```

- **Line 732**: `completed_tasks`
  ```
  # Mock save_active_tasks to succeed but save_completed_tasks to fail
  ```

- **Line 738**: `completed_tasks`
  ```
  "tasks.task_data_manager.save_completed_tasks", return_value=False
  ```

- **Line 742**: `task_id`
  ```
  result = complete_task(user_id, task_id)
  ```

- **Line 746**: `completed_tasks`
  ```
  )  # Should return False when save_completed_tasks fails
  ```

- **Line 749**: `completed_tasks`
  ```
  # Verify save_completed_tasks was called but failed
  ```

- **Line 754**: `completed_tasks`
  ```
  # The key is that the function returns False when save_completed_tasks fails
  ```

- **Line 761**: `task_id`
  ```
  task_id = create_task(user_id, "Test Task")
  ```

- **Line 765**: `task_id`
  ```
  result = complete_task(user_id, task_id)
  ```

- **Line 771**: `completed_tasks`
  ```
  completed_tasks = load_completed_tasks(user_id)
  ```

- **Line 771**: `completed_tasks`
  ```
  completed_tasks = load_completed_tasks(user_id)
  ```

- **Line 772**: `completed_tasks`
  ```
  assert len(completed_tasks) == 1
  ```

- **Line 773**: `completed_tasks`
  ```
  assert completed_tasks[0]["completed"] is True
  ```

- **Line 780**: `task_id`
  ```
  task_id = create_task(
  ```

- **Line 796**: `task_id`
  ```
  result = complete_task(user_id, task_id)
  ```

- **Line 802**: `completed_tasks`
  ```
  completed_tasks = load_completed_tasks(user_id)
  ```

- **Line 802**: `completed_tasks`
  ```
  completed_tasks = load_completed_tasks(user_id)
  ```

- **Line 803**: `completed_tasks`
  ```
  assert len(completed_tasks) == 1
  ```

- **Line 804**: `completed_tasks`
  ```
  assert completed_tasks[0]["completed"] is True
  ```

- **Line 813**: `task_id`
  ```
  task_id = create_task(user_id, "Test Task")
  ```

- **Line 814**: `task_id`
  ```
  complete_task(user_id, task_id)
  ```

- **Line 817**: `task_id`
  ```
  result = restore_task(user_id, task_id)
  ```

- **Line 834**: `task_id`
  ```
  task_id = create_task(
  ```

- **Line 841**: `task_id`
  ```
  complete_task(user_id, task_id)
  ```

- **Line 845**: `task_id`
  ```
  result = restore_task(user_id, task_id)
  ```

- **Line 850**: `task_id`
  ```
  task_id,
  ```

- **Line 863**: `task_id`
  ```
  task_id = create_task(user_id, "Test Task")
  ```

- **Line 866**: `task_id`
  ```
  result = delete_task(user_id, task_id)
  ```

- **Line 869**: `task_id`
  ```
  mock_cleanup.assert_called_once_with(user_id, task_id)
  ```

- **Line 874**: `task_id`
  ```
  assert all(task["task_id"] != task_id for task in tasks)
  ```

- **Line 874**: `task_id`
  ```
  assert all(task["task_id"] != task_id for task in tasks)
  ```

- **Line 887**: `task_id`
  ```
  task_id = create_task(user_id, "Test Task", "Description")
  ```

- **Line 890**: `task_id`
  ```
  task = get_task_by_id(user_id, task_id)
  ```

- **Line 893**: `task_id`
  ```
  assert task["task_id"] == task_id
  ```

- **Line 893**: `task_id`
  ```
  assert task["task_id"] == task_id
  ```

- **Line 902**: `task_id`
  ```
  task_id = create_task(user_id, "Test Task")
  ```

- **Line 903**: `task_id`
  ```
  complete_task(user_id, task_id)
  ```

- **Line 906**: `task_id`
  ```
  task = get_task_by_id(user_id, task_id)
  ```

- **Line 909**: `task_id`
  ```
  assert task["task_id"] == task_id
  ```

- **Line 909**: `task_id`
  ```
  assert task["task_id"] == task_id
  ```

- **Line 937**: `task_id`
  ```
  task_ids = [task["task_id"] for task in due_soon_tasks]
  ```

- **Line 937**: `task_id`
  ```
  task_ids = [task["task_id"] for task in due_soon_tasks]
  ```

- **Line 938**: `task_id`
  ```
  assert id_soon in task_ids
  ```

- **Line 939**: `task_id`
  ```
  assert id_late not in task_ids
  ```

- **Line 940**: `task_id`
  ```
  assert id_no_date not in task_ids
  ```

- **Line 981**: `task_id`
  ```
  task_ids = [task["task_id"] for task in due_soon_tasks]
  ```

- **Line 981**: `task_id`
  ```
  task_ids = [task["task_id"] for task in due_soon_tasks]
  ```

- **Line 982**: `task_id`
  ```
  assert id_exact in task_ids  # Exactly at cutoff should be included
  ```

- **Line 983**: `task_id`
  ```
  assert id_over not in task_ids  # Just over should not be included
  ```

- **Line 1080**: `task_id`
  ```
  task_id = "test-task-id"
  ```

- **Line 1091**: `task_id`
  ```
  result = schedule_task_reminders(user_id, task_id, reminder_periods)
  ```

- **Line 1100**: `task_id`
  ```
  task_id = "test-task-id"
  ```

- **Line 1106**: `task_id`
  ```
  result = schedule_task_reminders(user_id, task_id, reminder_periods)
  ```

- **Line 1114**: `task_id`
  ```
  task_id = "test-task-id"
  ```

- **Line 1116**: `task_id`
  ```
  result = schedule_task_reminders(user_id, task_id, [])
  ```

- **Line 1125**: `task_id`
  ```
  task_id = create_task(user_id, "Test Task")
  ```

- **Line 1137**: `task_id`
  ```
  result = schedule_task_reminders(user_id, task_id, reminder_periods)
  ```

- **Line 1148**: `task_id`
  ```
  task_id = create_task(user_id, "Test Task")
  ```

- **Line 1163**: `task_id`
  ```
  result = schedule_task_reminders(user_id, task_id, reminder_periods)
  ```

- **Line 1174**: `task_id`
  ```
  task_id = create_task(user_id, "Test Task")
  ```

- **Line 1187**: `task_id`
  ```
  result = schedule_task_reminders(user_id, task_id, reminder_periods)
  ```

- **Line 1197**: `task_id`
  ```
  task_id = create_task(user_id, "Test Task")
  ```

- **Line 1204**: `task_id`
  ```
  result = cleanup_task_reminders(user_id, task_id)
  ```

- **Line 1209**: `task_id`
  ```
  user_id, task_id
  ```

- **Line 1217**: `task_id`
  ```
  task_id = create_task(user_id, "Test Task")
  ```

- **Line 1224**: `task_id`
  ```
  result = cleanup_task_reminders(user_id, task_id)
  ```

- **Line 1370**: `task_id`
  ```
  task_id1 = create_task(user_id, "Task 1")
  ```

- **Line 1375**: `task_id`
  ```
  complete_task(user_id, task_id1)
  ```

### tests\behavior\test_task_reminder_followup_behavior.py
**Issues Found**: 26

- **Line 65**: `task_id`
  ```
  "task_id" in conversation_manager.user_states[user_id]["data"]
  ```

- **Line 66**: `task_id`
  ```
  ), "Should store task_id in flow data"
  ```

- **Line 69**: `task_id`
  ```
  task_id = conversation_manager.user_states[user_id]["data"]["task_id"]
  ```

- **Line 69**: `task_id`
  ```
  task_id = conversation_manager.user_states[user_id]["data"]["task_id"]
  ```

- **Line 70**: `task_id`
  ```
  task = get_task_by_id(user_id, task_id)
  ```

- **Line 86**: `task_id`
  ```
  task_id = create_task(
  ```

- **Line 93**: `task_id`
  ```
  conversation_manager.start_task_reminder_followup(user_id, task_id)
  ```

- **Line 110**: `task_id`
  ```
  task = get_task_by_id(user_id, task_id)
  ```

- **Line 140**: `task_id`
  ```
  task_id = create_task(
  ```

- **Line 143**: `task_id`
  ```
  conversation_manager.start_task_reminder_followup(user_id, task_id)
  ```

- **Line 160**: `task_id`
  ```
  task = get_task_by_id(user_id, task_id)
  ```

- **Line 201**: `task_id`
  ```
  task_id = create_task(
  ```

- **Line 204**: `task_id`
  ```
  conversation_manager.start_task_reminder_followup(user_id, task_id)
  ```

- **Line 215**: `task_id`
  ```
  task = get_task_by_id(user_id, task_id)
  ```

- **Line 251**: `task_id`
  ```
  task_id = create_task(user_id=actual_user_id, title="Test task", due_date=due_date)
  ```

- **Line 252**: `task_id`
  ```
  conversation_manager.start_task_reminder_followup(actual_user_id, task_id)
  ```

- **Line 266**: `task_id`
  ```
  lambda: get_task_by_id(actual_user_id, task_id) is not None,
  ```

- **Line 270**: `task_id`
  ```
  task = get_task_by_id(actual_user_id, task_id)
  ```

- **Line 306**: `task_id`
  ```
  task_id = create_task(user_id=user_id, title="Test task without due date")
  ```

- **Line 307**: `task_id`
  ```
  conversation_manager.start_task_reminder_followup(user_id, task_id)
  ```

- **Line 322**: `task_id`
  ```
  task = get_task_by_id(user_id, task_id)
  ```

- **Line 346**: `task_id`
  ```
  task_id = create_task(user_id=user_id, title="Test task", due_date=due_date)
  ```

- **Line 347**: `task_id`
  ```
  conversation_manager.start_task_reminder_followup(user_id, task_id)
  ```

- **Line 387**: `task_id`
  ```
  task_id = create_task(
  ```

- **Line 390**: `task_id`
  ```
  conversation_manager.start_task_reminder_followup(user_id, task_id)
  ```

- **Line 402**: `task_id`
  ```
  task = get_task_by_id(user_id, task_id)
  ```

### tests\behavior\test_task_suggestion_relevance.py
**Issues Found**: 9

- **Line 31**: `task_id`
  ```
  tasks.append({"title": "Test Task", "task_id": "test001"})
  ```

- **Line 54**: `task_id`
  ```
  def test_list_to_edit_flow_confirms_task_identifier(self, test_data_dir):
  ```

- **Line 67**: `task_id`
  ```
  tasks.append({"title": "Task One", "task_id": "task001"})
  ```

- **Line 68**: `task_id`
  ```
  tasks.append({"title": "Task Two", "task_id": "task002"})
  ```

- **Line 100**: `task_id`
  ```
  tasks.append({"title": "My Task", "task_id": "mytask01"})
  ```

- **Line 121**: `task_id`
  ```
  tasks.append({"title": "Test Due Task", "task_id": "duetest01"})
  ```

- **Line 133**: `task_id`
  ```
  task = next((t for t in tasks_after if t.get('task_id') == 'duetest01'), None)
  ```

- **Line 147**: `task_id`
  ```
  tasks.append({"title": "Test Due Date Task", "task_id": "duedatetest01"})
  ```

- **Line 158**: `task_id`
  ```
  task = next((t for t in tasks_after if t.get('task_id') == 'duedatetest01'), None)
  ```

### tests\core\test_message_management.py
**Issues Found**: 5

- **Line 107**: `message_id`
  ```
  "message_id": "m1",
  ```

- **Line 135**: `message_id`
  ```
  "message_id": "old",
  ```

- **Line 141**: `message_id`
  ```
  "message_id": "new",
  ```

- **Line 166**: `message_id`
  ```
  assert archived["messages"][0]["message_id"] == "old"
  ```

- **Line 170**: `message_id`
  ```
  assert active["messages"][0]["message_id"] == "new"
  ```

### tests\core\test_service_request_helpers.py
**Issues Found**: 1

- **Line 140**: `task_id`
  ```
  json.dumps({"user_id": "user-1", "task_id": "task-1"}),
  ```

### tests\core\test_user_data_read_scenarios.py
**Issues Found**: 7

- **Line 40**: `message_id`
  ```
  {"message_id": "dup", "body": "a"},
  ```

- **Line 41**: `message_id`
  ```
  {"message_id": "dup", "body": "b"},
  ```

- **Line 47**: `message_id`
  ```
  ids = [m["message_id"] for m in out["messages"]]
  ```

- **Line 127**: `message_id`
  ```
  def test_load_and_ensure_ids_fixes_duplicate_message_ids(
  ```

- **Line 137**: `message_id`
  ```
  {"message_id": "duplicate-id", "body": "first"},
  ```

- **Line 138**: `message_id`
  ```
  {"message_id": "duplicate-id", "body": "second"},
  ```

- **Line 149**: `message_id`
  ```
  ids = [m.get("message_id") for m in reloaded["messages"]]
  ```

### tests\integration\test_orphaned_reminder_cleanup.py
**Issues Found**: 34

- **Line 46**: `task_id`
  ```
  task_id = create_task(
  ```

- **Line 73**: `task_id`
  ```
  scheduler.handle_task_reminder, user_id=user_id, task_id=task_id
  ```

- **Line 73**: `task_id`
  ```
  scheduler.handle_task_reminder, user_id=user_id, task_id=task_id
  ```

- **Line 81**: `task_id`
  ```
  delete_task(user_id, task_id)
  ```

- **Line 84**: `task_id`
  ```
  assert get_task_by_id(user_id, task_id) is None, "Task should be deleted"
  ```

- **Line 105**: `task_id`
  ```
  and kwargs.get("task_id") == task_id
  ```

- **Line 105**: `task_id`
  ```
  and kwargs.get("task_id") == task_id
  ```

- **Line 119**: `completed_tasks`
  ```
  def test_cleanup_removes_reminders_for_completed_tasks(
  ```

- **Line 133**: `task_id`
  ```
  task_id = create_task(
  ```

- **Line 159**: `task_id`
  ```
  scheduler.handle_task_reminder, user_id=user_id, task_id=task_id
  ```

- **Line 159**: `task_id`
  ```
  scheduler.handle_task_reminder, user_id=user_id, task_id=task_id
  ```

- **Line 163**: `task_id`
  ```
  complete_task(user_id, task_id)
  ```

- **Line 166**: `task_id`
  ```
  get_task_by_id(user_id, task_id)
  ```

- **Line 167**: `completed_tasks.json`
  ```
  # Note: completed tasks are moved to completed_tasks.json, so get_task_by_id might return None
  ```

- **Line 167**: `completed_tasks`
  ```
  # Note: completed tasks are moved to completed_tasks.json, so get_task_by_id might return None
  ```

- **Line 172**: `task_id`
  ```
  active_task_ids = [t.get("task_id") for t in active_tasks]
  ```

- **Line 172**: `task_id`
  ```
  active_task_ids = [t.get("task_id") for t in active_tasks]
  ```

- **Line 173**: `task_id`
  ```
  assert task_id not in active_task_ids, "Task should not be in active tasks"
  ```

- **Line 173**: `task_id`
  ```
  assert task_id not in active_task_ids, "Task should not be in active tasks"
  ```

- **Line 191**: `task_id`
  ```
  and kwargs.get("task_id") == task_id
  ```

- **Line 191**: `task_id`
  ```
  and kwargs.get("task_id") == task_id
  ```

- **Line 219**: `task_id`
  ```
  task_id = create_task(
  ```

- **Line 240**: `task_id`
  ```
  scheduler.handle_task_reminder, user_id=user_id, task_id=task_id
  ```

- **Line 240**: `task_id`
  ```
  scheduler.handle_task_reminder, user_id=user_id, task_id=task_id
  ```

- **Line 244**: `task_id`
  ```
  task = get_task_by_id(user_id, task_id)
  ```

- **Line 256**: `task_id`
  ```
  and (_kw(job) or {}).get("task_id") == task_id
  ```

- **Line 256**: `task_id`
  ```
  and (_kw(job) or {}).get("task_id") == task_id
  ```

- **Line 269**: `task_id`
  ```
  and (_kw(job) or {}).get("task_id") == task_id
  ```

- **Line 269**: `task_id`
  ```
  and (_kw(job) or {}).get("task_id") == task_id
  ```

- **Line 332**: `task_id`
  ```
  scheduler.handle_task_reminder, user_id=user1_id, task_id=task1_id
  ```

- **Line 335**: `task_id`
  ```
  scheduler.handle_task_reminder, user_id=user2_id, task_id=task2_id
  ```

- **Line 358**: `task_id`
  ```
  _kw(job).get("user_id") == user1_id and _kw(job).get("task_id") == task1_id
  ```

- **Line 365**: `task_id`
  ```
  _kw(job).get("user_id") == user2_id and _kw(job).get("task_id") == task2_id
  ```

- **Line 375**: `task_id`
  ```
  "task_id"
  ```

### tests\integration\test_task_cleanup_real.py
**Issues Found**: 42

- **Line 18**: `completed_tasks`
  ```
  load_active_tasks, load_completed_tasks, get_task_by_id
  ```

- **Line 44**: `task_id`
  ```
  task_id = create_task(
  ```

- **Line 50**: `task_id`
  ```
  assert task_id is not None, "Task should be created"
  ```

- **Line 54**: `task_id`
  ```
  assert any(t['task_id'] == task_id for t in active_before), "Task should be in active_tasks"
  ```

- **Line 54**: `task_id`
  ```
  assert any(t['task_id'] == task_id for t in active_before), "Task should be in active_tasks"
  ```

- **Line 56**: `completed_tasks`
  ```
  completed_before = load_completed_tasks(user_id)
  ```

- **Line 57**: `task_id`
  ```
  assert not any(t['task_id'] == task_id for t in completed_before), "Task should not be in completed_tasks"
  ```

- **Line 57**: `task_id`
  ```
  assert not any(t['task_id'] == task_id for t in completed_before), "Task should not be in completed_tasks"
  ```

- **Line 57**: `completed_tasks`
  ```
  assert not any(t['task_id'] == task_id for t in completed_before), "Task should not be in completed_tasks"
  ```

- **Line 67**: `task_id`
  ```
  result = complete_task(user_id, task_id)
  ```

- **Line 74**: `task_id`
  ```
  assert not any(t['task_id'] == task_id for t in active_after), "Task should be removed from active_tasks"
  ```

- **Line 74**: `task_id`
  ```
  assert not any(t['task_id'] == task_id for t in active_after), "Task should be removed from active_tasks"
  ```

- **Line 76**: `completed_tasks`
  ```
  completed_after = load_completed_tasks(user_id)
  ```

- **Line 77**: `task_id`
  ```
  assert any(t['task_id'] == task_id for t in completed_after), "Task should be in completed_tasks"
  ```

- **Line 77**: `task_id`
  ```
  assert any(t['task_id'] == task_id for t in completed_after), "Task should be in completed_tasks"
  ```

- **Line 77**: `completed_tasks`
  ```
  assert any(t['task_id'] == task_id for t in completed_after), "Task should be in completed_tasks"
  ```

- **Line 80**: `task_id`
  ```
  completed_task = next(t for t in completed_after if t['task_id'] == task_id)
  ```

- **Line 80**: `task_id`
  ```
  completed_task = next(t for t in completed_after if t['task_id'] == task_id)
  ```

- **Line 89**: `completed_tasks.json`
  ```
  assert not (user_dir / "tasks" / "completed_tasks.json").exists()
  ```

- **Line 89**: `completed_tasks`
  ```
  assert not (user_dir / "tasks" / "completed_tasks.json").exists()
  ```

- **Line 94**: `task_id`
  ```
  t.get("id") == task_id and t.get("status") == "completed"
  ```

- **Line 112**: `task_id`
  ```
  task_id = create_task(
  ```

- **Line 118**: `task_id`
  ```
  assert task_id is not None, "Task should be created"
  ```

- **Line 122**: `task_id`
  ```
  assert any(t['task_id'] == task_id for t in active_before), "Task should exist before deletion"
  ```

- **Line 122**: `task_id`
  ```
  assert any(t['task_id'] == task_id for t in active_before), "Task should exist before deletion"
  ```

- **Line 132**: `task_id`
  ```
  result = delete_task(user_id, task_id)
  ```

- **Line 139**: `task_id`
  ```
  assert not any(t['task_id'] == task_id for t in active_after), "Task should be removed from active_tasks"
  ```

- **Line 139**: `task_id`
  ```
  assert not any(t['task_id'] == task_id for t in active_after), "Task should be removed from active_tasks"
  ```

- **Line 141**: `completed_tasks`
  ```
  # Verify task not in completed_tasks either
  ```

- **Line 142**: `completed_tasks`
  ```
  completed_after = load_completed_tasks(user_id)
  ```

- **Line 143**: `task_id`
  ```
  assert not any(t['task_id'] == task_id for t in completed_after), "Task should not be in completed_tasks"
  ```

- **Line 143**: `task_id`
  ```
  assert not any(t['task_id'] == task_id for t in completed_after), "Task should not be in completed_tasks"
  ```

- **Line 143**: `completed_tasks`
  ```
  assert not any(t['task_id'] == task_id for t in completed_after), "Task should not be in completed_tasks"
  ```

- **Line 146**: `task_id`
  ```
  task = get_task_by_id(user_id, task_id)
  ```

- **Line 154**: `active_tasks.json`
  ```
  assert not (user_dir / "tasks" / "active_tasks.json").exists()
  ```

- **Line 159**: `task_id`
  ```
  t.get("id") == task_id for t in file_data.get("tasks", [])
  ```

- **Line 176**: `task_id`
  ```
  task_id = create_task(
  ```

- **Line 183**: `task_id`
  ```
  assert task_id is not None, "Task should be created"
  ```

- **Line 186**: `task_id`
  ```
  task_before = get_task_by_id(user_id, task_id)
  ```

- **Line 205**: `task_id`
  ```
  result = update_task(user_id, task_id, updates)
  ```

- **Line 211**: `task_id`
  ```
  task_after = get_task_by_id(user_id, task_id)
  ```

- **Line 226**: `task_id`
  ```
  (t for t in file_data.get("tasks", []) if t.get("id") == task_id),
  ```

### tests\integration\test_task_cleanup_real_bug_verification.py
**Issues Found**: 7

- **Line 52**: `task_id`
  ```
  task_id = create_task(user_id=user_id, title="Task with Reminders")
  ```

- **Line 59**: `task_id`
  ```
  result = cleanup_task_reminders(user_id, task_id)
  ```

- **Line 86**: `task_id`
  ```
  task_id = create_task(user_id=user_id, title="Task to Complete")
  ```

- **Line 92**: `task_id`
  ```
  result = complete_task(user_id, task_id)
  ```

- **Line 120**: `task_id`
  ```
  task_id = create_task(user_id=user_id, title="Task with Reminders")
  ```

- **Line 139**: `task_id`
  ```
  user_id, task_id, reminder_periods
  ```

- **Line 146**: `task_id`
  ```
  cleanup_result = cleanup_task_reminders(user_id, task_id)
  ```

### tests\integration\test_task_cleanup_silent_failure.py
**Issues Found**: 4

- **Line 38**: `task_id`
  ```
  task_id = create_task(user_id=user_id, title="Test Task")
  ```

- **Line 43**: `task_id`
  ```
  cleanup_task_reminders(user_id, task_id)
  ```

- **Line 74**: `task_id`
  ```
  task_id = create_task(user_id=user_id, title="Task to Complete")
  ```

- **Line 78**: `task_id`
  ```
  result = complete_task(user_id, task_id)
  ```

### tests\integration\test_task_reminder_integration.py
**Issues Found**: 20

- **Line 64**: `task_id`
  ```
  task_id = create_task(
  ```

- **Line 70**: `task_id`
  ```
  assert task_id is not None, "Task should be created"
  ```

- **Line 119**: `task_id`
  ```
  task_id = create_task(
  ```

- **Line 134**: `task_id`
  ```
  result = complete_task(user_id, task_id)
  ```

- **Line 140**: `task_id`
  ```
  user_id, task_id
  ```

- **Line 170**: `task_id`
  ```
  task_id = create_task(
  ```

- **Line 185**: `task_id`
  ```
  result = delete_task(user_id, task_id)
  ```

- **Line 191**: `task_id`
  ```
  user_id, task_id
  ```

- **Line 221**: `task_id`
  ```
  task_id = create_task(
  ```

- **Line 251**: `task_id`
  ```
  user_id, task_id, {"reminder_periods": new_reminders}
  ```

- **Line 258**: `task_id`
  ```
  user_id, task_id
  ```

- **Line 296**: `task_id`
  ```
  task_id = create_task(
  ```

- **Line 316**: `task_id`
  ```
  result = complete_task(user_id, task_id)
  ```

- **Line 343**: `completed_tasks`
  ```
  def test_reminder_delivery_skips_completed_tasks(self, test_data_dir):
  ```

- **Line 361**: `task_id`
  ```
  task_id = create_task(user_id=user_id, title="Task to Complete")
  ```

- **Line 362**: `task_id`
  ```
  complete_task(user_id, task_id)
  ```

- **Line 365**: `task_id`
  ```
  scheduler.handle_task_reminder(user_id, task_id)
  ```

- **Line 391**: `task_id`
  ```
  task_id = create_task(user_id=user_id, title="Active Task")
  ```

- **Line 394**: `task_id`
  ```
  scheduler.handle_task_reminder(user_id, task_id)
  ```

- **Line 397**: `task_id`
  ```
  mock_comm_manager.handle_task_reminder.assert_called_once_with(user_id, task_id)
  ```

### tests\test_helpers\test_support\conftest_mocks.py
**Issues Found**: 3

- **Line 53**: `task_id`
  ```
  "task_id": "test-task-123",
  ```

- **Line 68**: `message_id`
  ```
  "message_id": "test-message-123",
  ```

- **Line 94**: `message_id`
  ```
  "message_id": "test-msg-123",
  ```

### tests\test_helpers\test_utilities\test_data_factory.py
**Issues Found**: 2

- **Line 121**: `task_id`
  ```
  "task_id": str(uuid.uuid4()),
  ```

- **Line 154**: `message_id`
  ```
  "message_id": str(uuid.uuid4()),
  ```

### tests\ui\test_dialog_behavior.py
**Issues Found**: 1

- **Line 440**: `completed_tasks`
  ```
  assert hasattr(dialog.ui, 'label_completed_tasks'), "Completed tasks label should exist"
  ```

### tests\ui\test_dialog_coverage_expansion.py
**Issues Found**: 2

- **Line 284**: `task_id`
  ```
  'task_id': 'task1',  # Changed from 'id' to 'task_id'
  ```

- **Line 284**: `task_id`
  ```
  'task_id': 'task1',  # Changed from 'id' to 'task_id'
  ```

### tests\ui\test_message_editor_dialog.py
**Issues Found**: 19

- **Line 80**: `message_id`
  ```
  'message_id': 'test_message_id',
  ```

- **Line 80**: `message_id`
  ```
  'message_id': 'test_message_id',
  ```

- **Line 287**: `message_id`
  ```
  'message_id': 'test_message_id',
  ```

- **Line 287**: `message_id`
  ```
  'message_id': 'test_message_id',
  ```

- **Line 328**: `message_id`
  ```
  assert 'message_id' in message_data, "Should include message_id"
  ```

- **Line 328**: `message_id`
  ```
  assert 'message_id' in message_data, "Should include message_id"
  ```

- **Line 355**: `message_id`
  ```
  assert call_args[0][2] == 'test_message_id', "Should pass message_id"
  ```

- **Line 355**: `message_id`
  ```
  assert call_args[0][2] == 'test_message_id', "Should pass message_id"
  ```

- **Line 367**: `message_id`
  ```
  def test_save_edit_fails_without_message_id(self, dialog_edit):
  ```

- **Line 368**: `message_id`
  ```
  """Test: Save edit fails when message_id is missing"""
  ```

- **Line 370**: `message_id`
  ```
  dialog_edit.message_data = {}  # Remove message_id
  ```

- **Line 405**: `message_id`
  ```
  'message_id': 'msg1',
  ```

- **Line 411**: `message_id`
  ```
  'message_id': 'msg2',
  ```

- **Line 510**: `message_id`
  ```
  'message_id': 'msg1',
  ```

- **Line 532**: `message_id`
  ```
  'message_id': 'msg2',
  ```

- **Line 545**: `message_id`
  ```
  assert dialog.messages[0]['message_id'] == 'msg2', "Should load new message"
  ```

- **Line 598**: `message_id`
  ```
  message_id = dialog.messages[0].get('message_id')
  ```

- **Line 598**: `message_id`
  ```
  message_id = dialog.messages[0].get('message_id')
  ```

- **Line 613**: `message_id`
  ```
  mock_delete.assert_called_once_with(dialog.user_id, dialog.category, message_id)
  ```

### tests\ui\test_task_crud_dialog.py
**Issues Found**: 40

- **Line 47**: `task_id`
  ```
  'task_id': 'task1',
  ```

- **Line 57**: `task_id`
  ```
  'task_id': 'task2',
  ```

- **Line 67**: `completed_tasks`
  ```
  'completed_tasks': [
  ```

- **Line 69**: `task_id`
  ```
  'task_id': 'task3',
  ```

- **Line 84**: `completed_tasks`
  ```
  with patch('ui.dialogs.task_crud_dialog.load_completed_tasks') as mock_load_completed:
  ```

- **Line 98**: `completed_tasks`
  ```
  assert dialog.completed_tasks == []
  ```

- **Line 110**: `completed_tasks`
  ```
  with patch('ui.dialogs.task_crud_dialog.load_completed_tasks') as mock_load_completed:
  ```

- **Line 123**: `completed_tasks`
  ```
  assert dialog.ui.tableWidget_completed_tasks.columnCount() == 6
  ```

- **Line 134**: `completed_tasks`
  ```
  (h.text() if (h := dialog.ui.tableWidget_completed_tasks.horizontalHeaderItem(i)) else "")
  ```

- **Line 135**: `completed_tasks`
  ```
  for i in range(dialog.ui.tableWidget_completed_tasks.columnCount())
  ```

- **Line 147**: `completed_tasks`
  ```
  with patch('ui.dialogs.task_crud_dialog.load_completed_tasks') as mock_load_completed:
  ```

- **Line 151**: `completed_tasks`
  ```
  mock_load_completed.return_value = mock_task_data['completed_tasks']
  ```

- **Line 160**: `completed_tasks`
  ```
  assert len(dialog.completed_tasks) == 1
  ```

- **Line 164**: `completed_tasks`
  ```
  assert dialog.ui.tableWidget_completed_tasks.rowCount() == 1
  ```

- **Line 173**: `completed_tasks`
  ```
  with patch('ui.dialogs.task_crud_dialog.load_completed_tasks') as mock_load_completed:
  ```

- **Line 186**: `completed_tasks`
  ```
  assert dialog.completed_tasks == []
  ```

- **Line 195**: `completed_tasks`
  ```
  with patch('ui.dialogs.task_crud_dialog.load_completed_tasks') as mock_load_completed:
  ```

- **Line 223**: `completed_tasks`
  ```
  def test_refresh_completed_tasks(self, qt_app, test_data_dir, mock_task_data):
  ```

- **Line 226**: `completed_tasks`
  ```
  with patch('ui.dialogs.task_crud_dialog.load_completed_tasks') as mock_load_completed:
  ```

- **Line 230**: `completed_tasks`
  ```
  mock_load_completed.return_value = mock_task_data['completed_tasks']
  ```

- **Line 238**: `completed_tasks`
  ```
  assert dialog.ui.tableWidget_completed_tasks.rowCount() == 1
  ```

- **Line 241**: `completed_tasks`
  ```
  dialog.refresh_completed_tasks()
  ```

- **Line 244**: `completed_tasks`
  ```
  assert dialog.ui.tableWidget_completed_tasks.rowCount() == 1
  ```

- **Line 247**: `completed_tasks`
  ```
  first_row = dialog.ui.tableWidget_completed_tasks.item(0, 0)
  ```

- **Line 257**: `completed_tasks`
  ```
  with patch('ui.dialogs.task_crud_dialog.load_completed_tasks') as mock_load_completed:
  ```

- **Line 292**: `completed_tasks`
  ```
  with patch('ui.dialogs.task_crud_dialog.load_completed_tasks') as mock_load_completed:
  ```

- **Line 317**: `completed_tasks`
  ```
  with patch('ui.dialogs.task_crud_dialog.load_completed_tasks') as mock_load_completed:
  ```

- **Line 342**: `completed_tasks`
  ```
  with patch('ui.dialogs.task_crud_dialog.load_completed_tasks') as mock_load_completed:
  ```

- **Line 367**: `completed_tasks`
  ```
  with patch('ui.dialogs.task_crud_dialog.load_completed_tasks') as mock_load_completed:
  ```

- **Line 394**: `completed_tasks`
  ```
  with patch('ui.dialogs.task_crud_dialog.load_completed_tasks') as mock_load_completed:
  ```

- **Line 419**: `completed_tasks`
  ```
  with patch('ui.dialogs.task_crud_dialog.load_completed_tasks') as mock_load_completed:
  ```

- **Line 448**: `completed_tasks`
  ```
  with patch('ui.dialogs.task_crud_dialog.load_completed_tasks') as mock_load_completed:
  ```

- **Line 473**: `completed_tasks`
  ```
  with patch('ui.dialogs.task_crud_dialog.load_completed_tasks') as mock_load_completed:
  ```

- **Line 478**: `completed_tasks`
  ```
  mock_load_completed.return_value = mock_task_data['completed_tasks']
  ```

- **Line 500**: `completed_tasks`
  ```
  with patch('ui.dialogs.task_crud_dialog.load_completed_tasks') as mock_load_completed:
  ```

- **Line 525**: `completed_tasks`
  ```
  with patch('ui.dialogs.task_crud_dialog.load_completed_tasks') as mock_load_completed:
  ```

- **Line 530**: `completed_tasks`
  ```
  mock_load_completed.return_value = mock_task_data['completed_tasks']
  ```

- **Line 552**: `completed_tasks`
  ```
  with patch('ui.dialogs.task_crud_dialog.load_completed_tasks') as mock_load_completed:
  ```

- **Line 556**: `completed_tasks`
  ```
  mock_load_completed.return_value = mock_task_data['completed_tasks']
  ```

- **Line 577**: `completed_tasks`
  ```
  with patch('ui.dialogs.task_crud_dialog.load_completed_tasks') as mock_load_completed:
  ```

### tests\ui\test_task_management_dialog.py
**Issues Found**: 1

- **Line 118**: `completed_tasks`
  ```
  assert dialog.ui.label_completed_tasks.text() is not None, "Should display completed tasks"
  ```

### tests\unit\test_analytics_handler_helper_branches.py
**Issues Found**: 2

- **Line 270**: `completed_tasks`
  ```
  monkeypatch.setattr("tasks.load_completed_tasks", lambda user_id: [])
  ```

- **Line 313**: `completed_tasks`
  ```
  "tasks.load_completed_tasks",
  ```

### tests\unit\test_channel_orchestrator.py
**Issues Found**: 23

- **Line 81**: `task_id`
  ```
  """Test get_last_task_reminder returns task_id when reminder exists."""
  ```

- **Line 83**: `task_id`
  ```
  task_id = "task_123"
  ```

- **Line 85**: `task_id`
  ```
  self.manager._last_task_reminders[user_id] = task_id
  ```

- **Line 89**: `task_id`
  ```
  assert result == task_id, "Should return task_id for user with reminder"
  ```

- **Line 89**: `task_id`
  ```
  assert result == task_id, "Should return task_id for user with reminder"
  ```

- **Line 124**: `task_id`
  ```
  'task_id': 'task_123'
  ```

- **Line 141**: `task_id`
  ```
  'task_id': 'task_1'
  ```

- **Line 388**: `task_id`
  ```
  # Test None task_id
  ```

- **Line 390**: `task_id`
  ```
  assert result is None, "Should return None for None task_id"
  ```

- **Line 392**: `task_id`
  ```
  # Test empty task_id
  ```

- **Line 394**: `task_id`
  ```
  assert result is None, "Should return None for empty task_id"
  ```

- **Line 399**: `task_id`
  ```
  task_id = "task_123"
  ```

- **Line 401**: `task_id`
  ```
  "task_id": task_id,
  ```

- **Line 401**: `task_id`
  ```
  "task_id": task_id,
  ```

- **Line 426**: `task_id`
  ```
  self.manager.handle_task_reminder(user_id, task_id)
  ```

- **Line 428**: `task_id`
  ```
  assert self.manager.get_last_task_reminder(user_id) == task_id
  ```

- **Line 433**: `task_id`
  ```
  task_id = "task_456"
  ```

- **Line 435**: `task_id`
  ```
  "task_id": task_id,
  ```

- **Line 435**: `task_id`
  ```
  "task_id": task_id,
  ```

- **Line 455**: `task_id`
  ```
  self.manager.handle_task_reminder(user_id, task_id)
  ```

- **Line 471**: `task_id`
  ```
  task = {"task_id": "task_done", "title": "Done", "completed": True}
  ```

- **Line 483**: `task_id`
  ```
  task = {"task_id": "task_ok", "title": "Active task", "completed": False}
  ```

- **Line 499**: `task_id`
  ```
  task = {"task_id": "task_ok", "title": "Active task", "completed": False}
  ```

### tests\unit\test_channel_orchestrator_message_selection.py
**Issues Found**: 3

- **Line 72**: `message_id`
  ```
  message = {"message_id": "m1", "message": "Hello world"}
  ```

- **Line 108**: `message_id`
  ```
  data = {"messages": [{"message": "x", "message_id": "m1", "days": ["MONDAY"], "time_periods": ["morning"]}]}
  ```

- **Line 123**: `message_id`
  ```
  data = {"messages": [{"message": "x", "message_id": "m1", "days": ["MONDAY"], "time_periods": ["morning"]}]}
  ```

### tests\unit\test_command_parser_helpers.py
**Issues Found**: 4

- **Line 42**: `task_id`
  ```
  assert entities.get("task_identifier") == "1", "Should extract task_id"
  ```

- **Line 42**: `task_id`
  ```
  assert entities.get("task_identifier") == "1", "Should extract task_id"
  ```

- **Line 54**: `task_id`
  ```
  assert entities.get("task_identifier") == "5", "Should extract task_id with TASKID key"
  ```

- **Line 54**: `task_id`
  ```
  assert entities.get("task_identifier") == "5", "Should extract task_id with TASKID key"
  ```

### tests\unit\test_command_parser_rule_based_patterns_expansion.py
**Issues Found**: 3

- **Line 96**: `task_id`
  ```
  assert result.parsed_command.entities.get("task_identifier") == expected_identifier
  ```

- **Line 113**: `task_id`
  ```
  assert result.parsed_command.entities.get("task_identifier") == expected_identifier
  ```

- **Line 143**: `task_id`
  ```
  assert entities.get("task_identifier") == expected_identifier
  ```

### tests\unit\test_command_parser_task_entities_expansion.py
**Issues Found**: 4

- **Line 175**: `task_id`
  ```
  "ai_response, expected_title, expected_task_id",
  ```

- **Line 188**: `task_id`
  ```
  self, command_parser, ai_response, expected_title, expected_task_id
  ```

- **Line 193**: `task_id`
  ```
  assert entities.get("task_identifier") == expected_task_id
  ```

- **Line 193**: `task_id`
  ```
  assert entities.get("task_identifier") == expected_task_id
  ```

### tests\unit\test_conversation_flow_reminder_helpers.py
**Issues Found**: 1

- **Line 88**: `task_id`
  ```
  with patch("tasks.get_task_by_id", return_value={"task_id": "t1"}):
  ```

### tests\unit\test_discord_api_client.py
**Issues Found**: 4

- **Line 722**: `message_id`
  ```
  message_id="111222333",
  ```

- **Line 730**: `message_id`
  ```
  assert message_data.message_id == "111222333", "Should set message_id"
  ```

- **Line 730**: `message_id`
  ```
  assert message_data.message_id == "111222333", "Should set message_id"
  ```

- **Line 742**: `message_id`
  ```
  message_id="111222333",
  ```

### tests\unit\test_discord_event_handler.py
**Issues Found**: 3

- **Line 53**: `message_id`
  ```
  message_id="444555666"
  ```

- **Line 61**: `message_id`
  ```
  assert context.message_id == "444555666", "Should set message_id"
  ```

- **Line 61**: `message_id`
  ```
  assert context.message_id == "444555666", "Should set message_id"
  ```

### tests\unit\test_interaction_handlers_helpers.py
**Issues Found**: 36

- **Line 375**: `task_id`
  ```
  """Test _get_task_candidates with exact task_id."""
  ```

- **Line 377**: `task_id`
  ```
  {"task_id": "abc123", "title": "Task 1"},
  ```

- **Line 378**: `task_id`
  ```
  {"task_id": "def456", "title": "Task 2"},
  ```

- **Line 388**: `task_id`
  ```
  {"task_id": "abcdef1234567890", "title": "Task 1"},
  ```

- **Line 389**: `task_id`
  ```
  {"task_id": "def4567890123456", "title": "Task 2"},
  ```

- **Line 399**: `task_id`
  ```
  {"task_id": "abc123", "title": "Task 1"},
  ```

- **Line 400**: `task_id`
  ```
  {"task_id": "def456", "title": "Task 2"},
  ```

- **Line 410**: `task_id`
  ```
  {"task_id": "abc123", "title": "Buy groceries"},
  ```

- **Line 411**: `task_id`
  ```
  {"task_id": "def456", "title": "Call mom"},
  ```

- **Line 421**: `task_id`
  ```
  {"task_id": "abc123", "title": "Buy groceries"},
  ```

- **Line 422**: `task_id`
  ```
  {"task_id": "def456", "title": "Buy milk"},
  ```

- **Line 434**: `task_id`
  ```
  {"task_id": "abc123", "title": "Task 1"},
  ```

- **Line 435**: `task_id`
  ```
  {"task_id": "def456", "title": "Task 2"},
  ```

- **Line 442**: `task_id`
  ```
  """Test _find_task_by_identifier_for_operation with exact task_id."""
  ```

- **Line 444**: `task_id`
  ```
  {"task_id": "abc123", "title": "Task 1"},
  ```

- **Line 445**: `task_id`
  ```
  {"task_id": "def456", "title": "Task 2"},
  ```

- **Line 455**: `task_id`
  ```
  {"task_id": "abcdef1234567890", "title": "Task 1"},
  ```

- **Line 456**: `task_id`
  ```
  {"task_id": "def4567890123456", "title": "Task 2"},
  ```

- **Line 466**: `task_id`
  ```
  {"task_id": "abc123", "title": "Task 1"},
  ```

- **Line 467**: `task_id`
  ```
  {"task_id": "def456", "title": "Task 2"},
  ```

- **Line 477**: `task_id`
  ```
  {"task_id": "abc123", "title": "Buy groceries"},
  ```

- **Line 478**: `task_id`
  ```
  {"task_id": "def456", "title": "Call mom"},
  ```

- **Line 488**: `task_id`
  ```
  {"task_id": "abc123", "title": "Buy groceries"},
  ```

- **Line 489**: `task_id`
  ```
  {"task_id": "def456", "title": "Call mom"},
  ```

- **Line 499**: `task_id`
  ```
  {"task_id": "abc123", "title": "Task 1"},
  ```

- **Line 500**: `task_id`
  ```
  {"task_id": "def456", "title": "Task 2"},
  ```

- **Line 525**: `task_id`
  ```
  "task_id": "abc123",
  ```

- **Line 531**: `task_id`
  ```
  "task_id": "def456",
  ```

- **Line 560**: `task_id`
  ```
  "task_id": "abc123",
  ```

- **Line 566**: `task_id`
  ```
  "task_id": "def456",
  ```

- **Line 596**: `task_id`
  ```
  "task_id": "abc123",
  ```

- **Line 602**: `task_id`
  ```
  "task_id": "def456",
  ```

- **Line 622**: `task_id`
  ```
  "task_id": "abc123",
  ```

- **Line 639**: `task_id`
  ```
  "task_id": "abc123",
  ```

- **Line 654**: `task_id`
  ```
  "task_id": "abc123",
  ```

- **Line 667**: `task_id`
  ```
  {"task_id": f"abc{i}", "title": f"Task {i}", "priority": "medium"}
  ```

### tests\unit\test_recurring_tasks.py
**Issues Found**: 28

- **Line 16**: `completed_tasks`
  ```
  load_completed_tasks,
  ```

- **Line 44**: `active_tasks.json`
  ```
  active_tasks_file = os.path.join(tasks_dir, 'active_tasks.json')
  ```

- **Line 45**: `completed_tasks.json`
  ```
  completed_tasks_file = os.path.join(tasks_dir, 'completed_tasks.json')
  ```

- **Line 45**: `completed_tasks`
  ```
  completed_tasks_file = os.path.join(tasks_dir, 'completed_tasks.json')
  ```

- **Line 45**: `completed_tasks`
  ```
  completed_tasks_file = os.path.join(tasks_dir, 'completed_tasks.json')
  ```

- **Line 49**: `completed_tasks`
  ```
  with open(completed_tasks_file, 'w') as f:
  ```

- **Line 50**: `completed_tasks`
  ```
  f.write('{"completed_tasks": []}')
  ```

- **Line 61**: `task_id`
  ```
  task_id = create_task(
  ```

- **Line 72**: `task_id`
  ```
  assert task_id is not None
  ```

- **Line 92**: `task_id`
  ```
  task_id = create_task(
  ```

- **Line 104**: `task_id`
  ```
  success = complete_task(user_id, task_id)
  ```

- **Line 108**: `completed_tasks`
  ```
  completed_tasks = load_completed_tasks(user_id)
  ```

- **Line 108**: `completed_tasks`
  ```
  completed_tasks = load_completed_tasks(user_id)
  ```

- **Line 109**: `completed_tasks`
  ```
  assert len(completed_tasks) == 1
  ```

- **Line 110**: `task_id`
  ```
  assert completed_tasks[0]['task_id'] == task_id
  ```

- **Line 110**: `task_id`
  ```
  assert completed_tasks[0]['task_id'] == task_id
  ```

- **Line 110**: `completed_tasks`
  ```
  assert completed_tasks[0]['task_id'] == task_id
  ```

- **Line 111**: `completed_tasks`
  ```
  assert completed_tasks[0]['completed'] is True
  ```

- **Line 118**: `task_id`
  ```
  assert new_task['task_id'] != task_id  # Different task ID
  ```

- **Line 118**: `task_id`
  ```
  assert new_task['task_id'] != task_id  # Different task ID
  ```

- **Line 193**: `task_id`
  ```
  task_id = create_task(
  ```

- **Line 202**: `task_id`
  ```
  success = complete_task(user_id, task_id)
  ```

- **Line 206**: `completed_tasks`
  ```
  completed_tasks = load_completed_tasks(user_id)
  ```

- **Line 206**: `completed_tasks`
  ```
  completed_tasks = load_completed_tasks(user_id)
  ```

- **Line 207**: `completed_tasks`
  ```
  assert len(completed_tasks) == 1
  ```

- **Line 208**: `task_id`
  ```
  assert completed_tasks[0]['task_id'] == task_id
  ```

- **Line 208**: `task_id`
  ```
  assert completed_tasks[0]['task_id'] == task_id
  ```

- **Line 208**: `completed_tasks`
  ```
  assert completed_tasks[0]['task_id'] == task_id
  ```

### tests\unit\test_schema_validation_helpers.py
**Issues Found**: 5

- **Line 101**: `message_id`
  ```
  "message_id": "1",
  ```

- **Line 108**: `message_id`
  ```
  "message_id": "2",
  ```

- **Line 113**: `message_id`
  ```
  {"message_id": "3"},
  ```

- **Line 123**: `message_id`
  ```
  "message_id": "1",
  ```

- **Line 130**: `message_id`
  ```
  "message_id": "2",
  ```

### tests\unit\test_schemas_validation.py
**Issues Found**: 2

- **Line 112**: `message_id`
  ```
  {"message_id": "1", "message": "Hello!", "days": [], "time_periods": []},
  ```

- **Line 122**: `message_id`
  ```
  {"message_id": "1", "message": "Hello!", "days": ["ALL"], "time_periods": ["ALL"], "timestamp": None}
  ```

### tests\unit\test_user_data_v2_migration.py
**Issues Found**: 35

- **Line 18**: `completed_tasks`
  ```
  from tasks.task_data_handlers import load_active_tasks, load_completed_tasks, save_active_tasks
  ```

- **Line 31**: `task_id`
  ```
  "task_id": "11111111-1111-4111-8111-111111111111",
  ```

- **Line 44**: `completed_tasks`
  ```
  "completed_tasks": [
  ```

- **Line 46**: `task_id`
  ```
  "task_id": "22222222-2222-4222-8222-222222222222",
  ```

- **Line 71**: `task_id`
  ```
  assert "task_id" not in active_task
  ```

- **Line 141**: `message_id`
  ```
  "message_id": "template-1",
  ```

- **Line 155**: `message_id`
  ```
  "message_id": "template-1",
  ```

- **Line 158**: `delivery_status`
  ```
  "delivery_status": "sent",
  ```

- **Line 176**: `delivery_status`
  ```
  assert "delivery_status" not in delivery
  ```

- **Line 178**: `message_id`
  ```
  assert set(template_report["fields_renamed"]) == {"days", "message", "message_id", "time_periods", "timestamp"}
  ```

- **Line 180**: `message_id`
  ```
  assert set(delivery_report["fields_renamed"]) == {"delivery_status", "message", "message_id", "timestamp"}
  ```

- **Line 180**: `delivery_status`
  ```
  assert set(delivery_report["fields_renamed"]) == {"delivery_status", "message", "message_id", "timestamp"}
  ```

- **Line 206**: `task_id`
  ```
  "task_id": "legacy",
  ```

- **Line 225**: `task_id`
  ```
  assert "task_id" in errors[0]
  ```

- **Line 235**: `active_tasks.json`
  ```
  (user_root / "tasks" / "active_tasks.json").write_text(
  ```

- **Line 236**: `task_id`
  ```
  json.dumps({"tasks": [{"task_id": "task-1", "title": "Plan", "created_at": TIMESTAMP}]}),
  ```

- **Line 239**: `completed_tasks.json`
  ```
  (user_root / "tasks" / "completed_tasks.json").write_text(
  ```

- **Line 239**: `completed_tasks`
  ```
  (user_root / "tasks" / "completed_tasks.json").write_text(
  ```

- **Line 240**: `completed_tasks`
  ```
  json.dumps({"completed_tasks": []}),
  ```

- **Line 243**: `task_schedules.json`
  ```
  (user_root / "tasks" / "task_schedules.json").write_text(
  ```

- **Line 269**: `active_tasks.json`
  ```
  assert not (user_root / "tasks" / "active_tasks.json").exists()
  ```

- **Line 270**: `completed_tasks.json`
  ```
  assert not (user_root / "tasks" / "completed_tasks.json").exists()
  ```

- **Line 270**: `completed_tasks`
  ```
  assert not (user_root / "tasks" / "completed_tasks.json").exists()
  ```

- **Line 271**: `task_schedules.json`
  ```
  assert not (user_root / "tasks" / "task_schedules.json").exists()
  ```

- **Line 275**: `active_tasks.json`
  ```
  assert "tasks/active_tasks.json" in written["files_removed"]
  ```

- **Line 320**: `message_id`
  ```
  "message_id": "template-1",
  ```

- **Line 365**: `message_id`
  ```
  assert messages[0]["message_id"] == "template-1"
  ```

- **Line 500**: `completed_tasks`
  ```
  completed = load_completed_tasks("user-1")
  ```

- **Line 505**: `task_id`
  ```
  assert active[0]["task_id"] == "task-active"
  ```

- **Line 507**: `task_id`
  ```
  assert completed[0]["task_id"] == "task-completed"
  ```

- **Line 514**: `task_id`
  ```
  "task_id": "task-new",
  ```

- **Line 525**: `task_id`
  ```
  assert "task_id" not in data["tasks"][0]
  ```

- **Line 526**: `active_tasks.json`
  ```
  assert not (tasks_dir / "active_tasks.json").exists()
  ```

- **Line 527**: `completed_tasks.json`
  ```
  assert not (tasks_dir / "completed_tasks.json").exists()
  ```

- **Line 527**: `completed_tasks`
  ```
  assert not (tasks_dir / "completed_tasks.json").exists()
  ```

### ui\ui_app_qt.py
**Issues Found**: 7

- **Line 2265**: `task_id`
  ```
  task_id = selected_task.get("task_id")
  ```

- **Line 2265**: `task_id`
  ```
  task_id = selected_task.get("task_id")
  ```

- **Line 2268**: `task_id`
  ```
  if not task_id:
  ```

- **Line 2270**: `task_id`
  ```
  self, "Invalid Task", "Selected task has no task_id."
  ```

- **Line 2286**: `task_id`
  ```
  base_dir / f"task_reminder_request_{self.current_user}_{task_id}.flag"
  ```

- **Line 2291**: `task_id`
  ```
  "task_id": task_id,
  ```

- **Line 2291**: `task_id`
  ```
  "task_id": task_id,
  ```

## Legacy Compatibility Markers
**Files Affected**: 4

### core\checkin_analytics.py
**Issues Found**: 1

- **Line 71**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Temporary bridge for flat top-level check-in answers.
  ```

### core\message_management.py
**Issues Found**: 4

- **Line 89**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Temporary bridge for legacy template payloads.
  ```

- **Line 116**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Temporary bridge for legacy sent-message payloads.
  ```

- **Line 143**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Default resources are v2, but tolerate older local
  ```

- **Line 165**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Keep tolerant normalization for pre-v2 schedule/value shapes.
  ```

### notebook\notebook_schemas.py
**Issues Found**: 1

- **Line 90**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Temporary bridge for pre-v2 notebook runtime aliases.
  ```

### tasks\task_data_manager.py
**Issues Found**: 5

- **Line 39**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Temporary runtime bridge for v1-shaped task payloads.
  ```

- **Line 52**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Temporary runtime bridge for v1 due_date field.
  ```

- **Line 64**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Temporary runtime bridge for v1 due_time field.
  ```

- **Line 86**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Temporary runtime bridge for v1 reminder_periods field.
  ```

- **Line 98**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Temporary runtime bridge for v1 recurrence_* fields.
  ```

## User Data V1 Runtime Adapters
**Files Affected**: 71

### ai\chatbot.py
**Issues Found**: 3

- **Line 941**: `.get("timestamp"`
  ```
  ts = recent_checkins[0].get("timestamp", "")
  ```

- **Line 989**: `.get("timestamp"`
  ```
  timestamp = msg.get("timestamp", "")
  ```

- **Line 1022**: `.get("timestamp"`
  ```
  t_ts = latest_task.get("timestamp", "")
  ```

### communication\command_handlers\analytics_handler.py
**Issues Found**: 3

- **Line 516**: `.get("timestamp"`
  ```
  last_timestamp = recent_checkins[0].get("timestamp")
  ```

- **Line 545**: `.get("timestamp"`
  ```
  timestamp = checkin.get("timestamp", "")
  ```

- **Line 766**: `.get("timestamp"`
  ```
  date_value = entry.get("date") or entry.get("timestamp") or "Unknown"
  ```

### communication\command_handlers\checkin_handler.py
**Issues Found**: 2

- **Line 75**: `.get("timestamp"`
  ```
  last_checkin_timestamp = last_checkin.get("timestamp", "")
  ```

- **Line 144**: `.get("timestamp"`
  ```
  timestamp = checkin.get("timestamp", "")
  ```

### communication\command_handlers\notebook_handler.py
**Issues Found**: 4

- **Line 228**: `.get("body"`
  ```
  body = entities.get("body")
  ```

- **Line 397**: `.get("body"`
  ```
  body = entities.get("body")
  ```

- **Line 484**: `.get("body"`
  ```
  text = entities.get("text") or entities.get("body")
  ```

- **Line 511**: `.get("body"`
  ```
  text = entities.get("text") or entities.get("body")
  ```

### communication\command_handlers\task_handler.py
**Issues Found**: 14

- **Line 793**: `"task_id"`
  ```
  task_id = suggested_task.get("task_id", "")
  ```

- **Line 836**: `"task_id"`
  ```
  if _get_tasks().complete_task(user_id, task.get("task_id", task.get("id"))):
  ```

- **Line 870**: `"task_id"`
  ```
  str(t.get("task_id", "")).lower(),
  ```

- **Line 876**: `"task_id"`
  ```
  and str(t.get("task_id", "")) == str(task_identifier)
  ```

- **Line 892**: `"task_id"`
  ```
  task_id = task.get("task_id", task.get("id"))
  ```

- **Line 943**: `"task_id"`
  ```
  str(task.get("task_id", "")).lower(),
  ```

- **Line 948**: `"task_id"`
  ```
  PENDING_DELETIONS[user_id] = task.get("task_id", task.get("id"))
  ```

- **Line 956**: `"task_id"`
  ```
  if _get_tasks().delete_task(user_id, task.get("task_id", task.get("id"))):
  ```

- **Line 1028**: `"task_id"`
  ```
  if _get_tasks().update_task(user_id, task.get("task_id", task.get("id")), updates):
  ```

- **Line 1085**: `"completed_tasks"`
  ```
  completed_tasks = overall_stats.get("completed_tasks", 0)
  ```

- **Line 1127**: `"task_id"`
  ```
  if task.get("task_id") == identifier or task.get("id") == identifier:
  ```

- **Line 1133**: `"task_id"`
  ```
  tid = task.get("task_id", "")
  ```

- **Line 1193**: `"task_id"`
  ```
  if identifier == t.get("task_id") or identifier == t.get("id"):
  ```

- **Line 1198**: `"task_id"`
  ```
  tid = t.get("task_id", "")
  ```

### communication\communication_channels\email\bot.py
**Issues Found**: 1

- **Line 266**: `"message_id"`
  ```
  "message_id": email_id.decode(),
  ```

### communication\core\channel_orchestrator.py
**Issues Found**: 4

- **Line 291**: `"message_id"`
  ```
  email_id = email_msg.get("message_id")
  ```

- **Line 352**: `.get("body"`
  ```
  email_body = email_msg.get("body", "")
  ```

- **Line 1792**: `"message_id"`
  ```
  message_to_send["message_id"],
  ```

- **Line 2105**: `"task_id"`
  ```
  task.get("task_id", "")
  ```

### communication\message_processing\conversation_flow_manager.py
**Issues Found**: 7

- **Line 1361**: `"task_id"`
  ```
  task_id = user_state.get("data", {}).get("task_id")
  ```

- **Line 1562**: `"task_id"`
  ```
  if "task_id" in str(e).lower() or "not found" in str(e).lower():
  ```

- **Line 1759**: `"task_id"`
  ```
  "data": {"task_id": task_id},
  ```

- **Line 1774**: `"task_id"`
  ```
  "data": {"task_id": task_id},
  ```

- **Line 1924**: `"task_id"`
  ```
  task_id = user_state.get("data", {}).get("task_id")
  ```

- **Line 1936**: `"task_id"`
  ```
  task_id = user_state.get("data", {}).get("task_id")
  ```

- **Line 1961**: `"task_id"`
  ```
  task_id = user_state.get("data", {}).get("task_id")
  ```

### communication\message_processing\interaction_manager.py
**Issues Found**: 2

- **Line 621**: `"task_id"`
  ```
  task_id = updated_user_state.get("data", {}).get("task_id")
  ```

- **Line 1327**: `.get("timestamp"`
  ```
  timestamp_str = latest.get("timestamp")
  ```

### core\file_operations.py
**Issues Found**: 1

- **Line 667**: `"completed_tasks"`
  ```
  task_files = {"active_tasks": [], "completed_tasks": [], "task_schedules": {}}
  ```

### core\message_analytics.py
**Issues Found**: 2

- **Line 69**: `.get("timestamp"`
  ```
  timestamp = msg.get("timestamp", "")
  ```

- **Line 149**: `"delivery_status"`
  ```
  status = msg.get("delivery_status", "unknown")
  ```

### core\message_management.py
**Issues Found**: 24

- **Line 94**: `"message_id"`
  ```
  message_id = message.get("id") or message.get("message_id")
  ```

- **Line 97**: `"message_id"`
  ```
  "message_id": message_id,
  ```

- **Line 117**: `"delivery_status"`
  ```
  if delivery.get("message") is not None or delivery.get("delivery_status") is not None or delivery.get("timestamp") is not None:
  ```

- **Line 117**: `.get("timestamp"`
  ```
  if delivery.get("message") is not None or delivery.get("delivery_status") is not None or delivery.get("timestamp") is not None:
  ```

- **Line 119**: `"message_id"`
  ```
  message_id = delivery.get("message_template_id") or delivery.get("message_id")
  ```

- **Line 120**: `.get("timestamp"`
  ```
  sent_at = delivery.get("sent_at") or delivery.get("timestamp", "")
  ```

- **Line 121**: `"delivery_status"`
  ```
  status = delivery.get("status") or delivery.get("delivery_status", "")
  ```

- **Line 124**: `"message_id"`
  ```
  "message_id": message_id,
  ```

- **Line 131**: `"delivery_status"`
  ```
  "delivery_status": status,
  ```

- **Line 139**: `"message_id"`
  ```
  message_id = str(message.get("id") or message.get("message_id") or uuid.uuid4())
  ```

- **Line 140**: `.get("timestamp"`
  ```
  created_at = _canonical_message_timestamp(message.get("created_at") or message.get("timestamp")) or now_timestamp_full()
  ```

- **Line 395**: `"message_id"`
  ```
  if (msg.get("id") or msg.get("message_id")) == message_id
  ```

- **Line 451**: `"message_id"`
  ```
  if (msg.get("id") or msg.get("message_id")) == message_id:
  ```

- **Line 495**: `"message_id"`
  ```
  (msg for msg in data["messages"] if (msg.get("id") or msg.get("message_id")) == message_id), None
  ```

- **Line 577**: `"message_id"`
  ```
  msg.get("message_id"): msg.get("category")
  ```

- **Line 579**: `"message_id"`
  ```
  if isinstance(msg, dict) and msg.get("message_id")
  ```

- **Line 583**: `"message_id"`
  ```
  category_value = id_to_category.get(message.get("message_id"))
  ```

- **Line 618**: `.get("timestamp"`
  ```
  if _parse_message_timestamp(msg.get("timestamp", "")) >= cutoff_date
  ```

- **Line 623**: `.get("timestamp"`
  ```
  key=lambda msg: _parse_message_timestamp(msg.get("timestamp", "")), reverse=True
  ```

- **Line 791**: `.get("timestamp"`
  ```
  message_timestamp = _parse_message_timestamp(message.get("timestamp", ""))
  ```

- **Line 818**: `.get("timestamp"`
  ```
  msg.get("timestamp", "") for msg in archived_messages
  ```

- **Line 821**: `.get("timestamp"`
  ```
  msg.get("timestamp", "") for msg in archived_messages
  ```

- **Line 900**: `.get("timestamp"`
  ```
  timestamp_value = message.get("timestamp", "")
  ```

- **Line 1090**: `.get("timestamp"`
  ```
  timestamp = item.get("timestamp", "1970-01-01 00:00:00")
  ```

### core\response_tracking.py
**Issues Found**: 3

- **Line 39**: `.get("timestamp"`
  ```
  submitted_at = response_data.get("submitted_at") or response_data.get("timestamp") or now_timestamp_full()
  ```

- **Line 161**: `.get("timestamp"`
  ```
  timestamp = item.get("timestamp", "1970-01-01 00:00:00")
  ```

- **Line 208**: `.get("timestamp"`
  ```
  checkin_date = parse_timestamp_full(checkin.get("timestamp", ""))
  ```

### core\scheduler.py
**Issues Found**: 4

- **Line 1391**: `"task_id"`
  ```
  user_id, selected_task["task_id"], random_time
  ```

- **Line 1504**: `"task_id"`
  ```
  str(task.get("task_id") or "").strip(),
  ```

- **Line 1808**: `"task_id"`
  ```
  and kwargs.get("task_id") == task_id
  ```

- **Line 1901**: `"task_id"`
  ```
  task_id = kwargs.get("task_id")
  ```

### core\service.py
**Issues Found**: 2

- **Line 1024**: `"task_id"`
  ```
  task_id = request_data.get("task_id")
  ```

- **Line 1121**: `.get("timestamp"`
  ```
  request_timestamp = request_data.get("timestamp", 0)
  ```

### core\user_data_manager.py
**Issues Found**: 5

- **Line 792**: `.get("timestamp"`
  ```
  return recent_checkins[0].get("timestamp", "1970-01-01 00:00:00")
  ```

- **Line 806**: `.get("timestamp"`
  ```
  return recent_chats[0].get("timestamp", "1970-01-01 00:00:00")
  ```

- **Line 825**: `.get("timestamp"`
  ```
  key=lambda x: x.get("timestamp", "1970-01-01 00:00:00"),
  ```

- **Line 828**: `.get("timestamp"`
  ```
  return sorted_messages[0].get("timestamp", "1970-01-01 00:00:00")
  ```

- **Line 1762**: `.get("timestamp"`
  ```
  data[-1].get("timestamp", "Unknown") if data else "None"
  ```

### core\user_data_read.py
**Issues Found**: 4

- **Line 51**: `"message_id"`
  ```
  if "message_id" not in message or message["message_id"] in existing_ids:
  ```

- **Line 51**: `"message_id"`
  ```
  if "message_id" not in message or message["message_id"] in existing_ids:
  ```

- **Line 52**: `"message_id"`
  ```
  message["message_id"] = str(uuid.uuid4())
  ```

- **Line 53**: `"message_id"`
  ```
  existing_ids.add(message["message_id"])
  ```

### core\user_data_v2.py
**Issues Found**: 4

- **Line 29**: `"task_id"`
  ```
  "task_id",
  ```

- **Line 45**: `"message_id"`
  ```
  "message": {"message_id", "message", "days", "time_periods", "timestamp"},
  ```

- **Line 46**: `"message_id"`
  ```
  "delivery": {"message_id", "message", "delivery_status", "timestamp"},
  ```

- **Line 46**: `"delivery_status"`
  ```
  "delivery": {"message_id", "message", "delivery_status", "timestamp"},
  ```

### core\user_item_storage.py
**Issues Found**: 2

- **Line 53**: `active_tasks.json`
  ```
  Files are created only if missing (e.g. {"active_tasks.json": {"tasks": []}}).
  ```

- **Line 85**: `active_tasks.json`
  ```
  filename: JSON filename (e.g. 'entries.json', 'active_tasks.json').
  ```

### development_tools\functions\analyze_duplicate_functions.py
**Issues Found**: 2

- **Line 658**: `.get("body"`
  ```
  overall += body_score * weights.get("body", 0.0)
  ```

- **Line 685**: `.get("body"`
  ```
  body_weight = float(weights.get("body", 0.0))
  ```

### development_tools\reports\quick_status.py
**Issues Found**: 2

- **Line 126**: `.get("timestamp"`
  ```
  docs["recent_audit"] = audit_data.get("timestamp")
  ```

- **Line 247**: `.get("timestamp"`
  ```
  activity["last_audit"] = audit_data.get("timestamp")
  ```

### development_tools\shared\output_storage.py
**Issues Found**: 1

- **Line 464**: `.get("timestamp"`
  ```
  raw_ts = result_data.get("timestamp") or result_data.get("last_generated")
  ```

### development_tools\shared\service\audit_orchestration.py
**Issues Found**: 2

- **Line 1853**: `.get('timestamp'`
  ```
  'timestamp': result_data.get('timestamp', datetime.now().isoformat())
  ```

- **Line 2162**: `.get("timestamp"`
  ```
  existing_run.get("timestamp")
  ```

### development_tools\shared\service\data_loading.py
**Issues Found**: 2

- **Line 388**: `.get('timestamp'`
  ```
  timestamp = data.get('timestamp', 'Unknown')
  ```

- **Line 505**: `.get('timestamp'`
  ```
  timestamp = meta.get('timestamp')
  ```

### notebook\notebook_data_handlers.py
**Issues Found**: 2

- **Line 169**: `.get("archived"`
  ```
  status = entry.get("status") or ("archived" if entry.get("archived") else "active")
  ```

- **Line 170**: `.get("body"`
  ```
  description = entry.get("body")
  ```

### notebook\notebook_schemas.py
**Issues Found**: 4

- **Line 94**: `.get("body"`
  ```
  if normalized.get("body") is None and normalized.get("description") is not None:
  ```

- **Line 97**: `.get("body"`
  ```
  if normalized.get("description") is None and normalized.get("body") is not None:
  ```

- **Line 99**: `.get("body"`
  ```
  normalized["description"] = normalized.get("body")
  ```

- **Line 102**: `.get("archived"`
  ```
  normalized["status"] = "archived" if normalized.get("archived") else "active"
  ```

### tasks\task_data_handlers.py
**Issues Found**: 3

- **Line 174**: `"task_id"`
  ```
  task_id = str(task.get("id") or task.get("task_id") or "")
  ```

- **Line 242**: `"task_id"`
  ```
  "task_id": task.get("id"),
  ```

- **Line 299**: `"task_id"`
  ```
  "task_id",
  ```

### tasks\task_data_manager.py
**Issues Found**: 2

- **Line 40**: `"task_id"`
  ```
  if task.get("task_id"):
  ```

- **Line 42**: `"task_id"`
  ```
  return str(task.get("task_id"))
  ```

### tasks\task_schemas.py
**Issues Found**: 3

- **Line 35**: `active_tasks.json`
  ```
  ACTIVE_TASKS_FILENAME = "active_tasks.json"
  ```

- **Line 36**: `completed_tasks.json`
  ```
  COMPLETED_TASKS_FILENAME = "completed_tasks.json"
  ```

- **Line 37**: `task_schedules.json`
  ```
  TASK_SCHEDULES_FILENAME = "task_schedules.json"
  ```

### tests\ai\ai_test_base.py
**Issues Found**: 1

- **Line 274**: `.get("timestamp"`
  ```
  if c.get("timestamp", "").startswith(
  ```

### tests\ai\test_ai_integration.py
**Issues Found**: 1

- **Line 94**: `.get("timestamp"`
  ```
  if c.get("timestamp", "").startswith(today_prefix)
  ```

### tests\behavior\test_conversation_flow_manager_behavior.py
**Issues Found**: 1

- **Line 705**: `"task_id"`
  ```
  "data": {"task_id": "task-1"},
  ```

### tests\behavior\test_core_message_management_coverage_expansion.py
**Issues Found**: 2

- **Line 102**: `"message_id"`
  ```
  {"message_id": "a", "timestamp": "2023-02-03T04:05:06Z"},
  ```

- **Line 103**: `"message_id"`
  ```
  {"message_id": "b", "timestamp": "2023-02-03 04:05:06"},
  ```

### tests\behavior\test_discord_bot_behavior.py
**Issues Found**: 1

- **Line 568**: `"task_id"`
  ```
  assert not any(t.get("task_id") == t_id for t in tasks)
  ```

### tests\behavior\test_email_bot_behavior.py
**Issues Found**: 1

- **Line 257**: `'message_id'`
  ```
  assert 'message_id' in messages[0], "Should have message_id field if messages exist"
  ```

### tests\behavior\test_interaction_handlers_behavior.py
**Issues Found**: 2

- **Line 291**: `'task_id'`
  ```
  assert any(task.get('task_id') == task_id for task in tasks), "Task should exist before completion"
  ```

- **Line 310**: `'task_id'`
  ```
  assert not any(task.get('task_id') == task_id for task in tasks), "Task should be removed from active tasks"
  ```

### tests\behavior\test_interaction_handlers_coverage_expansion.py
**Issues Found**: 2

- **Line 1241**: `"task_id"`
  ```
  entities={"task_id": "invalid_task_id", "title": "New Title"},
  ```

- **Line 1264**: `"task_id"`
  ```
  entities={"task_id": "invalid_task_id"},
  ```

### tests\behavior\test_message_analytics_behavior.py
**Issues Found**: 6

- **Line 64**: `"message_id"`
  ```
  "message_id": f"msg-{i}",
  ```

- **Line 68**: `"delivery_status"`
  ```
  "delivery_status": "sent",
  ```

- **Line 167**: `"message_id"`
  ```
  "message_id": f"msg-{i}",
  ```

- **Line 171**: `"delivery_status"`
  ```
  "delivery_status": status,
  ```

- **Line 235**: `"message_id"`
  ```
  "message_id": f"msg-{i}",
  ```

- **Line 239**: `"delivery_status"`
  ```
  "delivery_status": "sent",
  ```

### tests\behavior\test_message_behavior.py
**Issues Found**: 23

- **Line 89**: `'message_id'`
  ```
  'message_id': 'motivational_001'
  ```

- **Line 95**: `'message_id'`
  ```
  'message_id': 'motivational_002'
  ```

- **Line 234**: `"message_id"`
  ```
  "message_id": "test-msg-1",
  ```

- **Line 288**: `"message_id"`
  ```
  "message_id": "test-msg-1",
  ```

- **Line 320**: `"message_id"`
  ```
  "message_id": "test-msg-1",
  ```

- **Line 360**: `"message_id"`
  ```
  "message_id": "test-msg-1",
  ```

- **Line 366**: `"message_id"`
  ```
  "message_id": "test-msg-2",
  ```

- **Line 408**: `"message_id"`
  ```
  "message_id": "test-msg-1",
  ```

- **Line 473**: `"message_id"`
  ```
  {"message_id": "msg1", "message": "Test message 1", "category": category, "timestamp": "2025-01-01 10:00:00", "delivery_status": "sent"},
  ```

- **Line 473**: `"delivery_status"`
  ```
  {"message_id": "msg1", "message": "Test message 1", "category": category, "timestamp": "2025-01-01 10:00:00", "delivery_status": "sent"},
  ```

- **Line 474**: `"message_id"`
  ```
  {"message_id": "msg2", "message": "Test message 2", "category": category, "timestamp": "2025-01-01 11:00:00", "delivery_status": "sent"},
  ```

- **Line 474**: `"delivery_status"`
  ```
  {"message_id": "msg2", "message": "Test message 2", "category": category, "timestamp": "2025-01-01 11:00:00", "delivery_status": "sent"},
  ```

- **Line 475**: `"message_id"`
  ```
  {"message_id": "msg3", "message": "Test message 3", "category": category, "timestamp": "2025-01-01 12:00:00", "delivery_status": "sent"}
  ```

- **Line 475**: `"delivery_status"`
  ```
  {"message_id": "msg3", "message": "Test message 3", "category": category, "timestamp": "2025-01-01 12:00:00", "delivery_status": "sent"}
  ```

- **Line 487**: `'message_id'`
  ```
  assert messages[0]['message_id'] == 'msg3'
  ```

- **Line 488**: `'message_id'`
  ```
  assert messages[1]['message_id'] == 'msg2'
  ```

- **Line 489**: `'message_id'`
  ```
  assert messages[2]['message_id'] == 'msg1'
  ```

- **Line 523**: `"message_id"`
  ```
  "message_id": "msg-good",
  ```

- **Line 545**: `'message_id'`
  ```
  assert messages[0]['message_id'] == 'msg-good'
  ```

- **Line 563**: `"message_id"`
  ```
  {"message_id": "default1", "message": "Default message 1", "days": ["monday"], "time_periods": ["morning"]},
  ```

- **Line 564**: `"message_id"`
  ```
  {"message_id": "default2", "message": "Default message 2", "days": ["tuesday"], "time_periods": ["evening"]}
  ```

- **Line 612**: `"message_id"`
  ```
  message_data = {"message_id": "test_msg", "message": "Test message", "days": ["monday"], "time_periods": ["morning"]}
  ```

- **Line 629**: `"message_id"`
  ```
  updated_data = {"message_id": "test_msg", "message": "Updated message", "days": ["monday"], "time_periods": ["morning"]}
  ```

### tests\behavior\test_notebook_handler_behavior.py
**Issues Found**: 2

- **Line 995**: `.get("body"`
  ```
  body = result.parsed_command.entities.get("body", "").lower()
  ```

- **Line 1009**: `.get("body"`
  ```
  body = result.parsed_command.entities.get("body", "").lower()
  ```

### tests\behavior\test_quantitative_analytics_expansion.py
**Issues Found**: 3

- **Line 33**: `.get("timestamp"`
  ```
  "submitted_at": checkin.get("timestamp"),
  ```

- **Line 42**: `.get("timestamp"`
  ```
  "created_at": checkin.get("timestamp"),
  ```

- **Line 43**: `.get("timestamp"`
  ```
  "updated_at": checkin.get("timestamp"),
  ```

### tests\behavior\test_scheduler_coverage_expansion.py
**Issues Found**: 11

- **Line 424**: `"task_id"`
  ```
  "task_id": "task-1",
  ```

- **Line 429**: `"task_id"`
  ```
  "task_id": "task-2",
  ```

- **Line 495**: `"task_id"`
  ```
  "task_id": task_id,
  ```

- **Line 523**: `"task_id"`
  ```
  "task_id": task_id,
  ```

- **Line 800**: `"task_id"`
  ```
  "task_id": task_id,
  ```

- **Line 827**: `"task_id"`
  ```
  "task_id": task_id,
  ```

- **Line 1380**: `"task_id"`
  ```
  {"task_id": "task1", "completed": False, "title": "Test Task 1"},
  ```

- **Line 1381**: `"task_id"`
  ```
  {"task_id": "task2", "completed": False, "title": "Test Task 2"},
  ```

- **Line 1385**: `"task_id"`
  ```
  mock_select_task.return_value = {"task_id": "task1", "title": "Test Task 1"}
  ```

- **Line 1453**: `"task_id"`
  ```
  {"task_id": "task1", "completed": False, "title": "Test Task 1"}
  ```

- **Line 1456**: `"task_id"`
  ```
  mock_select_task.return_value = {"task_id": "task1", "title": "Test Task 1"}
  ```

### tests\behavior\test_task_behavior.py
**Issues Found**: 10

- **Line 77**: `active_tasks.json`
  ```
  assert not os.path.exists(os.path.join(task_dir, "active_tasks.json"))
  ```

- **Line 78**: `completed_tasks.json`
  ```
  assert not os.path.exists(os.path.join(task_dir, "completed_tasks.json"))
  ```

- **Line 79**: `task_schedules.json`
  ```
  assert not os.path.exists(os.path.join(task_dir, "task_schedules.json"))
  ```

- **Line 109**: `"task_id"`
  ```
  {"task_id": "1", "title": "Test Task 1", "completed": False},
  ```

- **Line 110**: `"task_id"`
  ```
  {"task_id": "2", "title": "Test Task 2", "completed": False},
  ```

- **Line 128**: `"task_id"`
  ```
  assert all("task_id" not in task for task in saved_data["tasks"])
  ```

- **Line 237**: `"task_id"`
  ```
  assert all(t["task_id"] != task_id for t in tasks)
  ```

- **Line 255**: `"task_id"`
  ```
  assert task["task_id"] == task_id
  ```

- **Line 291**: `"task_id"`
  ```
  assert any(t["task_id"] == id_soon for t in due_soon_tasks)
  ```

- **Line 292**: `"task_id"`
  ```
  assert all(t["task_id"] != id_late for t in due_soon_tasks)
  ```

### tests\behavior\test_task_crud_disambiguation.py
**Issues Found**: 14

- **Line 24**: `"task_id"`
  ```
  tasks.append({"title": "Wash dishes", "task_id": "tdishes"})
  ```

- **Line 25**: `"task_id"`
  ```
  tasks.append({"title": "Wash laundry", "task_id": "tlaundry"})
  ```

- **Line 41**: `"task_id"`
  ```
  tasks.append({"title": "Task A", "task_id": "taskaaaa"})
  ```

- **Line 42**: `"task_id"`
  ```
  tasks.append({"title": "Task B", "task_id": "taskbbbb"})
  ```

- **Line 56**: `"task_id"`
  ```
  tasks.append({"title": "Brush teeth", "task_id": "teeth123"})
  ```

- **Line 76**: `"task_id"`
  ```
  tasks.append({"title": "Wash dishes", "task_id": "wash0001"})
  ```

- **Line 83**: `'task_id'`
  ```
  updated = [t for t in tasks2 if t.get('task_id') == 'wash0001']
  ```

- **Line 91**: `"task_id"`
  ```
  tasks.append({"title": "Change me", "task_id": "chg001"})
  ```

- **Line 106**: `"task_id"`
  ```
  tasks.append({"title": "Take a walk", "task_id": "walk001"})
  ```

- **Line 122**: `"task_id"`
  ```
  tasks.append({"title": "Wash dishes", "task_id": "washA"})
  ```

- **Line 123**: `"task_id"`
  ```
  tasks.append({"title": "Wash laundry", "task_id": "washB"})
  ```

- **Line 136**: `"task_id"`
  ```
  tasks.append({"title": "Rename me", "task_id": "rename01"})
  ```

- **Line 142**: `'task_id'`
  ```
  t1 = [t for t in tasks1 if t.get('task_id') == 'rename01'][0]
  ```

- **Line 150**: `'task_id'`
  ```
  still_exists = any(t.get('task_id') == 'rename01' for t in tasks_after)
  ```

### tests\behavior\test_task_error_handling.py
**Issues Found**: 1

- **Line 234**: `active_tasks.json`
  ```
  task_file = user_dir / "tasks" / "active_tasks.json"
  ```

### tests\behavior\test_task_handler_behavior.py
**Issues Found**: 22

- **Line 352**: `"task_id"`
  ```
  "task_id": "task_1",
  ```

- **Line 358**: `"task_id"`
  ```
  "task_id": "task_2",
  ```

- **Line 434**: `"task_id"`
  ```
  "task_id": "task_1",
  ```

- **Line 442**: `"task_id"`
  ```
  "task_id": "task_2",
  ```

- **Line 477**: `"task_id"`
  ```
  {"title": "Task 1", "priority": "high", "task_id": "task_1"},
  ```

- **Line 478**: `"task_id"`
  ```
  {"title": "Task 2", "priority": "medium", "task_id": "task_2"},
  ```

- **Line 518**: `"task_id"`
  ```
  {"title": "Task 1", "priority": "high", "task_id": "task_1"}
  ```

- **Line 574**: `"task_id"`
  ```
  {"title": "Task 1", "priority": "high", "task_id": "task_1"}
  ```

- **Line 617**: `"task_id"`
  ```
  {"title": "Task 1", "priority": "medium", "task_id": "task_1"}
  ```

- **Line 641**: `"task_id"`
  ```
  call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("task_id")
  ```

- **Line 670**: `"task_id"`
  ```
  {"title": "Task 1", "priority": "medium", "task_id": "task_1"}
  ```

- **Line 707**: `"completed_tasks"`
  ```
  "completed_tasks": 10,
  ```

- **Line 751**: `"task_id"`
  ```
  {"title": "Task 1", "task_id": "task_1"},
  ```

- **Line 752**: `"task_id"`
  ```
  {"title": "Task 2", "task_id": "task_2"},
  ```

- **Line 753**: `"task_id"`
  ```
  {"title": "Task 3", "task_id": "task_3"},
  ```

- **Line 767**: `"task_id"`
  ```
  {"title": "Brush Teeth", "task_id": "task_1"},
  ```

- **Line 768**: `"task_id"`
  ```
  {"title": "Wash Dishes", "task_id": "task_2"},
  ```

- **Line 782**: `"task_id"`
  ```
  {"title": "Brush Teeth Every Morning", "task_id": "task_1"},
  ```

- **Line 783**: `"task_id"`
  ```
  {"title": "Wash Dishes After Dinner", "task_id": "task_2"},
  ```

- **Line 797**: `"task_id"`
  ```
  {"title": "Task 1", "task_id": "task_123"},
  ```

- **Line 798**: `"task_id"`
  ```
  {"title": "Task 2", "task_id": "task_456"},
  ```

- **Line 803**: `"task_id"`
  ```
  assert task["task_id"] == "task_123", "Should find correct task"
  ```

### tests\behavior\test_task_management_coverage_expansion.py
**Issues Found**: 24

- **Line 98**: `active_tasks.json`
  ```
  assert not (task_dir / "active_tasks.json").exists()
  ```

- **Line 99**: `completed_tasks.json`
  ```
  assert not (task_dir / "completed_tasks.json").exists()
  ```

- **Line 100**: `task_schedules.json`
  ```
  assert not (task_dir / "task_schedules.json").exists()
  ```

- **Line 128**: `active_tasks.json`
  ```
  "active_tasks.json": {"tasks": [{"existing": "task"}]},
  ```

- **Line 129**: `completed_tasks.json`
  ```
  "completed_tasks.json": {"completed_tasks": []},
  ```

- **Line 129**: `"completed_tasks"`
  ```
  "completed_tasks.json": {"completed_tasks": []},
  ```

- **Line 130**: `task_schedules.json`
  ```
  "task_schedules.json": {"task_schedules": {}},
  ```

- **Line 144**: `active_tasks.json`
  ```
  active_file = task_dir / "active_tasks.json"
  ```

- **Line 184**: `active_tasks.json`
  ```
  active_file = task_dir / "active_tasks.json"
  ```

- **Line 204**: `"task_id"`
  ```
  {"task_id": "1", "title": "Task 1", "completed": False},
  ```

- **Line 205**: `"task_id"`
  ```
  {"task_id": "2", "title": "Task 2", "completed": False},
  ```

- **Line 221**: `active_tasks.json`
  ```
  assert not (task_dir / "active_tasks.json").exists()
  ```

- **Line 257**: `"task_id"`
  ```
  {"task_id": "1", "title": "Completed Task 1", "completed": True},
  ```

- **Line 258**: `"task_id"`
  ```
  {"task_id": "2", "title": "Completed Task 2", "completed": True},
  ```

- **Line 277**: `completed_tasks.json`
  ```
  assert not (task_dir / "completed_tasks.json").exists()
  ```

- **Line 308**: `"task_id"`
  ```
  assert task["task_id"] == task_id
  ```

- **Line 428**: `"task_id"`
  ```
  "task_id": "new-id",  # Disallowed - should be skipped
  ```

- **Line 441**: `"task_id"`
  ```
  assert task["task_id"] == task_id  # Disallowed field not updated
  ```

- **Line 718**: `"task_id"`
  ```
  assert active_tasks[0]["task_id"] == task_id
  ```

- **Line 874**: `"task_id"`
  ```
  assert all(task["task_id"] != task_id for task in tasks)
  ```

- **Line 893**: `"task_id"`
  ```
  assert task["task_id"] == task_id
  ```

- **Line 909**: `"task_id"`
  ```
  assert task["task_id"] == task_id
  ```

- **Line 937**: `"task_id"`
  ```
  task_ids = [task["task_id"] for task in due_soon_tasks]
  ```

- **Line 981**: `"task_id"`
  ```
  task_ids = [task["task_id"] for task in due_soon_tasks]
  ```

### tests\behavior\test_task_reminder_followup_behavior.py
**Issues Found**: 2

- **Line 65**: `"task_id"`
  ```
  "task_id" in conversation_manager.user_states[user_id]["data"]
  ```

- **Line 69**: `"task_id"`
  ```
  task_id = conversation_manager.user_states[user_id]["data"]["task_id"]
  ```

### tests\behavior\test_task_suggestion_relevance.py
**Issues Found**: 8

- **Line 31**: `"task_id"`
  ```
  tasks.append({"title": "Test Task", "task_id": "test001"})
  ```

- **Line 67**: `"task_id"`
  ```
  tasks.append({"title": "Task One", "task_id": "task001"})
  ```

- **Line 68**: `"task_id"`
  ```
  tasks.append({"title": "Task Two", "task_id": "task002"})
  ```

- **Line 100**: `"task_id"`
  ```
  tasks.append({"title": "My Task", "task_id": "mytask01"})
  ```

- **Line 121**: `"task_id"`
  ```
  tasks.append({"title": "Test Due Task", "task_id": "duetest01"})
  ```

- **Line 133**: `'task_id'`
  ```
  task = next((t for t in tasks_after if t.get('task_id') == 'duetest01'), None)
  ```

- **Line 147**: `"task_id"`
  ```
  tasks.append({"title": "Test Due Date Task", "task_id": "duedatetest01"})
  ```

- **Line 158**: `'task_id'`
  ```
  task = next((t for t in tasks_after if t.get('task_id') == 'duedatetest01'), None)
  ```

### tests\core\test_message_management.py
**Issues Found**: 5

- **Line 107**: `"message_id"`
  ```
  "message_id": "m1",
  ```

- **Line 135**: `"message_id"`
  ```
  "message_id": "old",
  ```

- **Line 141**: `"message_id"`
  ```
  "message_id": "new",
  ```

- **Line 166**: `"message_id"`
  ```
  assert archived["messages"][0]["message_id"] == "old"
  ```

- **Line 170**: `"message_id"`
  ```
  assert active["messages"][0]["message_id"] == "new"
  ```

### tests\core\test_service_request_helpers.py
**Issues Found**: 1

- **Line 140**: `"task_id"`
  ```
  json.dumps({"user_id": "user-1", "task_id": "task-1"}),
  ```

### tests\core\test_user_data_read_scenarios.py
**Issues Found**: 6

- **Line 40**: `"message_id"`
  ```
  {"message_id": "dup", "body": "a"},
  ```

- **Line 41**: `"message_id"`
  ```
  {"message_id": "dup", "body": "b"},
  ```

- **Line 47**: `"message_id"`
  ```
  ids = [m["message_id"] for m in out["messages"]]
  ```

- **Line 137**: `"message_id"`
  ```
  {"message_id": "duplicate-id", "body": "first"},
  ```

- **Line 138**: `"message_id"`
  ```
  {"message_id": "duplicate-id", "body": "second"},
  ```

- **Line 149**: `"message_id"`
  ```
  ids = [m.get("message_id") for m in reloaded["messages"]]
  ```

### tests\integration\test_orphaned_reminder_cleanup.py
**Issues Found**: 9

- **Line 105**: `"task_id"`
  ```
  and kwargs.get("task_id") == task_id
  ```

- **Line 167**: `completed_tasks.json`
  ```
  # Note: completed tasks are moved to completed_tasks.json, so get_task_by_id might return None
  ```

- **Line 172**: `"task_id"`
  ```
  active_task_ids = [t.get("task_id") for t in active_tasks]
  ```

- **Line 191**: `"task_id"`
  ```
  and kwargs.get("task_id") == task_id
  ```

- **Line 256**: `"task_id"`
  ```
  and (_kw(job) or {}).get("task_id") == task_id
  ```

- **Line 269**: `"task_id"`
  ```
  and (_kw(job) or {}).get("task_id") == task_id
  ```

- **Line 358**: `"task_id"`
  ```
  _kw(job).get("user_id") == user1_id and _kw(job).get("task_id") == task1_id
  ```

- **Line 365**: `"task_id"`
  ```
  _kw(job).get("user_id") == user2_id and _kw(job).get("task_id") == task2_id
  ```

- **Line 375**: `"task_id"`
  ```
  "task_id"
  ```

### tests\integration\test_task_cleanup_real.py
**Issues Found**: 10

- **Line 54**: `'task_id'`
  ```
  assert any(t['task_id'] == task_id for t in active_before), "Task should be in active_tasks"
  ```

- **Line 57**: `'task_id'`
  ```
  assert not any(t['task_id'] == task_id for t in completed_before), "Task should not be in completed_tasks"
  ```

- **Line 74**: `'task_id'`
  ```
  assert not any(t['task_id'] == task_id for t in active_after), "Task should be removed from active_tasks"
  ```

- **Line 77**: `'task_id'`
  ```
  assert any(t['task_id'] == task_id for t in completed_after), "Task should be in completed_tasks"
  ```

- **Line 80**: `'task_id'`
  ```
  completed_task = next(t for t in completed_after if t['task_id'] == task_id)
  ```

- **Line 89**: `completed_tasks.json`
  ```
  assert not (user_dir / "tasks" / "completed_tasks.json").exists()
  ```

- **Line 122**: `'task_id'`
  ```
  assert any(t['task_id'] == task_id for t in active_before), "Task should exist before deletion"
  ```

- **Line 139**: `'task_id'`
  ```
  assert not any(t['task_id'] == task_id for t in active_after), "Task should be removed from active_tasks"
  ```

- **Line 143**: `'task_id'`
  ```
  assert not any(t['task_id'] == task_id for t in completed_after), "Task should not be in completed_tasks"
  ```

- **Line 154**: `active_tasks.json`
  ```
  assert not (user_dir / "tasks" / "active_tasks.json").exists()
  ```

### tests\test_helpers\test_support\conftest_mocks.py
**Issues Found**: 3

- **Line 53**: `"task_id"`
  ```
  "task_id": "test-task-123",
  ```

- **Line 68**: `"message_id"`
  ```
  "message_id": "test-message-123",
  ```

- **Line 94**: `"message_id"`
  ```
  "message_id": "test-msg-123",
  ```

### tests\test_helpers\test_utilities\test_data_factory.py
**Issues Found**: 2

- **Line 121**: `"task_id"`
  ```
  "task_id": str(uuid.uuid4()),
  ```

- **Line 154**: `"message_id"`
  ```
  "message_id": str(uuid.uuid4()),
  ```

### tests\ui\test_dialog_coverage_expansion.py
**Issues Found**: 2

- **Line 284**: `'task_id'`
  ```
  'task_id': 'task1',  # Changed from 'id' to 'task_id'
  ```

- **Line 284**: `'task_id'`
  ```
  'task_id': 'task1',  # Changed from 'id' to 'task_id'
  ```

### tests\ui\test_message_editor_dialog.py
**Issues Found**: 9

- **Line 80**: `'message_id'`
  ```
  'message_id': 'test_message_id',
  ```

- **Line 287**: `'message_id'`
  ```
  'message_id': 'test_message_id',
  ```

- **Line 328**: `'message_id'`
  ```
  assert 'message_id' in message_data, "Should include message_id"
  ```

- **Line 405**: `'message_id'`
  ```
  'message_id': 'msg1',
  ```

- **Line 411**: `'message_id'`
  ```
  'message_id': 'msg2',
  ```

- **Line 510**: `'message_id'`
  ```
  'message_id': 'msg1',
  ```

- **Line 532**: `'message_id'`
  ```
  'message_id': 'msg2',
  ```

- **Line 545**: `'message_id'`
  ```
  assert dialog.messages[0]['message_id'] == 'msg2', "Should load new message"
  ```

- **Line 598**: `'message_id'`
  ```
  message_id = dialog.messages[0].get('message_id')
  ```

### tests\ui\test_task_crud_dialog.py
**Issues Found**: 9

- **Line 47**: `'task_id'`
  ```
  'task_id': 'task1',
  ```

- **Line 57**: `'task_id'`
  ```
  'task_id': 'task2',
  ```

- **Line 67**: `'completed_tasks'`
  ```
  'completed_tasks': [
  ```

- **Line 69**: `'task_id'`
  ```
  'task_id': 'task3',
  ```

- **Line 151**: `'completed_tasks'`
  ```
  mock_load_completed.return_value = mock_task_data['completed_tasks']
  ```

- **Line 230**: `'completed_tasks'`
  ```
  mock_load_completed.return_value = mock_task_data['completed_tasks']
  ```

- **Line 478**: `'completed_tasks'`
  ```
  mock_load_completed.return_value = mock_task_data['completed_tasks']
  ```

- **Line 530**: `'completed_tasks'`
  ```
  mock_load_completed.return_value = mock_task_data['completed_tasks']
  ```

- **Line 556**: `'completed_tasks'`
  ```
  mock_load_completed.return_value = mock_task_data['completed_tasks']
  ```

### tests\unit\test_channel_orchestrator.py
**Issues Found**: 7

- **Line 124**: `'task_id'`
  ```
  'task_id': 'task_123'
  ```

- **Line 141**: `'task_id'`
  ```
  'task_id': 'task_1'
  ```

- **Line 401**: `"task_id"`
  ```
  "task_id": task_id,
  ```

- **Line 435**: `"task_id"`
  ```
  "task_id": task_id,
  ```

- **Line 471**: `"task_id"`
  ```
  task = {"task_id": "task_done", "title": "Done", "completed": True}
  ```

- **Line 483**: `"task_id"`
  ```
  task = {"task_id": "task_ok", "title": "Active task", "completed": False}
  ```

- **Line 499**: `"task_id"`
  ```
  task = {"task_id": "task_ok", "title": "Active task", "completed": False}
  ```

### tests\unit\test_channel_orchestrator_message_selection.py
**Issues Found**: 3

- **Line 72**: `"message_id"`
  ```
  message = {"message_id": "m1", "message": "Hello world"}
  ```

- **Line 108**: `"message_id"`
  ```
  data = {"messages": [{"message": "x", "message_id": "m1", "days": ["MONDAY"], "time_periods": ["morning"]}]}
  ```

- **Line 123**: `"message_id"`
  ```
  data = {"messages": [{"message": "x", "message_id": "m1", "days": ["MONDAY"], "time_periods": ["morning"]}]}
  ```

### tests\unit\test_command_parser_notebook_entities_expansion.py
**Issues Found**: 3

- **Line 66**: `.get("body"`
  ```
  assert entities.get("body") == expected_body
  ```

- **Line 85**: `.get("body"`
  ```
  assert entities.get("body") is None
  ```

- **Line 273**: `.get("body"`
  ```
  assert entities.get("body") == expected_text
  ```

### tests\unit\test_conversation_flow_reminder_helpers.py
**Issues Found**: 1

- **Line 88**: `"task_id"`
  ```
  with patch("tasks.get_task_by_id", return_value={"task_id": "t1"}):
  ```

### tests\unit\test_interaction_handlers_helpers.py
**Issues Found**: 34

- **Line 377**: `"task_id"`
  ```
  {"task_id": "abc123", "title": "Task 1"},
  ```

- **Line 378**: `"task_id"`
  ```
  {"task_id": "def456", "title": "Task 2"},
  ```

- **Line 388**: `"task_id"`
  ```
  {"task_id": "abcdef1234567890", "title": "Task 1"},
  ```

- **Line 389**: `"task_id"`
  ```
  {"task_id": "def4567890123456", "title": "Task 2"},
  ```

- **Line 399**: `"task_id"`
  ```
  {"task_id": "abc123", "title": "Task 1"},
  ```

- **Line 400**: `"task_id"`
  ```
  {"task_id": "def456", "title": "Task 2"},
  ```

- **Line 410**: `"task_id"`
  ```
  {"task_id": "abc123", "title": "Buy groceries"},
  ```

- **Line 411**: `"task_id"`
  ```
  {"task_id": "def456", "title": "Call mom"},
  ```

- **Line 421**: `"task_id"`
  ```
  {"task_id": "abc123", "title": "Buy groceries"},
  ```

- **Line 422**: `"task_id"`
  ```
  {"task_id": "def456", "title": "Buy milk"},
  ```

- **Line 434**: `"task_id"`
  ```
  {"task_id": "abc123", "title": "Task 1"},
  ```

- **Line 435**: `"task_id"`
  ```
  {"task_id": "def456", "title": "Task 2"},
  ```

- **Line 444**: `"task_id"`
  ```
  {"task_id": "abc123", "title": "Task 1"},
  ```

- **Line 445**: `"task_id"`
  ```
  {"task_id": "def456", "title": "Task 2"},
  ```

- **Line 455**: `"task_id"`
  ```
  {"task_id": "abcdef1234567890", "title": "Task 1"},
  ```

- **Line 456**: `"task_id"`
  ```
  {"task_id": "def4567890123456", "title": "Task 2"},
  ```

- **Line 466**: `"task_id"`
  ```
  {"task_id": "abc123", "title": "Task 1"},
  ```

- **Line 467**: `"task_id"`
  ```
  {"task_id": "def456", "title": "Task 2"},
  ```

- **Line 477**: `"task_id"`
  ```
  {"task_id": "abc123", "title": "Buy groceries"},
  ```

- **Line 478**: `"task_id"`
  ```
  {"task_id": "def456", "title": "Call mom"},
  ```

- **Line 488**: `"task_id"`
  ```
  {"task_id": "abc123", "title": "Buy groceries"},
  ```

- **Line 489**: `"task_id"`
  ```
  {"task_id": "def456", "title": "Call mom"},
  ```

- **Line 499**: `"task_id"`
  ```
  {"task_id": "abc123", "title": "Task 1"},
  ```

- **Line 500**: `"task_id"`
  ```
  {"task_id": "def456", "title": "Task 2"},
  ```

- **Line 525**: `"task_id"`
  ```
  "task_id": "abc123",
  ```

- **Line 531**: `"task_id"`
  ```
  "task_id": "def456",
  ```

- **Line 560**: `"task_id"`
  ```
  "task_id": "abc123",
  ```

- **Line 566**: `"task_id"`
  ```
  "task_id": "def456",
  ```

- **Line 596**: `"task_id"`
  ```
  "task_id": "abc123",
  ```

- **Line 602**: `"task_id"`
  ```
  "task_id": "def456",
  ```

- **Line 622**: `"task_id"`
  ```
  "task_id": "abc123",
  ```

- **Line 639**: `"task_id"`
  ```
  "task_id": "abc123",
  ```

- **Line 654**: `"task_id"`
  ```
  "task_id": "abc123",
  ```

- **Line 667**: `"task_id"`
  ```
  {"task_id": f"abc{i}", "title": f"Task {i}", "priority": "medium"}
  ```

### tests\unit\test_notebook_validation.py
**Issues Found**: 3

- **Line 453**: `'kind': 'journal'`
  ```
  {'title': 'Journal Entry', 'body': 'Journal body', 'kind': 'journal'},
  ```

- **Line 459**: `.get('body'`
  ```
  body=content.get('body'),
  ```

- **Line 484**: `.get('body'`
  ```
  body=content.get('body'),
  ```

### tests\unit\test_notebook_validation_error_handling.py
**Issues Found**: 1

- **Line 145**: `.get('body'`
  ```
  body=case.get('body'),
  ```

### tests\unit\test_recurring_tasks.py
**Issues Found**: 6

- **Line 44**: `active_tasks.json`
  ```
  active_tasks_file = os.path.join(tasks_dir, 'active_tasks.json')
  ```

- **Line 45**: `completed_tasks.json`
  ```
  completed_tasks_file = os.path.join(tasks_dir, 'completed_tasks.json')
  ```

- **Line 50**: `"completed_tasks"`
  ```
  f.write('{"completed_tasks": []}')
  ```

- **Line 110**: `'task_id'`
  ```
  assert completed_tasks[0]['task_id'] == task_id
  ```

- **Line 118**: `'task_id'`
  ```
  assert new_task['task_id'] != task_id  # Different task ID
  ```

- **Line 208**: `'task_id'`
  ```
  assert completed_tasks[0]['task_id'] == task_id
  ```

### tests\unit\test_schema_validation_helpers.py
**Issues Found**: 5

- **Line 101**: `"message_id"`
  ```
  "message_id": "1",
  ```

- **Line 108**: `"message_id"`
  ```
  "message_id": "2",
  ```

- **Line 113**: `"message_id"`
  ```
  {"message_id": "3"},
  ```

- **Line 123**: `"message_id"`
  ```
  "message_id": "1",
  ```

- **Line 130**: `"message_id"`
  ```
  "message_id": "2",
  ```

### tests\unit\test_schemas_validation.py
**Issues Found**: 2

- **Line 112**: `"message_id"`
  ```
  {"message_id": "1", "message": "Hello!", "days": [], "time_periods": []},
  ```

- **Line 122**: `"message_id"`
  ```
  {"message_id": "1", "message": "Hello!", "days": ["ALL"], "time_periods": ["ALL"], "timestamp": None}
  ```

### tests\unit\test_user_data_v2_migration.py
**Issues Found**: 31

- **Line 31**: `"task_id"`
  ```
  "task_id": "11111111-1111-4111-8111-111111111111",
  ```

- **Line 44**: `"completed_tasks"`
  ```
  "completed_tasks": [
  ```

- **Line 46**: `"task_id"`
  ```
  "task_id": "22222222-2222-4222-8222-222222222222",
  ```

- **Line 71**: `"task_id"`
  ```
  assert "task_id" not in active_task
  ```

- **Line 85**: `"kind": "journal"`
  ```
  "kind": "journal",
  ```

- **Line 141**: `"message_id"`
  ```
  "message_id": "template-1",
  ```

- **Line 155**: `"message_id"`
  ```
  "message_id": "template-1",
  ```

- **Line 158**: `"delivery_status"`
  ```
  "delivery_status": "sent",
  ```

- **Line 176**: `"delivery_status"`
  ```
  assert "delivery_status" not in delivery
  ```

- **Line 178**: `"message_id"`
  ```
  assert set(template_report["fields_renamed"]) == {"days", "message", "message_id", "time_periods", "timestamp"}
  ```

- **Line 180**: `"message_id"`
  ```
  assert set(delivery_report["fields_renamed"]) == {"delivery_status", "message", "message_id", "timestamp"}
  ```

- **Line 180**: `"delivery_status"`
  ```
  assert set(delivery_report["fields_renamed"]) == {"delivery_status", "message", "message_id", "timestamp"}
  ```

- **Line 206**: `"task_id"`
  ```
  "task_id": "legacy",
  ```

- **Line 225**: `"task_id"`
  ```
  assert "task_id" in errors[0]
  ```

- **Line 235**: `active_tasks.json`
  ```
  (user_root / "tasks" / "active_tasks.json").write_text(
  ```

- **Line 236**: `"task_id"`
  ```
  json.dumps({"tasks": [{"task_id": "task-1", "title": "Plan", "created_at": TIMESTAMP}]}),
  ```

- **Line 239**: `completed_tasks.json`
  ```
  (user_root / "tasks" / "completed_tasks.json").write_text(
  ```

- **Line 240**: `"completed_tasks"`
  ```
  json.dumps({"completed_tasks": []}),
  ```

- **Line 243**: `task_schedules.json`
  ```
  (user_root / "tasks" / "task_schedules.json").write_text(
  ```

- **Line 269**: `active_tasks.json`
  ```
  assert not (user_root / "tasks" / "active_tasks.json").exists()
  ```

- **Line 270**: `completed_tasks.json`
  ```
  assert not (user_root / "tasks" / "completed_tasks.json").exists()
  ```

- **Line 271**: `task_schedules.json`
  ```
  assert not (user_root / "tasks" / "task_schedules.json").exists()
  ```

- **Line 275**: `active_tasks.json`
  ```
  assert "tasks/active_tasks.json" in written["files_removed"]
  ```

- **Line 320**: `"message_id"`
  ```
  "message_id": "template-1",
  ```

- **Line 365**: `"message_id"`
  ```
  assert messages[0]["message_id"] == "template-1"
  ```

- **Line 505**: `"task_id"`
  ```
  assert active[0]["task_id"] == "task-active"
  ```

- **Line 507**: `"task_id"`
  ```
  assert completed[0]["task_id"] == "task-completed"
  ```

- **Line 514**: `"task_id"`
  ```
  "task_id": "task-new",
  ```

- **Line 525**: `"task_id"`
  ```
  assert "task_id" not in data["tasks"][0]
  ```

- **Line 526**: `active_tasks.json`
  ```
  assert not (tasks_dir / "active_tasks.json").exists()
  ```

- **Line 527**: `completed_tasks.json`
  ```
  assert not (tasks_dir / "completed_tasks.json").exists()
  ```

### ui\ui_app_qt.py
**Issues Found**: 2

- **Line 2265**: `"task_id"`
  ```
  task_id = selected_task.get("task_id")
  ```

- **Line 2291**: `"task_id"`
  ```
  "task_id": task_id,
  ```
