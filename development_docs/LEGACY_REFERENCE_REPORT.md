# Legacy Reference Cleanup Report

> **File**: `development_docs/LEGACY_REFERENCE_REPORT.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2026-04-29 19:24:34
> **Source**: `python development_tools/generate_legacy_reference_report.py` - Legacy Reference Report Generator
**Total Files with Issues**: 43
**Legacy Compatibility Markers Detected**: 176

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
- Active/candidate entries: 1
- Removed entries: 10
- Active search terms: 0
- Current inventory-term hits in scan: 0 file(s), 0 marker(s)

## User Data V1 Runtime Adapters
**Files Affected**: 43

### ai\chatbot.py
**Issues Found**: 2

- **Line 994**: `.get("timestamp"`
  ```
  msg.get("sent_at") or msg.get("timestamp") or ""
  ```

- **Line 1031**: `.get("timestamp"`
  ```
  latest_task.get("sent_at") or latest_task.get("timestamp") or ""
  ```

### communication\command_handlers\task_handler.py
**Issues Found**: 1

- **Line 1104**: `"completed_tasks"`
  ```
  completed_tasks = overall_stats.get("completed_tasks", 0)
  ```

### communication\communication_channels\email\bot.py
**Issues Found**: 1

- **Line 266**: `"message_id"`
  ```
  "message_id": email_id.decode(),
  ```

### communication\core\channel_orchestrator.py
**Issues Found**: 2

- **Line 287**: `"message_id"`
  ```
  email_id = email_msg.get("message_id")
  ```

- **Line 348**: `.get("body"`
  ```
  email_body = email_msg.get("body", "")
  ```

### communication\message_processing\conversation_flow_manager.py
**Issues Found**: 4

- **Line 165**: `"task_id"`
  ```
  legacy = data.get("task_id")
  ```

- **Line 169**: `"task_id"`
  ```
  data.pop("task_id", None)
  ```

- **Line 172**: `"task_id"`
  ```
  data.pop("task_id", None)
  ```

- **Line 1600**: `"task_id"`
  ```
  if "task_id" in str(e).lower() or "not found" in str(e).lower():
  ```

### core\message_management.py
**Issues Found**: 8

- **Line 93**: `"message_id"`
  ```
  message_id = message.get("id") or message.get("message_id")
  ```

- **Line 123**: `"message_id"`
  ```
  message_id = str(message.get("id") or message.get("message_id") or uuid.uuid4())
  ```

- **Line 124**: `.get("timestamp"`
  ```
  created_at = _canonical_message_timestamp(message.get("created_at") or message.get("timestamp")) or now_timestamp_full()
  ```

- **Line 753**: `.get("timestamp"`
  ```
  message_timestamp = _parse_message_timestamp(message.get("timestamp", ""))
  ```

- **Line 780**: `.get("timestamp"`
  ```
  msg.get("timestamp", "") for msg in archived_messages
  ```

- **Line 783**: `.get("timestamp"`
  ```
  msg.get("timestamp", "") for msg in archived_messages
  ```

- **Line 862**: `.get("timestamp"`
  ```
  timestamp_value = message.get("timestamp", "")
  ```

- **Line 1052**: `.get("timestamp"`
  ```
  timestamp = item.get("sent_at") or item.get("timestamp") or "1970-01-01 00:00:00"
  ```

### core\response_tracking.py
**Issues Found**: 4

- **Line 44**: `.get("timestamp"`
  ```
  raw = checkin.get("submitted_at") or checkin.get("timestamp")
  ```

- **Line 56**: `.get("timestamp"`
  ```
  or response_data.get("timestamp")
  ```

- **Line 216**: `.get("timestamp"`
  ```
  or item.get("timestamp")
  ```

- **Line 272**: `.get("timestamp"`
  ```
  or checkin.get("timestamp", "")
  ```

### core\scheduler.py
**Issues Found**: 2

- **Line 1822**: `"task_id"`
  ```
  and kwargs.get("task_id") == task_id
  ```

- **Line 1915**: `"task_id"`
  ```
  task_id = kwargs.get("task_id")
  ```

### core\service.py
**Issues Found**: 2

- **Line 1060**: `"task_id"`
  ```
  "task_id"
  ```

- **Line 1158**: `.get("timestamp"`
  ```
  request_timestamp = request_data.get("timestamp", 0)
  ```

### core\user_data_manager.py
**Issues Found**: 4

- **Line 814**: `.get("timestamp"`
  ```
  or recent_chats[0].get("timestamp")
  ```

- **Line 1793**: `.get("timestamp"`
  ```
  or x.get("timestamp")
  ```

- **Line 1801**: `.get("timestamp"`
  ```
  or lm.get("timestamp")
  ```

- **Line 1815**: `.get("timestamp"`
  ```
  last_ix = str(raw[-1].get("timestamp") or "Unknown")
  ```

### core\user_data_read.py
**Issues Found**: 2

- **Line 53**: `"message_id"`
  ```
  message_id = str(message.get("id") or message.get("message_id") or "").strip()
  ```

- **Line 58**: `"message_id"`
  ```
  message.pop("message_id", None)
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
**Issues Found**: 4

- **Line 138**: `.get("body"`
  ```
  if description is None and entry.get("body"):
  ```

- **Line 139**: `.get("body"`
  ```
  description = entry.get("body")
  ```

- **Line 141**: `.get("archived"`
  ```
  if status == "active" and entry.get("archived") is True:
  ```

- **Line 176**: `.get("body"`
  ```
  description = entry.get("body") or ""
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
**Issues Found**: 2

- **Line 235**: `"message_id"`
  ```
  "message_id": f"msg-{i}",
  ```

- **Line 239**: `"delivery_status"`
  ```
  "delivery_status": "sent",
  ```

### tests\behavior\test_message_behavior.py
**Issues Found**: 13

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

- **Line 552**: `"message_id"`
  ```
  "message_id": "msg-good",
  ```

- **Line 581**: `"message_id"`
  ```
  {"message_id": "default1", "message": "Default message 1", "days": ["monday"], "time_periods": ["morning"]},
  ```

- **Line 582**: `"message_id"`
  ```
  {"message_id": "default2", "message": "Default message 2", "days": ["tuesday"], "time_periods": ["evening"]}
  ```

- **Line 630**: `"message_id"`
  ```
  message_data = {"message_id": "test_msg", "message": "Test message", "days": ["monday"], "time_periods": ["morning"]}
  ```

- **Line 647**: `"message_id"`
  ```
  updated_data = {"message_id": "test_msg", "message": "Updated message", "days": ["monday"], "time_periods": ["morning"]}
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

### tests\behavior\test_task_behavior.py
**Issues Found**: 4

- **Line 78**: `active_tasks.json`
  ```
  assert not os.path.exists(os.path.join(task_dir, "active_tasks.json"))
  ```

- **Line 79**: `completed_tasks.json`
  ```
  assert not os.path.exists(os.path.join(task_dir, "completed_tasks.json"))
  ```

- **Line 80**: `task_schedules.json`
  ```
  assert not os.path.exists(os.path.join(task_dir, "task_schedules.json"))
  ```

- **Line 129**: `"task_id"`
  ```
  assert all("task_id" not in task for task in saved_data["tasks"])
  ```

### tests\behavior\test_task_handler_behavior.py
**Issues Found**: 2

- **Line 640**: `"task_id"`
  ```
  call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("task_id")
  ```

- **Line 706**: `"completed_tasks"`
  ```
  "completed_tasks": 10,
  ```

### tests\behavior\test_task_management_coverage_expansion.py
**Issues Found**: 12

- **Line 106**: `active_tasks.json`
  ```
  assert not (task_dir / "active_tasks.json").exists()
  ```

- **Line 107**: `completed_tasks.json`
  ```
  assert not (task_dir / "completed_tasks.json").exists()
  ```

- **Line 108**: `task_schedules.json`
  ```
  assert not (task_dir / "task_schedules.json").exists()
  ```

- **Line 136**: `active_tasks.json`
  ```
  "active_tasks.json": {"tasks": [{"existing": "task"}]},
  ```

- **Line 137**: `completed_tasks.json`
  ```
  "completed_tasks.json": {"completed_tasks": []},
  ```

- **Line 137**: `"completed_tasks"`
  ```
  "completed_tasks.json": {"completed_tasks": []},
  ```

- **Line 138**: `task_schedules.json`
  ```
  "task_schedules.json": {"task_schedules": {}},
  ```

- **Line 152**: `active_tasks.json`
  ```
  active_file = task_dir / "active_tasks.json"
  ```

- **Line 192**: `active_tasks.json`
  ```
  active_file = task_dir / "active_tasks.json"
  ```

- **Line 229**: `active_tasks.json`
  ```
  assert not (task_dir / "active_tasks.json").exists()
  ```

- **Line 285**: `completed_tasks.json`
  ```
  assert not (task_dir / "completed_tasks.json").exists()
  ```

- **Line 436**: `"task_id"`
  ```
  "task_id": "new-id",  # Disallowed - should be skipped
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

- **Line 52**: `"message_id"`
  ```
  assert all("message_id" not in m for m in out["messages"])
  ```

- **Line 138**: `"message_id"`
  ```
  {"message_id": "duplicate-id", "body": "first"},
  ```

- **Line 139**: `"message_id"`
  ```
  {"message_id": "duplicate-id", "body": "second"},
  ```

- **Line 153**: `"message_id"`
  ```
  assert all("message_id" not in m for m in reloaded["messages"])
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
**Issues Found**: 2

- **Line 91**: `completed_tasks.json`
  ```
  assert not (user_dir / "tasks" / "completed_tasks.json").exists()
  ```

- **Line 156**: `active_tasks.json`
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
**Issues Found**: 5

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

### tests\unit\test_recurring_tasks.py
**Issues Found**: 3

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
**Issues Found**: 27

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

- **Line 501**: `"task_id"`
  ```
  assert "task_id" not in active[0]
  ```

- **Line 521**: `"task_id"`
  ```
  assert "task_id" not in data["tasks"][0]
  ```

- **Line 522**: `active_tasks.json`
  ```
  assert not (tasks_dir / "active_tasks.json").exists()
  ```

- **Line 523**: `completed_tasks.json`
  ```
  assert not (tasks_dir / "completed_tasks.json").exists()
  ```

### ui\ui_app_qt.py
**Issues Found**: 1

- **Line 2292**: `"task_id"`
  ```
  "task_id": task_id,
  ```
