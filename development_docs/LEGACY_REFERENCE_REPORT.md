# Legacy Reference Cleanup Report

> **File**: `development_docs/LEGACY_REFERENCE_REPORT.md`
> **Generated**: This file is auto-generated. Do not edit manually.
> **Last Generated**: 2026-05-14 01:40:05
> **Source**: `python development_tools/generate_legacy_reference_report.py` - Legacy Reference Report Generator
**Total Files with Issues**: 50
**Legacy Compatibility Markers Detected**: 350

## Summary
- Scan mode only: no automated fixes were applied.
- Changelogs, archive folders, and planning documents are intentionally historical and excluded from this report.
- Legacy compatibility markers remain in 10 file(s) (10 total markers).
- Remaining counts come from legacy inventory tracking categories (40 file(s), 340 marker(s)).

## Recommended Follow-Up
- Additional guidance: [AI_LEGACY_COMPATIBILITY_GUIDE.md](../ai_development_docs/AI_LEGACY_COMPATIBILITY_GUIDE.md)
1. Identify active legacy compatibility behavior and migrate all callers/dependencies to current implementations before deleting markers.
2. Add or update regression tests that prove migrated flows work without legacy compatibility code paths. See [AI_TESTING_GUIDE.md](../ai_development_docs/AI_TESTING_GUIDE.md) for additional guidance.
3. Only after migration is verified, remove legacy markers/comments/docs evidence and rerun `python development_tools/run_development_tools.py legacy --clean --dry-run` until this report returns zero issues.

## Deprecation Inventory
- Inventory file: `development_tools/config/jsons/DEPRECATION_INVENTORY.json`
- Active/candidate entries: 2
- Removed entries: 22
- Active search terms: 11
- Current inventory-term hits in scan: 50 file(s), 253 marker(s)

## Core Storage Module Bridges
**Files Affected**: 31

### tests\behavior\test_account_handler_behavior.py
**Issues Found**: 14

- **Line 75**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import delete_user_completely, rebuild_user_index
  ```

- **Line 125**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import delete_user_completely
  ```

- **Line 174**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import delete_user_completely
  ```

- **Line 250**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 281**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 323**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import delete_user_completely, rebuild_user_index
  ```

- **Line 399**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 453**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 562**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 587**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 705**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 758**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 815**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 858**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

### tests\behavior\test_account_management_real_behavior.py
**Issues Found**: 4

- **Line 129**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 251**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 469**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 594**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

### tests\behavior\test_backup_manager_behavior.py
**Issues Found**: 1

- **Line 787**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

### tests\behavior\test_comprehensive_quantitative_analytics.py
**Issues Found**: 1

- **Line 12**: `from core.user_data_v2_base import`
  ```
  from core.user_data_v2_base import SCHEMA_VERSION
  ```

### tests\behavior\test_discord_bot_behavior.py
**Issues Found**: 3

- **Line 360**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 409**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 479**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

### tests\behavior\test_interaction_handlers_behavior.py
**Issues Found**: 3

- **Line 201**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 270**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 346**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

### tests\behavior\test_notebook_handler_behavior.py
**Issues Found**: 1

- **Line 13**: `from core.user_data_v2_base import`
  ```
  from core.user_data_v2_base import generate_short_id
  ```

### tests\behavior\test_quantitative_analytics_expansion.py
**Issues Found**: 1

- **Line 10**: `from core.user_data_v2_base import`
  ```
  from core.user_data_v2_base import SCHEMA_VERSION
  ```

### tests\behavior\test_response_tracking_behavior.py
**Issues Found**: 1

- **Line 21**: `from core.user_data_v2_base import`
  ```
  from core.user_data_v2_base import SCHEMA_VERSION
  ```

### tests\behavior\test_service_utilities_behavior.py
**Issues Found**: 1

- **Line 25**: `from core.user_data_validation import`
  ```
  from core.user_data_validation import _shared__title_case
  ```

### tests\behavior\test_task_behavior.py
**Issues Found**: 1

- **Line 18**: `import core.user_item_storage`
  ```
  import core.user_item_storage as user_item_storage
  ```

### tests\behavior\test_user_management_coverage_expansion.py
**Issues Found**: 4

- **Line 33**: `from core.user_data_registry import`
  ```
  from core.user_data_registry import (
  ```

- **Line 93**: `import core.user_data_registry`
  ```
  import core.user_data_registry as um
  ```

- **Line 103**: `import core.user_data_registry`
  ```
  import core.user_data_registry as um
  ```

- **Line 1010**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import UserDataManager
  ```

### tests\conftest.py
**Issues Found**: 2

- **Line 345**: `import core.user_data_operations`
  ```
  import core.user_data_operations as udm_module
  ```

- **Line 346**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import UserDataManager
  ```

### tests\core\test_message_management.py
**Issues Found**: 1

- **Line 16**: `from core.user_data_v2_base import`
  ```
  from core.user_data_v2_base import SCHEMA_VERSION
  ```

### tests\core\test_user_data_read_scenarios.py
**Issues Found**: 2

