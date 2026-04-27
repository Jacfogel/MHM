# Legacy Reference Cleanup Report

> **File**: `development_docs/LEGACY_REFERENCE_REPORT.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2026-04-27 03:22:51
> **Source**: `python development_tools/generate_legacy_reference_report.py` - Legacy Reference Report Generator
**Total Files with Issues**: 68
**Legacy Compatibility Markers Detected**: 470

## Summary
- Scan mode only: no automated fixes were applied.
- Changelogs, archive folders, and planning documents are intentionally historical and excluded from this report.

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
- Current inventory-term hits in scan: 0 file(s), 0 marker(s)

## User Data V1 Runtime Adapters
**Files Affected**: 68

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

- **Line 760**: `.get("timestamp"`
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
**Issues Found**: 25

- **Line 39**: `"message_id"`
  ```
  "message_id": message.get("id") or message.get("message_id"),
  ```

- **Line 39**: `"message_id"`
  ```
  "message_id": message.get("id") or message.get("message_id"),
  ```

- **Line 52**: `"message_id"`
  ```
  "message_id": delivery.get("message_template_id") or delivery.get("message_id"),
  ```

- **Line 52**: `"message_id"`
  ```
  "message_id": delivery.get("message_template_id") or delivery.get("message_id"),
  ```

- **Line 55**: `.get("timestamp"`
  ```
  "timestamp": delivery.get("sent_at") or delivery.get("timestamp", ""),
  ```

- **Line 56**: `"delivery_status"`
  ```
  "delivery_status": delivery.get("status") or delivery.get("delivery_status", ""),
  ```

- **Line 56**: `"delivery_status"`
  ```
  "delivery_status": delivery.get("status") or delivery.get("delivery_status", ""),
  ```

- **Line 222**: `"message_id"`
  ```
  if "message_id" not in message_data:
  ```

- **Line 223**: `"message_id"`
  ```
  message_data["message_id"] = str(uuid.uuid4())
  ```

- **Line 279**: `"message_id"`
  ```
  if msg["message_id"] == message_id
  ```

- **Line 332**: `"message_id"`
  ```
  if msg.get("message_id") == message_id:
  ```

- **Line 372**: `"message_id"`
  ```
  (msg for msg in data["messages"] if msg["message_id"] == message_id), None
  ```

- **Line 448**: `"message_id"`
  ```
  msg.get("message_id"): msg.get("category")
  ```

- **Line 450**: `"message_id"`
  ```
  if isinstance(msg, dict) and msg.get("message_id")
  ```

- **Line 454**: `"message_id"`
  ```
  category_value = id_to_category.get(message.get("message_id"))
  ```

- **Line 489**: `.get("timestamp"`
  ```
  if _parse_message_timestamp(msg.get("timestamp", "")) >= cutoff_date
  ```

- **Line 494**: `.get("timestamp"`
  ```
  key=lambda msg: _parse_message_timestamp(msg.get("timestamp", "")), reverse=True
  ```

- **Line 548**: `"message_id"`
  ```
  "message_id": message_id,
  ```

- **Line 553**: `"delivery_status"`
  ```
  "delivery_status": delivery_status,
  ```

- **Line 597**: `.get("timestamp"`
  ```
  existing_timestamp = _parse_message_timestamp(existing_msg.get("timestamp", ""))
  ```

- **Line 667**: `.get("timestamp"`
  ```
  message_timestamp = _parse_message_timestamp(message.get("timestamp", ""))
  ```

- **Line 694**: `.get("timestamp"`
  ```
  msg.get("timestamp", "") for msg in archived_messages
  ```

- **Line 697**: `.get("timestamp"`
  ```
  msg.get("timestamp", "") for msg in archived_messages
  ```

- **Line 776**: `.get("timestamp"`
  ```
  timestamp_value = message.get("timestamp", "")
  ```

- **Line 958**: `.get("timestamp"`
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
**Issues Found**: 21

- **Line 44**: `"task_id"`
  ```
  "task_id",
  ```

- **Line 60**: `"message_id"`
  ```
  "message": {"message_id", "message", "days", "time_periods", "timestamp"},
  ```

- **Line 61**: `"message_id"`
  ```
  "delivery": {"message_id", "message", "delivery_status", "timestamp"},
  ```

- **Line 61**: `"delivery_status"`
  ```
  "delivery": {"message_id", "message", "delivery_status", "timestamp"},
  ```

- **Line 387**: `"completed_tasks"`
  ```
  for item in _list_from_wrapper(completed_data, "completed_tasks"):
  ```

- **Line 390**: `task_schedules.json`
  ```
  _append_report_field(report, "fields_moved_to_metadata", "task_schedules.json:task_schedules")
  ```

- **Line 526**: `active_tasks.json`
  ```
  _read_json(root / "tasks" / "active_tasks.json"),
  ```

- **Line 527**: `completed_tasks.json`
  ```
  _read_json(root / "tasks" / "completed_tasks.json"),
  ```

- **Line 528**: `task_schedules.json`
  ```
  _read_json(root / "tasks" / "task_schedules.json"),
  ```

- **Line 572**: `active_tasks.json`
  ```
  "tasks/active_tasks.json",
  ```

- **Line 573**: `completed_tasks.json`
  ```
  "tasks/completed_tasks.json",
  ```

- **Line 574**: `task_schedules.json`
  ```
  "tasks/task_schedules.json",
  ```

- **Line 597**: `"task_id"`
  ```
  old_id = str(item.get("task_id") or item.get("id") or uuid4())
  ```

- **Line 653**: `.get("archived"`
  ```
  archived = bool(item.get("archived", False))
  ```

- **Line 659**: `.get("body"`
  ```
  "description": str(item.get("description") or item.get("body") or ""),
  ```

- **Line 683**: `.get("timestamp"`
  ```
  submitted_at = _timestamp_or_now(item.get("submitted_at") or item.get("timestamp"))
  ```

- **Line 708**: `"message_id"`
  ```
  old_id = str(item.get("message_id") or item.get("id") or uuid4())
  ```

- **Line 709**: `.get("timestamp"`
  ```
  created_at = _timestamp_or_now(item.get("created_at") or item.get("timestamp"))
  ```

- **Line 732**: `"message_id"`
  ```
  template_id = str(item.get("message_template_id") or item.get("message_id") or "")
  ```

- **Line 733**: `.get("timestamp"`
  ```
  sent_at = _timestamp_or_now(item.get("sent_at") or item.get("timestamp"))
  ```

- **Line 740**: `"delivery_status"`
  ```
  "status": str(item.get("status") or item.get("delivery_status") or "sent"),
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

### tasks\task_data_handlers.py
**Issues Found**: 5

- **Line 34**: `"completed_tasks"`
  ```
  COMPLETED_DEFAULT: dict = {"completed_tasks": []}
  ```

- **Line 123**: `"completed_tasks"`
  ```
  return data.get("completed_tasks", [])
  ```

- **Line 140**: `"completed_tasks"`
  ```
  user_id, TASKS_SUBDIR, COMPLETED_TASKS_FILENAME, {"completed_tasks": tasks}
  ```

- **Line 170**: `"completed_tasks"`
  ```
  completed_data = {"completed_tasks": tasks if status == "completed" else []}
  ```

- **Line 181**: `"task_id"`
  ```
  "task_id": task.get("id"),
  ```

### tasks\task_data_manager.py
**Issues Found**: 14

- **Line 78**: `"task_id"`
  ```
  "task_id": task_id,
  ```

- **Line 119**: `"task_id"`
  ```
  if task.get("task_id") == task_id:
  ```

- **Line 162**: `"task_id"`
  ```
  if task.get("task_id") == task_id:
  ```

- **Line 210**: `"task_id"`
  ```
  if task.get("task_id") == task_id:
  ```

- **Line 239**: `"task_id"`
  ```
  if task.get("task_id") == task_id:
  ```

- **Line 243**: `"task_id"`
  ```
  tasks = [t for t in tasks if t.get("task_id") != task_id]
  ```

- **Line 263**: `"task_id"`
  ```
  if task.get("task_id") == task_id:
  ```

- **Line 266**: `"task_id"`
  ```
  if task.get("task_id") == task_id:
  ```

- **Line 286**: `'task_id'`
  ```
  logger.warning(f"Invalid due date format for task {task.get('task_id')}")
  ```

- **Line 421**: `'task_id'`
  ```
  logger.warning(f"Could not parse completion date '{completion_date_str}' for recurring task {completed_task.get('task_id')}")
  ```

- **Line 428**: `'task_id'`
  ```
  logger.warning(f"Could not calculate next due date for recurring task {completed_task.get('task_id')}")
  ```

- **Line 433**: `"task_id"`
  ```
  "task_id": str(uuid.uuid4()),
  ```

- **Line 459**: `'task_id'`
  ```
  logger.info(f"Created next recurring task instance for task {completed_task.get('task_id')} with due date {next_due_date_str}")
  ```

- **Line 461**: `"task_id"`
  ```
  schedule_task_reminders(user_id, next_task["task_id"], next_task["reminder_periods"])
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

- **Line 1250**: `"task_id"`
  ```
  entities={"task_id": "invalid_task_id", "title": "New Title"},
  ```

- **Line 1273**: `"task_id"`
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
**Issues Found**: 27

- **Line 89**: `'message_id'`
  ```
  'message_id': 'motivational_001'
  ```

- **Line 95**: `'message_id'`
  ```
  'message_id': 'motivational_002'
  ```

- **Line 208**: `'message_id'`
  ```
  assert 'message_id' in data['messages'][0]
  ```

- **Line 234**: `"message_id"`
  ```
  "message_id": "test-msg-1",
  ```

- **Line 274**: `'message_id'`
  ```
  assert data['messages'][0]['message_id'] == "test-msg-1"
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

- **Line 394**: `'message_id'`
  ```
  assert data['messages'][0]['message_id'] == "test-msg-2"
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

- **Line 735**: `'message_id'`
  ```
  message_id = data['messages'][0]['message_id']
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
**Issues Found**: 32

- **Line 76**: `active_tasks.json`
  ```
  assert os.path.exists(os.path.join(task_dir, "active_tasks.json"))
  ```

- **Line 77**: `completed_tasks.json`
  ```
  assert os.path.exists(os.path.join(task_dir, "completed_tasks.json"))
  ```

- **Line 78**: `task_schedules.json`
  ```
  assert os.path.exists(os.path.join(task_dir, "task_schedules.json"))
  ```

- **Line 89**: `"task_id"`
  ```
  {"task_id": "1", "title": "Test Task 1", "completed": False},
  ```

- **Line 90**: `"task_id"`
  ```
  {"task_id": "2", "title": "Test Task 2", "completed": False},
  ```

- **Line 93**: `active_tasks.json`
  ```
  with open(os.path.join(task_dir, "active_tasks.json"), "w") as f:
  ```

- **Line 107**: `"task_id"`
  ```
  {"task_id": "1", "title": "Test Task 1", "completed": False},
  ```

- **Line 108**: `"task_id"`
  ```
  {"task_id": "2", "title": "Test Task 2", "completed": False},
  ```

- **Line 117**: `active_tasks.json`
  ```
  task_file = os.path.join(task_dir, "active_tasks.json")
  ```

- **Line 151**: `active_tasks.json`
  ```
  task_file = os.path.join(task_dir, "active_tasks.json")
  ```

- **Line 155**: `"task_id"`
  ```
  assert any(t["task_id"] == task_id for t in data["tasks"])
  ```

- **Line 180**: `active_tasks.json`
  ```
  task_file = os.path.join(task_dir, "active_tasks.json")
  ```

- **Line 184**: `"task_id"`
  ```
  t["task_id"] == task_id and t["title"] == "Updated Title"
  ```

- **Line 211**: `completed_tasks.json`
  ```
  completed_file = os.path.join(task_dir, "completed_tasks.json")
  ```

- **Line 216**: `"task_id"`
  ```
  t["task_id"] == task_id and t["completed"] for t in data["completed_tasks"]
  ```

- **Line 216**: `"completed_tasks"`
  ```
  t["task_id"] == task_id and t["completed"] for t in data["completed_tasks"]
  ```

- **Line 231**: `"task_id"`
  ```
  assert all(t["task_id"] != task_id for t in tasks)
  ```

- **Line 234**: `active_tasks.json`
  ```
  task_file = os.path.join(task_dir, "active_tasks.json")
  ```

- **Line 237**: `"task_id"`
  ```
  assert all(t["task_id"] != task_id for t in data["tasks"])
  ```

- **Line 249**: `"task_id"`
  ```
  assert task["task_id"] == task_id
  ```

- **Line 253**: `active_tasks.json`
  ```
  task_file = os.path.join(task_dir, "active_tasks.json")
  ```

- **Line 256**: `"task_id"`
  ```
  assert any(t["task_id"] == task_id for t in data["tasks"])
  ```

- **Line 285**: `"task_id"`
  ```
  assert any(t["task_id"] == id_soon for t in due_soon_tasks)
  ```

- **Line 286**: `"task_id"`
  ```
  assert all(t["task_id"] != id_late for t in due_soon_tasks)
  ```

- **Line 290**: `active_tasks.json`
  ```
  task_file = os.path.join(task_dir, "active_tasks.json")
  ```

- **Line 294**: `"task_id"`
  ```
  assert any(t["task_id"] == id_soon for t in data["tasks"])
  ```

- **Line 295**: `"task_id"`
  ```
  assert any(t["task_id"] == id_late for t in data["tasks"])
  ```

- **Line 332**: `active_tasks.json`
  ```
  active_file = os.path.join(task_dir, "active_tasks.json")
  ```

- **Line 333**: `completed_tasks.json`
  ```
  completed_file = os.path.join(task_dir, "completed_tasks.json")
  ```

- **Line 338**: `"task_id"`
  ```
  assert any(t["task_id"] == id2 for t in active_data["tasks"])
  ```

- **Line 339**: `"task_id"`
  ```
  assert any(t["task_id"] == id1 for t in completed_data["completed_tasks"])
  ```

- **Line 339**: `"completed_tasks"`
  ```
  assert any(t["task_id"] == id1 for t in completed_data["completed_tasks"])
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

- **Line 233**: `active_tasks.json`
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
**Issues Found**: 32

- **Line 89**: `active_tasks.json`
  ```
  "active_tasks.json",
  ```

- **Line 90**: `completed_tasks.json`
  ```
  "completed_tasks.json",
  ```

- **Line 91**: `task_schedules.json`
  ```
  "task_schedules.json",
  ```

- **Line 129**: `active_tasks.json`
  ```
  "active_tasks.json": {"tasks": [{"existing": "task"}]},
  ```

- **Line 130**: `completed_tasks.json`
  ```
  "completed_tasks.json": {"completed_tasks": []},
  ```

- **Line 130**: `"completed_tasks"`
  ```
  "completed_tasks.json": {"completed_tasks": []},
  ```

- **Line 131**: `task_schedules.json`
  ```
  "task_schedules.json": {"task_schedules": {}},
  ```

- **Line 145**: `active_tasks.json`
  ```
  active_file = task_dir / "active_tasks.json"
  ```

- **Line 161**: `"task_id"`
  ```
  {"task_id": "1", "title": "Task 1", "completed": False},
  ```

- **Line 162**: `"task_id"`
  ```
  {"task_id": "2", "title": "Task 2", "completed": False},
  ```

- **Line 165**: `active_tasks.json`
  ```
  active_file = task_dir / "active_tasks.json"
  ```

- **Line 185**: `active_tasks.json`
  ```
  active_file = task_dir / "active_tasks.json"
  ```

- **Line 205**: `"task_id"`
  ```
  {"task_id": "1", "title": "Task 1", "completed": False},
  ```

- **Line 206**: `"task_id"`
  ```
  {"task_id": "2", "title": "Task 2", "completed": False},
  ```

- **Line 215**: `active_tasks.json`
  ```
  active_file = task_dir / "active_tasks.json"
  ```

- **Line 237**: `"task_id"`
  ```
  {"task_id": "1", "title": "Completed Task 1", "completed": True},
  ```

- **Line 238**: `"task_id"`
  ```
  {"task_id": "2", "title": "Completed Task 2", "completed": True},
  ```

- **Line 241**: `completed_tasks.json`
  ```
  completed_file = task_dir / "completed_tasks.json"
  ```

- **Line 243**: `"completed_tasks"`
  ```
  json.dump({"completed_tasks": test_tasks}, f)
  ```

- **Line 256**: `"task_id"`
  ```
  {"task_id": "1", "title": "Completed Task 1", "completed": True},
  ```

- **Line 257**: `"task_id"`
  ```
  {"task_id": "2", "title": "Completed Task 2", "completed": True},
  ```

- **Line 266**: `completed_tasks.json`
  ```
  completed_file = task_dir / "completed_tasks.json"
  ```

- **Line 271**: `"completed_tasks"`
  ```
  assert data["completed_tasks"] == test_tasks
  ```

- **Line 302**: `"task_id"`
  ```
  assert task["task_id"] == task_id
  ```

- **Line 422**: `"task_id"`
  ```
  "task_id": "new-id",  # Disallowed - should be skipped
  ```

- **Line 435**: `"task_id"`
  ```
  assert task["task_id"] == task_id  # Disallowed field not updated
  ```

- **Line 712**: `"task_id"`
  ```
  assert active_tasks[0]["task_id"] == task_id
  ```

- **Line 868**: `"task_id"`
  ```
  assert all(task["task_id"] != task_id for task in tasks)
  ```

- **Line 887**: `"task_id"`
  ```
  assert task["task_id"] == task_id
  ```

- **Line 903**: `"task_id"`
  ```
  assert task["task_id"] == task_id
  ```

- **Line 931**: `"task_id"`
  ```
  task_ids = [task["task_id"] for task in due_soon_tasks]
  ```

- **Line 975**: `"task_id"`
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
**Issues Found**: 21

- **Line 36**: `active_tasks.json`
  ```
  Test: Completing a task moves it to completed_tasks.json and removes from active_tasks.json.
  ```

- **Line 36**: `completed_tasks.json`
  ```
  Test: Completing a task moves it to completed_tasks.json and removes from active_tasks.json.
  ```

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

- **Line 87**: `completed_tasks.json`
  ```
  completed_file = user_dir / 'tasks' / 'completed_tasks.json'
  ```

- **Line 88**: `completed_tasks.json`
  ```
  assert completed_file.exists(), "completed_tasks.json should exist"
  ```

- **Line 92**: `'task_id'`
  ```
  assert any(t['task_id'] == task_id for t in file_data.get('completed_tasks', [])), \
  ```

- **Line 92**: `'completed_tasks'`
  ```
  assert any(t['task_id'] == task_id for t in file_data.get('completed_tasks', [])), \
  ```

- **Line 93**: `completed_tasks.json`
  ```
  "Task should persist in completed_tasks.json file"
  ```

- **Line 101**: `active_tasks.json`
  ```
  Test: Deleting a task removes it from active_tasks.json and file system.
  ```

- **Line 119**: `'task_id'`
  ```
  assert any(t['task_id'] == task_id for t in active_before), "Task should exist before deletion"
  ```

- **Line 136**: `'task_id'`
  ```
  assert not any(t['task_id'] == task_id for t in active_after), "Task should be removed from active_tasks"
  ```

- **Line 140**: `'task_id'`
  ```
  assert not any(t['task_id'] == task_id for t in completed_after), "Task should not be in completed_tasks"
  ```

- **Line 149**: `active_tasks.json`
  ```
  active_file = user_dir / 'tasks' / 'active_tasks.json'
  ```

- **Line 153**: `'task_id'`
  ```
  assert not any(t['task_id'] == task_id for t in file_data.get('tasks', [])), \
  ```

- **Line 154**: `active_tasks.json`
  ```
  "Task should not persist in active_tasks.json file"
  ```

- **Line 214**: `active_tasks.json`
  ```
  active_file = user_dir / 'tasks' / 'active_tasks.json'
  ```

- **Line 218**: `'task_id'`
  ```
  file_task = next((t for t in file_data.get('tasks', []) if t['task_id'] == task_id), None)
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
**Issues Found**: 28

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

- **Line 319**: `"message_id"`
  ```
  "message_id": "template-1",
  ```

- **Line 360**: `"message_id"`
  ```
  assert messages[0]["message_id"] == "template-1"
  ```

- **Line 497**: `"task_id"`
  ```
  assert active[0]["task_id"] == "task-active"
  ```

- **Line 499**: `"task_id"`
  ```
  assert completed[0]["task_id"] == "task-completed"
  ```

- **Line 506**: `"task_id"`
  ```
  "task_id": "task-new",
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
