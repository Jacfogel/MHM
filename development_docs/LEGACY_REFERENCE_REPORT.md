# Legacy Reference Cleanup Report

> **File**: `development_docs/LEGACY_REFERENCE_REPORT.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2026-05-06 22:46:09
> **Source**: `python development_tools/generate_legacy_reference_report.py` - Legacy Reference Report Generator
**Total Files with Issues**: 10
**Legacy Compatibility Markers Detected**: 17

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
- Removed entries: 21
- Active search terms: 2
- Current inventory-term hits in scan: 1 file(s), 2 marker(s)

## Deprecation Inventory Terms
**Files Affected**: 1

### ai\chatbot.py
**Issues Found**: 2

- **Line 611**: `_get_fallback_response`
  ```
  def _get_fallback_response(self, user_prompt: str) -> str:
  ```

- **Line 612**: `Legacy fallback method for backwards compatibility`
  ```
  """Legacy fallback method for backwards compatibility."""
  ```

## Legacy Inventory Tracking
**Files Affected**: 1

### ai\chatbot.py
**Issues Found**: 1

- **Line 612**: `backwards compatibility`
  ```
  """Legacy fallback method for backwards compatibility."""
  ```

## User Data V1 Runtime Adapters
**Files Affected**: 9

### communication\core\channel_orchestrator.py
**Issues Found**: 1

- **Line 352**: `.get("body"`
  ```
  email_body = email_msg.get("body", "")
  ```

### core\service_requests.py
**Issues Found**: 1

- **Line 503**: `.get("timestamp"`
  ```
  "timestamp": request_data.get("timestamp", 0),
  ```

### core\user_data_operations.py
**Issues Found**: 2

- **Line 814**: `.get("timestamp"`
  ```
  ts = recent_chats[0].get("timestamp")
  ```

- **Line 1800**: `.get("timestamp"`
  ```
  last_ix = str(raw[-1].get("timestamp") or "Unknown")
  ```

### development_tools\functions\analyze_duplicate_functions.py
**Issues Found**: 2

- **Line 724**: `.get("body"`
  ```
  overall += body_score * weights.get("body", 0.0)
  ```

- **Line 756**: `.get("body"`
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

- **Line 1847**: `.get('timestamp'`
  ```
  'timestamp': result_data.get('timestamp', datetime.now().isoformat())
  ```

- **Line 2156**: `.get("timestamp"`
  ```
  existing_run.get("timestamp")
  ```

### development_tools\shared\service\data_loading.py
**Issues Found**: 2

- **Line 390**: `.get('timestamp'`
  ```
  timestamp = data.get('timestamp', 'Unknown')
  ```

- **Line 507**: `.get('timestamp'`
  ```
  timestamp = meta.get('timestamp')
  ```

### tests\behavior\test_checkin_analytics_behavior.py
**Issues Found**: 1

- **Line 485**: `.get("timestamp"`
  ```
  assert checkin.get("timestamp"), "Formatted history should include display timestamp"
  ```