- **Line 16**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import update_user_index
  ```

- **Line 17**: `from core.user_data_read import`
  ```
  from core.user_data_read import (
  ```

### tests\integration\test_account_lifecycle.py
**Issues Found**: 12

- **Line 14**: `from core.user_data_v2_base import`
  ```
  from core.user_data_v2_base import SCHEMA_VERSION
  ```

- **Line 169**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 232**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import update_user_index
  ```

- **Line 329**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 437**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import update_user_index
  ```

- **Line 533**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 632**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import update_user_index
  ```

- **Line 720**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import update_user_index
  ```

- **Line 788**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import update_user_index
  ```

- **Line 867**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import update_user_index
  ```

- **Line 937**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import update_user_index
  ```

- **Line 1004**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

### tests\integration\test_account_management.py
**Issues Found**: 3

- **Line 64**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import UserDataManager
  ```

- **Line 256**: `from core.user_data_validation import`
  ```
  from core.user_data_validation import validate_user_update
  ```

- **Line 437**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import update_user_index
  ```

### tests\integration\test_error_handling_improvements.py
**Issues Found**: 1

- **Line 19**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import UserDataManager
  ```

### tests\integration\test_user_creation.py
**Issues Found**: 5

- **Line 27**: `from core.user_data_validation import`
  ```
  from core.user_data_validation import is_valid_email
  ```

- **Line 177**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 394**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 533**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 751**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

### tests\test_helpers\test_support\conftest_user_data.py
**Issues Found**: 8

- **Line 20**: `from core.user_data_v2_base import`
  ```
  from core.user_data_v2_base import SCHEMA_VERSION
  ```

- **Line 82**: `import core.user_data_registry`
  ```
  import core.user_data_registry as um
  ```

- **Line 104**: `import core.user_data_registry`
  ```
  import core.user_data_registry as um
  ```

- **Line 128**: `import core.user_data_registry`
  ```
  import core.user_data_registry as um
  ```

- **Line 129**: `import core.user_data_read`
  ```
  import core.user_data_read as read_module
  ```

- **Line 299**: `import core.user_data_registry`
  ```
  import core.user_data_registry as um
  ```

- **Line 674**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import update_user_index
  ```

- **Line 839**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import update_user_index
  ```

### tests\test_helpers\test_utilities\test_user_factory.py
**Issues Found**: 2

- **Line 1047**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import update_user_index
  ```

- **Line 1197**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import update_user_index
  ```

### tests\ui\test_account_creation_ui.py
**Issues Found**: 4

- **Line 927**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import update_user_index, rebuild_user_index
  ```

- **Line 1218**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 1574**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import update_user_index, rebuild_user_index
  ```

- **Line 2263**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import build_user_index
  ```

### tests\ui\test_widget_behavior.py
**Issues Found**: 1

- **Line 328**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

### tests\unit\test_recurring_tasks.py
**Issues Found**: 1

- **Line 13**: `from core.user_data_v2_base import`
  ```
  from core.user_data_v2_base import SCHEMA_VERSION
  ```

### tests\unit\test_task_short_ids.py
**Issues Found**: 1

- **Line 5**: `from core.user_data_v2_base import`
  ```
  from core.user_data_v2_base import generate_short_id
  ```

### tests\unit\test_user_data_loader_idempotency.py
**Issues Found**: 2

- **Line 12**: `import_module('core.user_data_registry')`
  ```
  um = importlib.import_module('core.user_data_registry')
  ```

- **Line 13**: `import_module('core.user_data_registry')`
  ```
  udh = importlib.import_module('core.user_data_registry')
  ```

### tests\unit\test_user_data_manager.py
**Issues Found**: 3

- **Line 21**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import (
  ```

- **Line 358**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 389**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

### tests\unit\test_user_data_validation_user_id.py
**Issues Found**: 1

- **Line 5**: `from core.user_data_validation import`
  ```
  from core.user_data_validation import is_valid_user_id
  ```

### tests\unit\test_user_item_storage.py
**Issues Found**: 1

- **Line 5**: `from core.user_item_storage import`
  ```
  from core.user_item_storage import (
  ```

### tests\unit\test_user_management.py
**Issues Found**: 1

- **Line 532**: `from core.user_data_operations import`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

### tests\unit\test_validation.py
**Issues Found**: 1

- **Line 14**: `from core.user_data_validation import`
  ```
  from core.user_data_validation import (
  ```

## Deprecation Inventory Terms
**Files Affected**: 50

### core\runtime_state_storage.py
**Issues Found**: 1

- **Line 1**: `core.runtime_state_storage`
  ```
  # LEGACY COMPATIBILITY: Temporary bridge for old core.runtime_state_storage imports.
  ```

### core\service_flag_storage.py
**Issues Found**: 1

- **Line 1**: `core.service_flag_storage`
  ```
  # LEGACY COMPATIBILITY: Temporary bridge for old core.service_flag_storage imports.
  ```

### core\user_data_operations.py
**Issues Found**: 1

- **Line 1**: `core.user_data_operations`
  ```
  # LEGACY COMPATIBILITY: Temporary bridge for old core.user_data_operations imports.
  ```

### core\user_data_presets.py
**Issues Found**: 1

- **Line 1**: `core.user_data_presets`
  ```
  # LEGACY COMPATIBILITY: Temporary bridge for old core.user_data_presets imports.
  ```

### core\user_data_read.py
**Issues Found**: 1

- **Line 1**: `core.user_data_read`
  ```
  # LEGACY COMPATIBILITY: Temporary bridge for old core.user_data_read imports.
  ```

### core\user_data_registry.py
**Issues Found**: 1

- **Line 1**: `core.user_data_registry`
  ```
  # LEGACY COMPATIBILITY: Temporary bridge for old core.user_data_registry imports.
  ```

### core\user_data_v2_base.py
**Issues Found**: 1

- **Line 1**: `core.user_data_v2_base`
  ```
  # LEGACY COMPATIBILITY: Temporary bridge for old core.user_data_v2_base imports.
  ```

### core\user_data_validation.py
**Issues Found**: 1

- **Line 1**: `core.user_data_validation`
  ```
  # LEGACY COMPATIBILITY: Temporary bridge for old core.user_data_validation imports.
  ```

### core\user_data_write.py
**Issues Found**: 1

- **Line 1**: `core.user_data_write`
  ```
  # LEGACY COMPATIBILITY: Temporary bridge for old core.user_data_write imports.
  ```

### core\user_item_storage.py
**Issues Found**: 1

- **Line 1**: `core.user_item_storage`
  ```
  # LEGACY COMPATIBILITY: Temporary bridge for old core.user_item_storage imports.
  ```

### tests\behavior\test_account_handler_behavior.py
**Issues Found**: 14

- **Line 75**: `core.user_data_operations`
  ```
  from core.user_data_operations import delete_user_completely, rebuild_user_index
  ```

- **Line 125**: `core.user_data_operations`
  ```
  from core.user_data_operations import delete_user_completely
  ```

- **Line 174**: `core.user_data_operations`
  ```
  from core.user_data_operations import delete_user_completely
  ```

- **Line 250**: `core.user_data_operations`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 281**: `core.user_data_operations`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 323**: `core.user_data_operations`
  ```
  from core.user_data_operations import delete_user_completely, rebuild_user_index
  ```

- **Line 399**: `core.user_data_operations`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 453**: `core.user_data_operations`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 562**: `core.user_data_operations`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 587**: `core.user_data_operations`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 705**: `core.user_data_operations`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 758**: `core.user_data_operations`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 815**: `core.user_data_operations`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 858**: `core.user_data_operations`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

### tests\behavior\test_account_management_real_behavior.py
**Issues Found**: 4

- **Line 129**: `core.user_data_operations`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 251**: `core.user_data_operations`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 469**: `core.user_data_operations`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 594**: `core.user_data_operations`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

### tests\behavior\test_analytics_handler_behavior.py
**Issues Found**: 1

- **Line 621**: `core.user_data_read`
  ```
  @patch('core.user_data_read.get_user_data')
  ```

### tests\behavior\test_backup_manager_behavior.py
**Issues Found**: 1

- **Line 787**: `core.user_data_operations`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

### tests\behavior\test_comprehensive_quantitative_analytics.py
**Issues Found**: 1

- **Line 12**: `core.user_data_v2_base`
  ```
  from core.user_data_v2_base import SCHEMA_VERSION
  ```

### tests\behavior\test_discord_bot_behavior.py
**Issues Found**: 3

- **Line 360**: `core.user_data_operations`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 409**: `core.user_data_operations`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 479**: `core.user_data_operations`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

### tests\behavior\test_interaction_handlers_behavior.py
**Issues Found**: 3

- **Line 201**: `core.user_data_operations`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 270**: `core.user_data_operations`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 346**: `core.user_data_operations`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

### tests\behavior\test_notebook_handler_behavior.py
**Issues Found**: 1

- **Line 13**: `core.user_data_v2_base`
  ```
  from core.user_data_v2_base import generate_short_id
  ```

### tests\behavior\test_quantitative_analytics_expansion.py
**Issues Found**: 1

- **Line 10**: `core.user_data_v2_base`
  ```
  from core.user_data_v2_base import SCHEMA_VERSION
  ```

### tests\behavior\test_response_tracking_behavior.py
**Issues Found**: 1

- **Line 21**: `core.user_data_v2_base`
  ```
  from core.user_data_v2_base import SCHEMA_VERSION
  ```

### tests\behavior\test_service_utilities_behavior.py
**Issues Found**: 1

- **Line 25**: `core.user_data_validation`
  ```
  from core.user_data_validation import _shared__title_case
  ```

### tests\behavior\test_task_behavior.py
**Issues Found**: 1

- **Line 18**: `core.user_item_storage`
  ```
  import core.user_item_storage as user_item_storage
  ```

### tests\behavior\test_task_management_coverage_expansion.py
**Issues Found**: 1

- **Line 77**: `core.user_item_storage`
  ```
  with patch("core.user_item_storage.get_user_data_dir", return_value=temp_dir):
  ```

### tests\behavior\test_user_data_flow_architecture.py
**Issues Found**: 2

- **Line 490**: `core.user_data_write`
  ```
  with patch('core.user_data_write.update_user_account') as mock_update_account:
  ```

- **Line 538**: `core.user_data_write`
  ```
  with patch('core.user_data_write.update_user_account') as mock_update_account:
  ```

### tests\behavior\test_user_management_coverage_expansion.py
**Issues Found**: 99

- **Line 33**: `core.user_data_registry`
  ```
  from core.user_data_registry import (
  ```

- **Line 62**: `core.user_data_registry`
  ```
  monkeypatch.setattr('core.user_data_registry.get_user_file_path', mock_path, raising=False)
  ```

- **Line 63**: `core.user_data_registry`
  ```
  monkeypatch.setattr('core.user_data_registry.ensure_user_directory', lambda uid: True, raising=False)
  ```

- **Line 93**: `core.user_data_registry`
  ```
  import core.user_data_registry as um
  ```

- **Line 103**: `core.user_data_registry`
  ```
  import core.user_data_registry as um
  ```

- **Line 186**: `core.user_data_registry`
  ```
  with patch('core.user_data_registry.get_user_file_path', return_value=account_file), \
  ```

- **Line 187**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.ensure_user_directory'), \
  ```

- **Line 188**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.load_json_data', return_value=test_account):
  ```

- **Line 209**: `core.user_data_registry`
  ```
  with patch('core.user_data_registry.get_user_file_path') as mock_get_path:
  ```

- **Line 228**: `core.user_data_registry`
  ```
  with patch('core.user_data_registry.os.path.exists', side_effect=exists_side_effect), \
  ```

- **Line 229**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.ensure_user_directory'), \
  ```

- **Line 230**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.load_json_data', return_value=None), \
  ```

- **Line 231**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.save_json_data') as mock_save:
  ```

- **Line 254**: `core.user_data_registry`
  ```
  with patch('core.user_data_registry.get_user_file_path') as mock_get_path:
  ```

- **Line 274**: `core.user_data_registry`
  ```
  with patch('core.user_data_registry.get_user_file_path') as mock_get_path:
  ```

- **Line 279**: `core.user_data_registry`
  ```
  with patch('core.user_data_registry.ensure_user_directory'), \
  ```

- **Line 280**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.save_json_data') as mock_save, \
  ```

- **Line 281**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.validate_account_dict') as mock_validate:
  ```

- **Line 311**: `core.user_data_registry`
  ```
  with patch('core.user_data_registry.get_user_file_path', return_value=preferences_file), \
  ```

- **Line 312**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.ensure_user_directory'), \
  ```

- **Line 313**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.load_json_data', return_value=test_preferences):
  ```

- **Line 328**: `core.user_data_registry`
  ```
  with patch('core.user_data_registry.get_user_file_path') as mock_get_path:
  ```

- **Line 333**: `core.user_data_registry`
  ```
  with patch('core.user_data_registry.ensure_user_directory'), \
  ```

- **Line 334**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.save_json_data') as mock_save:
  ```

- **Line 355**: `core.user_data_registry`
  ```
  with patch('core.user_data_registry.get_user_file_path') as mock_get_path:
  ```

- **Line 360**: `core.user_data_registry`
  ```
  with patch('core.user_data_registry.ensure_user_directory'), \
  ```

- **Line 361**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.save_json_data') as mock_save, \
  ```

- **Line 362**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.validate_preferences_dict') as mock_validate:
  ```

- **Line 385**: `core.user_data_registry`
  ```
  with patch('core.user_data_registry.get_user_file_path', return_value=context_file), \
  ```

- **Line 386**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.ensure_user_directory'), \
  ```

- **Line 387**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.load_json_data', return_value=test_context):
  ```

- **Line 403**: `core.user_data_registry`
  ```
  with patch('core.user_data_registry.get_user_file_path') as mock_get_path:
  ```

- **Line 408**: `core.user_data_registry`
  ```
  with patch('core.user_data_registry.ensure_user_directory'), \
  ```

- **Line 409**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.save_json_data') as mock_save:
  ```

- **Line 434**: `core.user_data_registry`
  ```
  with patch('core.user_data_registry.get_user_file_path') as mock_get_path:
  ```

- **Line 439**: `core.user_data_registry`
  ```
  with patch('core.user_data_registry.ensure_user_directory'), \
  ```

- **Line 440**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.save_json_data') as mock_save, \
  ```

- **Line 441**: `core.user_data_operations`
  ```
  patch('core.user_data_operations.update_user_index'):
  ```

- **Line 466**: `core.user_data_registry`
  ```
  with patch('core.user_data_registry.get_user_file_path', return_value=schedules_file), \
  ```

- **Line 467**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.ensure_user_directory'), \
  ```

- **Line 468**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.load_json_data', return_value=test_schedules):
  ```

- **Line 484**: `core.user_data_registry`
  ```
  with patch('core.user_data_registry.get_user_file_path') as mock_get_path:
  ```

- **Line 489**: `core.user_data_registry`
  ```
  with patch('core.user_data_registry.ensure_user_directory'), \
  ```

- **Line 490**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.save_json_data') as mock_save:
  ```

- **Line 508**: `core.user_data_registry`
  ```
  with patch('core.user_data_registry.get_user_file_path') as mock_get_path:
  ```

- **Line 513**: `core.user_data_registry`
  ```
  with patch('core.user_data_registry.ensure_user_directory'), \
  ```

- **Line 514**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.save_json_data') as mock_save:
  ```

- **Line 538**: `core.user_data_write`
  ```
  with patch('core.user_data_write.save_user_data') as mock_save:
  ```

- **Line 607**: `core.user_data_registry`
  ```
  with patch('core.user_data_registry.get_user_file_path') as mock_get_path:
  ```

- **Line 612**: `core.user_data_registry`
  ```
  with patch('core.user_data_registry.ensure_user_directory'), \
  ```

- **Line 613**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.load_json_data', return_value=test_account):
  ```

- **Line 630**: `core.user_data_registry`
  ```
  with patch('core.user_data_registry.get_user_file_path') as mock_get_path:
  ```

- **Line 635**: `core.user_data_registry`
  ```
  with patch('core.user_data_registry.ensure_user_directory'), \
  ```

- **Line 636**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.load_json_data', return_value=test_account):
  ```

- **Line 678**: `core.user_data_registry`
  ```
  with patch('core.user_data_registry.get_user_file_path') as mock_get_path:
  ```

- **Line 683**: `core.user_data_registry`
  ```
  with patch('core.user_data_registry.ensure_user_directory'), \
  ```

- **Line 684**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.save_json_data') as mock_save, \
  ```

- **Line 685**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.validate_account_dict') as mock_validate:
  ```

- **Line 706**: `core.user_data_registry`
  ```
  with patch('core.user_data_registry.get_user_file_path', return_value=account_file), \
  ```

- **Line 707**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.ensure_user_directory'), \
  ```

- **Line 708**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.save_json_data') as mock_save, \
  ```

- **Line 709**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.validate_account_dict') as mock_validate, \
  ```

- **Line 710**: `core.user_data_operations`
  ```
  patch('core.user_data_operations.update_user_index'):
  ```

- **Line 779**: `core.user_data_registry`
  ```
  with patch('core.user_data_registry.get_user_file_path') as mock_get_path:
  ```

- **Line 784**: `core.user_data_registry`
  ```
  with patch('core.user_data_registry.ensure_user_directory'), \
  ```

- **Line 785**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.save_json_data') as mock_save, \
  ```

- **Line 786**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.validate_account_dict') as mock_validate_account, \
  ```

- **Line 787**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.validate_preferences_dict') as mock_validate_prefs, \
  ```

- **Line 788**: `core.user_data_operations`
  ```
  patch('core.user_data_operations.update_user_index'):
  ```

- **Line 817**: `core.user_data_registry`
  ```
  with patch('core.user_data_registry.get_user_file_path') as mock_get_path:
  ```

- **Line 822**: `core.user_data_registry`
  ```
  with patch('core.user_data_registry.ensure_user_directory'), \
  ```

- **Line 823**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.save_json_data'), \
  ```

- **Line 824**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.load_json_data') as mock_load, \
  ```

- **Line 825**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.validate_account_dict') as mock_validate:
  ```

- **Line 848**: `core.user_data_registry`
  ```
  with patch('core.user_data_registry.get_user_file_path') as mock_get_path:
  ```

- **Line 853**: `core.user_data_registry`
  ```
  with patch('core.user_data_registry.ensure_user_directory'), \
  ```

- **Line 854**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.load_json_data', return_value=corrupted_data), \
  ```

- **Line 855**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.save_json_data') as mock_save:
  ```

- **Line 877**: `core.user_data_registry`
  ```
  with patch('core.user_data_registry.get_user_file_path') as mock_get_path:
  ```

- **Line 882**: `core.user_data_registry`
  ```
  with patch('core.user_data_registry.ensure_user_directory'), \
  ```

- **Line 883**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.save_json_data') as mock_save, \
  ```

- **Line 884**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.load_json_data', return_value=test_account), \
  ```

- **Line 885**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.validate_account_dict') as mock_validate, \
  ```

- **Line 886**: `core.user_data_operations`
  ```
  patch('core.user_data_operations.update_user_index'):  # Mock the side effect
  ```

- **Line 922**: `core.user_data_registry`
  ```
  with patch('core.user_data_registry.get_user_file_path') as mock_get_path:
  ```

- **Line 927**: `core.user_data_registry`
  ```
  with patch('core.user_data_registry.ensure_user_directory'), \
  ```

- **Line 928**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.save_json_data'), \
  ```

- **Line 929**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.load_json_data', return_value=test_account), \
  ```

- **Line 930**: `core.user_data_registry`
  ```
  patch('core.user_data_registry.validate_account_dict') as mock_validate:
  ```

- **Line 1010**: `core.user_data_operations`
  ```
  from core.user_data_operations import UserDataManager
  ```

- **Line 1025**: `core.user_data_operations`
  ```
  with patch('core.user_data_operations.get_user_info_for_data_manager', return_value={
  ```

- **Line 1041**: `core.user_data_operations`
  ```
  with patch('core.user_data_operations.get_user_data', return_value={
  ```

- **Line 1060**: `core.user_data_operations`
  ```
  with patch('core.user_data_operations.get_user_data', return_value={
  ```

- **Line 1081**: `core.user_data_operations`
  ```
  with patch('core.user_data_operations.get_all_user_ids', return_value=[self.user_id, "user2"]), \
  ```

- **Line 1082**: `core.user_data_operations`
  ```
  patch('core.user_data_operations.get_user_data_summary') as mock_summary, \
  ```

- **Line 1104**: `core.user_data_operations`
  ```
  with patch('core.user_data_operations.get_user_data', side_effect=Exception("Test error")):
  ```

- **Line 1117**: `core.user_data_operations`
  ```
  with patch('core.user_data_operations.get_user_info_for_data_manager', return_value=None):
  ```

- **Line 1128**: `core.user_data_operations`
  ```
  with patch('core.user_data_operations.get_user_data', return_value={
  ```

- **Line 1143**: `core.user_data_operations`
  ```
  with patch('core.user_data_operations.get_all_user_ids', side_effect=Exception("Test error")):
  ```

### tests\conftest.py
**Issues Found**: 2

- **Line 345**: `core.user_data_operations`
  ```
  import core.user_data_operations as udm_module
  ```

- **Line 346**: `core.user_data_operations`
  ```
  from core.user_data_operations import UserDataManager
  ```

### tests\core\test_message_management.py
**Issues Found**: 1

- **Line 16**: `core.user_data_v2_base`
  ```
  from core.user_data_v2_base import SCHEMA_VERSION
  ```

### tests\core\test_user_data_read_scenarios.py
**Issues Found**: 3

- **Line 2**: `core.user_data_read`
  ```
  Scenario-style coverage for core.user_data_read (get/load paths, ID repair).
  ```

- **Line 16**: `core.user_data_operations`
  ```
  from core.user_data_operations import update_user_index
  ```

- **Line 17**: `core.user_data_read`
  ```
  from core.user_data_read import (
  ```

### tests\integration\test_account_lifecycle.py
**Issues Found**: 12

- **Line 14**: `core.user_data_v2_base`
  ```
  from core.user_data_v2_base import SCHEMA_VERSION
  ```

- **Line 169**: `core.user_data_operations`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 232**: `core.user_data_operations`
  ```
  from core.user_data_operations import update_user_index
  ```

- **Line 329**: `core.user_data_operations`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 437**: `core.user_data_operations`
  ```
  from core.user_data_operations import update_user_index
  ```

- **Line 533**: `core.user_data_operations`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 632**: `core.user_data_operations`
  ```
  from core.user_data_operations import update_user_index
  ```

- **Line 720**: `core.user_data_operations`
  ```
  from core.user_data_operations import update_user_index
  ```

- **Line 788**: `core.user_data_operations`
  ```
  from core.user_data_operations import update_user_index
  ```

- **Line 867**: `core.user_data_operations`
  ```
  from core.user_data_operations import update_user_index
  ```

- **Line 937**: `core.user_data_operations`
  ```
  from core.user_data_operations import update_user_index
  ```

- **Line 1004**: `core.user_data_operations`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

### tests\integration\test_account_management.py
**Issues Found**: 5

- **Line 27**: `core.user_data_write`
  ```
  ("User Management", "core.user_data_write", "update_user_account"),
  ```

- **Line 28**: `core.user_data_operations`
  ```
  ("User Data Manager", "core.user_data_operations", "UserDataManager"),
  ```

- **Line 64**: `core.user_data_operations`
  ```
  from core.user_data_operations import UserDataManager
  ```

- **Line 256**: `core.user_data_validation`
  ```
  from core.user_data_validation import validate_user_update
  ```

- **Line 437**: `core.user_data_operations`
  ```
  from core.user_data_operations import update_user_index
  ```

### tests\integration\test_error_handling_improvements.py
**Issues Found**: 1

- **Line 19**: `core.user_data_operations`
  ```
  from core.user_data_operations import UserDataManager
  ```

### tests\integration\test_user_creation.py
**Issues Found**: 5

- **Line 27**: `core.user_data_validation`
  ```
  from core.user_data_validation import is_valid_email
  ```

- **Line 177**: `core.user_data_operations`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 394**: `core.user_data_operations`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 533**: `core.user_data_operations`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 751**: `core.user_data_operations`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

### tests\test_helpers\test_support\conftest_user_data.py
**Issues Found**: 9

- **Line 20**: `core.user_data_v2_base`
  ```
  from core.user_data_v2_base import SCHEMA_VERSION
  ```

- **Line 82**: `core.user_data_registry`
  ```
  import core.user_data_registry as um
  ```

- **Line 104**: `core.user_data_registry`
  ```
  import core.user_data_registry as um
  ```

- **Line 120**: `core.user_data_read`
  ```
  """Shim core.user_data_read.get_user_data to ensure structured dicts.
  ```

- **Line 128**: `core.user_data_registry`
  ```
  import core.user_data_registry as um
  ```

- **Line 129**: `core.user_data_read`
  ```
  import core.user_data_read as read_module
  ```

- **Line 299**: `core.user_data_registry`
  ```
  import core.user_data_registry as um
  ```

- **Line 674**: `core.user_data_operations`
  ```
  from core.user_data_operations import update_user_index
  ```

- **Line 839**: `core.user_data_operations`
  ```
  from core.user_data_operations import update_user_index
  ```

### tests\test_helpers\test_utilities\test_user_factory.py
**Issues Found**: 2

- **Line 1047**: `core.user_data_operations`
  ```
  from core.user_data_operations import update_user_index
  ```

- **Line 1197**: `core.user_data_operations`
  ```
  from core.user_data_operations import update_user_index
  ```

### tests\ui\test_account_creation_ui.py
**Issues Found**: 4

- **Line 927**: `core.user_data_operations`
  ```
  from core.user_data_operations import update_user_index, rebuild_user_index
  ```

- **Line 1218**: `core.user_data_operations`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 1574**: `core.user_data_operations`
  ```
  from core.user_data_operations import update_user_index, rebuild_user_index
  ```

- **Line 2263**: `core.user_data_operations`
  ```
  from core.user_data_operations import build_user_index
  ```

### tests\ui\test_task_settings_widget.py
**Issues Found**: 3

- **Line 378**: `core.user_data_read`
  ```
  with patch('core.user_data_read.get_user_data') as mock_get_data:
  ```

- **Line 412**: `core.user_data_read`
  ```
  with patch('core.user_data_read.get_user_data') as mock_get_data:
  ```

- **Line 413**: `core.user_data_write`
  ```
  with patch('core.user_data_write.update_user_preferences'):
  ```

### tests\ui\test_ui_app_qt_main.py
**Issues Found**: 1

- **Line 658**: `core.user_data_operations`
  ```
  with patch('core.user_data_operations.rebuild_user_index') as mock_rebuild:
  ```

### tests\ui\test_widget_behavior.py
**Issues Found**: 1

- **Line 328**: `core.user_data_operations`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

### tests\unit\test_recurring_tasks.py
**Issues Found**: 4

- **Line 13**: `core.user_data_v2_base`
  ```
  from core.user_data_v2_base import SCHEMA_VERSION
  ```

- **Line 55**: `core.user_item_storage`
  ```
  @patch('core.user_item_storage.get_user_data_dir')
  ```

- **Line 86**: `core.user_item_storage`
  ```
  @patch('core.user_item_storage.get_user_data_dir')
  ```

- **Line 187**: `core.user_item_storage`
  ```
  @patch('core.user_item_storage.get_user_data_dir')
  ```

### tests\unit\test_task_short_ids.py
**Issues Found**: 1

- **Line 5**: `core.user_data_v2_base`
  ```
  from core.user_data_v2_base import generate_short_id
  ```

### tests\unit\test_user_data_handlers.py
**Issues Found**: 3

- **Line 443**: `core.user_data_write`
  ```
  with patch('core.user_data_write.save_user_data', side_effect=Exception("Test error")):
  ```

- **Line 523**: `core.user_data_operations`
  ```
  with patch('core.user_data_operations.UserDataManager') as mock_manager_class:
  ```

- **Line 546**: `core.user_data_operations`
  ```
  with patch('core.user_data_operations.update_user_index'):
  ```

### tests\unit\test_user_data_loader_idempotency.py
**Issues Found**: 2

- **Line 12**: `core.user_data_registry`
  ```
  um = importlib.import_module('core.user_data_registry')
  ```

- **Line 13**: `core.user_data_registry`
  ```
  udh = importlib.import_module('core.user_data_registry')
  ```

### tests\unit\test_user_data_loader_order_insensitivity.py
**Issues Found**: 4

- **Line 22**: `core.user_data_registry`
  ```
  um1, udh1 = _reload_in_order('core.user_data_registry', 'core.user_data_registry')
  ```

- **Line 22**: `core.user_data_registry`
  ```
  um1, udh1 = _reload_in_order('core.user_data_registry', 'core.user_data_registry')
  ```

- **Line 36**: `core.user_data_registry`
  ```
  udh2, um2 = _reload_in_order('core.user_data_registry', 'core.user_data_registry')
  ```

- **Line 36**: `core.user_data_registry`
  ```
  udh2, um2 = _reload_in_order('core.user_data_registry', 'core.user_data_registry')
  ```

### tests\unit\test_user_data_manager.py
**Issues Found**: 21

- **Line 21**: `core.user_data_operations`
  ```
  from core.user_data_operations import (
  ```

- **Line 50**: `core.user_data_operations`
  ```
  with patch('core.user_data_operations.BASE_DATA_DIR', test_data_dir), \
  ```

- **Line 51**: `core.user_data_operations`
  ```
  patch('core.user_data_operations.get_backups_dir', return_value=os.path.join(test_data_dir, 'backups')):
  ```

- **Line 87**: `core.user_data_operations`
  ```
  with patch('core.user_data_operations.BASE_DATA_DIR', test_data_dir), \
  ```

- **Line 88**: `core.user_data_operations`
  ```
  patch('core.user_data_operations.get_backups_dir', return_value=backup_dir):
  ```

- **Line 104**: `core.user_data_operations`
  ```
  with patch('core.user_data_operations.BASE_DATA_DIR', test_data_dir), \
  ```

- **Line 105**: `core.user_data_operations`
  ```
  patch('core.user_data_operations.get_backups_dir', return_value=os.path.join(test_data_dir, 'backups')):
  ```

- **Line 202**: `core.user_data_operations`
  ```
  with patch('core.user_data_operations.BASE_DATA_DIR', test_data_dir), \
  ```

- **Line 203**: `core.user_data_operations`
  ```
  patch('core.user_data_operations.get_backups_dir', return_value=os.path.join(test_data_dir, 'backups')):
  ```

- **Line 282**: `core.user_data_operations`
  ```
  with patch('core.user_data_operations.BASE_DATA_DIR', test_data_dir), \
  ```

- **Line 283**: `core.user_data_operations`
  ```
  patch('core.user_data_operations.get_backups_dir', return_value=os.path.join(test_data_dir, 'backups')):
  ```

- **Line 346**: `core.user_data_operations`
  ```
  with patch('core.user_data_operations.BASE_DATA_DIR', test_data_dir), \
  ```

- **Line 347**: `core.user_data_operations`
  ```
  patch('core.user_data_operations.get_backups_dir', return_value=os.path.join(test_data_dir, 'backups')):
  ```

- **Line 358**: `core.user_data_operations`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 389**: `core.user_data_operations`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

- **Line 499**: `core.user_data_operations`
  ```
  with patch('core.user_data_operations.BASE_DATA_DIR', test_data_dir), \
  ```

- **Line 500**: `core.user_data_operations`
  ```
  patch('core.user_data_operations.get_backups_dir', return_value=os.path.join(test_data_dir, 'backups')):
  ```

- **Line 572**: `core.user_data_operations`
  ```
  with patch('core.user_data_operations.BASE_DATA_DIR', test_data_dir), \
  ```

- **Line 573**: `core.user_data_operations`
  ```
  patch('core.user_data_operations.get_backups_dir', return_value=os.path.join(test_data_dir, 'backups')):
  ```

- **Line 808**: `core.user_data_operations`
  ```
  with patch('core.user_data_operations.BASE_DATA_DIR', test_data_dir), \
  ```

- **Line 809**: `core.user_data_operations`
  ```
  patch('core.user_data_operations.get_backups_dir', return_value=os.path.join(test_data_dir, 'backups')):
  ```

### tests\unit\test_user_data_v2_runtime.py
**Issues Found**: 1

- **Line 232**: `core.user_item_storage`
  ```
  monkeypatch.setattr("core.user_item_storage.get_user_data_dir", lambda _user_id: str(user_root))
  ```

### tests\unit\test_user_data_validation_user_id.py
**Issues Found**: 2

- **Line 1**: `core.user_data_validation`
  ```
  """Unit tests for core.user_data_validation.is_valid_user_id."""
  ```

- **Line 5**: `core.user_data_validation`
  ```
  from core.user_data_validation import is_valid_user_id
  ```

### tests\unit\test_user_item_storage.py
**Issues Found**: 15

- **Line 5**: `core.user_item_storage`
  ```
  from core.user_item_storage import (
  ```

- **Line 24**: `core.user_item_storage`
  ```
  monkeypatch.setattr("core.user_item_storage.get_user_data_dir", lambda _uid: "")
  ```

- **Line 28**: `core.user_item_storage`
  ```
  monkeypatch.setattr("core.user_item_storage.get_user_subdir_path", lambda *_args, **_kwargs: None)
  ```

- **Line 32**: `core.user_item_storage`
  ```
  monkeypatch.setattr("core.user_item_storage.get_user_subdir_path", lambda *_args, **_kwargs: None)
  ```

- **Line 37**: `core.user_item_storage`
  ```
  monkeypatch.setattr("core.user_item_storage.get_user_subdir_path", lambda *_args, **_kwargs: Path(tmp_path))
  ```

- **Line 38**: `core.user_item_storage`
  ```
  monkeypatch.setattr("core.user_item_storage.load_json_data", lambda _path: None)
  ```

- **Line 44**: `core.user_item_storage`
  ```
  monkeypatch.setattr("core.user_item_storage.get_user_subdir_path", lambda *_args, **_kwargs: Path(tmp_path))
  ```

- **Line 45**: `core.user_item_storage`
  ```
  monkeypatch.setattr("core.user_item_storage.load_json_data", lambda _path: {"not": "a list"})
  ```

- **Line 51**: `core.user_item_storage`
  ```
  monkeypatch.setattr("core.user_item_storage.get_user_subdir_path", lambda *_args, **_kwargs: Path(tmp_path))
  ```

- **Line 52**: `core.user_item_storage`
  ```
  monkeypatch.setattr("core.user_item_storage.load_json_data", lambda _path: {"tasks": [{"id": 1}]})
  ```

- **Line 57**: `core.user_item_storage`
  ```
  monkeypatch.setattr("core.user_item_storage.get_user_subdir_path", lambda *_args, **_kwargs: Path(tmp_path))
  ```

- **Line 58**: `core.user_item_storage`
  ```
  monkeypatch.setattr("core.user_item_storage.load_json_data", lambda _path: [{"id": 1}])
  ```

- **Line 64**: `core.user_item_storage`
  ```
  monkeypatch.setattr("core.user_item_storage.ensure_user_subdir", lambda *_args, **_kwargs: None)
  ```

- **Line 68**: `core.user_item_storage`
  ```
  monkeypatch.setattr("core.user_item_storage.ensure_user_subdir", lambda *_args, **_kwargs: Path(tmp_path))
  ```

- **Line 69**: `core.user_item_storage`
  ```
  monkeypatch.setattr("core.user_item_storage.save_json_data", lambda _data, _path: True)
  ```

### tests\unit\test_user_management.py
**Issues Found**: 1

- **Line 532**: `core.user_data_operations`
  ```
  from core.user_data_operations import rebuild_user_index
  ```

### tests\unit\test_validation.py
**Issues Found**: 5

- **Line 14**: `core.user_data_validation`
  ```
  from core.user_data_validation import (
  ```

- **Line 218**: `core.user_data_read`
  ```
  with patch('core.user_data_read.get_user_data') as mock_get_data:
  ```

- **Line 239**: `core.user_data_read`
  ```
  with patch('core.user_data_read.get_user_data') as mock_get_data:
  ```

- **Line 266**: `core.user_data_read`
  ```
  with patch('core.user_data_read.get_user_data') as mock_get_data:
  ```

- **Line 289**: `core.user_data_read`
  ```
  with patch('core.user_data_read.get_user_data') as mock_get_data:
  ```

### tests\unit\test_webhook_handler_gap_coverage.py
**Issues Found**: 1

- **Line 76**: `core.user_data_write`
  ```
  "core.user_data_write.update_user_account",
  ```

## Legacy Compatibility Markers
**Files Affected**: 10

### core\runtime_state_storage.py
**Issues Found**: 1

- **Line 1**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Temporary bridge for old core.runtime_state_storage imports.
  ```

### core\service_flag_storage.py
**Issues Found**: 1

- **Line 1**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Temporary bridge for old core.service_flag_storage imports.
  ```

### core\user_data_operations.py
**Issues Found**: 1

- **Line 1**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Temporary bridge for old core.user_data_operations imports.
  ```

### core\user_data_presets.py
**Issues Found**: 1

- **Line 1**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Temporary bridge for old core.user_data_presets imports.
  ```

### core\user_data_read.py
**Issues Found**: 1

- **Line 1**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Temporary bridge for old core.user_data_read imports.
  ```

### core\user_data_registry.py
**Issues Found**: 1

- **Line 1**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Temporary bridge for old core.user_data_registry imports.
  ```

### core\user_data_v2_base.py
**Issues Found**: 1

- **Line 1**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Temporary bridge for old core.user_data_v2_base imports.
  ```

### core\user_data_validation.py
**Issues Found**: 1

- **Line 1**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Temporary bridge for old core.user_data_validation imports.
  ```

### core\user_data_write.py
**Issues Found**: 1

- **Line 1**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Temporary bridge for old core.user_data_write imports.
  ```

### core\user_item_storage.py
**Issues Found**: 1

- **Line 1**: `# LEGACY COMPATIBILITY:`
  ```
  # LEGACY COMPATIBILITY: Temporary bridge for old core.user_item_storage imports.
  ```
