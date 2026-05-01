# Legacy Reference Cleanup Report

> **File**: `development_docs/LEGACY_REFERENCE_REPORT.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2026-05-01 00:33:00
> **Source**: `python development_tools/generate_legacy_reference_report.py` - Legacy Reference Report Generator
**Total Files with Issues**: 17
**Legacy Compatibility Markers Detected**: 38

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
- Removed entries: 17
- Active search terms: 0
- Current inventory-term hits in scan: 0 file(s), 0 marker(s)

## User Data V1 Runtime Adapters
**Files Affected**: 17

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

### core\response_tracking.py
**Issues Found**: 2

- **Line 61**: `.get("timestamp"`
  ```
  candidates.append(response_data.get("timestamp"))
  ```

- **Line 297**: `.get("timestamp"`
  ```
  or item.get("timestamp")
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
**Issues Found**: 1

- **Line 1159**: `.get("timestamp"`
  ```
  request_timestamp = request_data.get("timestamp", 0)
  ```

### core\user_data_manager.py
**Issues Found**: 2

- **Line 810**: `.get("timestamp"`
  ```
  ts = recent_chats[0].get("timestamp")
  ```

- **Line 1796**: `.get("timestamp"`
  ```
  last_ix = str(raw[-1].get("timestamp") or "Unknown")
  ```

### core\user_data_read.py
**Issues Found**: 1

- **Line 59**: `"message_id"`
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

### tests\behavior\test_checkin_analytics_behavior.py
**Issues Found**: 1

- **Line 485**: `.get("timestamp"`
  ```
  assert checkin.get("timestamp"), "Formatted history should include display timestamp"
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
**Issues Found**: 6

- **Line 34**: `"task_id"`
  ```
  "task_id": "legacy",
  ```

- **Line 53**: `"task_id"`
  ```
  assert "task_id" in errors[0]
  ```

- **Line 275**: `"task_id"`
  ```
  assert "task_id" not in active[0]
  ```

- **Line 295**: `"task_id"`
  ```
  assert "task_id" not in data["tasks"][0]
  ```

- **Line 296**: `active_tasks.json`
  ```
  assert not (tasks_dir / "active_tasks.json").exists()
  ```

- **Line 297**: `completed_tasks.json`
  ```
  assert not (tasks_dir / "completed_tasks.json").exists()
  ```
