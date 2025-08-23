# Legacy Code Management Strategy

## Overview

This document outlines our systematic approach to managing legacy code in the MHM project. Instead of arbitrary "cleanup," we follow a structured process that ensures we understand the purpose, track usage, and have clear removal criteria for every piece of legacy code.

## Core Principles

### 1. **Purpose-Driven Documentation**
Every legacy code section must have:
- **Clear explanation** of why it exists
- **Specific removal criteria** 
- **Usage tracking plan**
- **Removal timeline**

### 2. **Usage-Based Removal**
Legacy code is only removed when:
- **Usage is tracked** and confirmed minimal/zero
- **Removal criteria are met**
- **Impact is understood**

### 3. **No Arbitrary Cleanup**
We don't remove legacy code just because it "looks old" or "could be cleaner." We remove it when it's safe and beneficial.

## Legacy Code Categories

### Category 1: **Functional Legacy Code** (Callable Functions/Methods)
- **Examples**: Legacy methods with usage logging
- **Management**: Add warning logs, track usage, remove when unused
- **Documentation**: `LEGACY COMPATIBILITY` headers with removal plans

### Category 2: **Configuration Legacy Code** (Environment Variables, Settings)
- **Examples**: `LOG_FILE_PATH` environment variable
- **Management**: Document purpose, track external usage, remove when safe
- **Documentation**: Clear explanation of why it exists and removal criteria

### Category 3: **Import Legacy Code** (Import Statements, Dependencies)
- **Examples**: Old import statements kept for compatibility
- **Management**: Track which modules still use them, remove when all updated
- **Documentation**: List of modules that need updating

### Category 4: **Data Structure Legacy Code** (File Formats, JSON Structures)
- **Examples**: Backward compatibility in user data files
- **Management**: Maintain compatibility, warn about deprecated fields
- **Documentation**: Migration plans and timeline

## Current Legacy Code Inventory

### Configuration Legacy Code

#### `LOG_FILE_PATH` Environment Variable ✅ **COMPLETED**
- **Location**: `core/config.py` lines 50, 126
- **Purpose**: Was intended to allow external configuration of log file path
- **Problem**: Line 126 overwrites the env var, making it useless
- **Status**: ✅ **REMOVED** - No external dependencies found
- **Removal Criteria**: 
  1. ✅ Confirm no external scripts use `LOG_FILE_PATH` env var
  2. ✅ Update `core/logger.py` to import `LOG_MAIN_FILE` from config
  3. ✅ Remove both line 50 (env var handling) and line 126 (overwrite)
- **Usage Tracking**: ✅ No external usage found - safe to remove
- **Files Updated**: `core/logger.py`, `core/service.py`, `ui/ui_app_qt.py`

#### Import Legacy Code

#### `load_user_preferences_data` Import ✅ **DOCUMENTED**
- **Location**: `tasks/task_management.py` line 19
- **Purpose**: Transition from old individual load functions to unified `get_user_data`
- **Status**: ✅ **PROPERLY DOCUMENTED** - Added removal plan and usage tracking
- **Removal Criteria**: All callers updated to use `get_user_data(user_id, 'preferences')`
- **Usage Tracking**: Search for remaining calls to `load_user_preferences_data`

#### `load_user_*_data` Imports ✅ **DOCUMENTED**
- **Location**: `communication/command_handlers/interaction_handlers.py` line 23
- **Purpose**: Transition from old individual load functions to unified `get_user_data`
- **Status**: ✅ **PROPERLY DOCUMENTED** - Added removal plan and usage tracking
- **Removal Criteria**: All callers updated to use `get_user_data(user_id, data_type)`
- **Usage Tracking**: Search for remaining calls to individual load functions

#### Redundant FLOW_CHECKIN Assignment ✅ **DOCUMENTED**
- **Location**: `communication/message_processing/conversation_flow_manager.py` line 44
- **Purpose**: Redundant assignment for backward compatibility
- **Status**: ✅ **PROPERLY DOCUMENTED** - Added removal plan and usage tracking
- **Removal Criteria**: All references updated to use FLOW_CHECKIN directly
- **Usage Tracking**: Monitor for any remaining references to this constant

#### Legacy Compatibility Methods ✅ **COMPLETED**
- **Location**: `communication/core/channel_orchestrator.py` line 1023
- **Purpose**: Methods for backward compatibility
- **Status**: ✅ **COMPLETED** - All callers updated to use new channel management methods
- **Removal Criteria**: ✅ **MET** - All callers updated to use new specific methods
- **Usage Tracking**: ✅ **ACTIVE** - Warning logs will show when legacy methods are called
- **New Methods Added**:
  - `get_active_channels()` - Returns currently active/running channels
  - `get_configured_channels()` - Returns channels from configuration
  - `get_registered_channels()` - Returns channels registered in factory
- **Files Updated**: 
  - `tests/behavior/test_communication_behavior.py` - Updated to use new methods
  - `tests/ui/test_account_creation_ui.py` - Updated to use new methods
  - `communication/core/factory.py` - Added `get_registered_channels()` method
- **Note**: The `get_available_channels()` function in `core/config.py` serves a different purpose (determining configured channels from environment variables) and should remain as-is.

#### Simple Mapping Fallback ✅ **HELPER FUNCTION RENAMING COMPLETED**
- **Location**: `core/user_management.py` line 792
- **Purpose**: Check simple mapping first for performance
- **Status**: ✅ **HELPER FUNCTION RENAMING COMPLETED** - All helper functions renamed to follow `_main_function__helper_name` pattern
- **Removal Criteria**: ✅ **MET** - All code now uses new multi-identifier structure
- **Usage Tracking**: ✅ **COMPLETED** - Legacy comments and warning logs removed
- **Migration Results**:
  - ✅ **50 function calls migrated** across 14 files
  - ✅ **All import statements updated** to use get_user_id_by_identifier
  - ✅ **Legacy functions renamed** to follow helper function naming convention
  - ✅ **Legacy comments and warnings removed** - Clean codebase
  - ✅ **System tested** and confirmed working
- **Helper Function Renaming**:
  - `get_user_id_by_internal_username` → `_get_user_id_by_identifier__by_internal_username`
  - `get_user_id_by_email` → `_get_user_id_by_identifier__by_email`
  - `get_user_id_by_phone` → `_get_user_id_by_identifier__by_phone`
  - `get_user_id_by_chat_id` → `_get_user_id_by_identifier__by_chat_id`
  - `get_user_id_by_discord_user_id` → `_get_user_id_by_identifier__by_discord_user_id`
- **Files Updated**:
  - `communication/communication_channels/discord/bot.py` - 3 calls migrated
  - `communication/communication_channels/discord/event_handler.py` - 1 call migrated
  - `tests/test_utilities.py` - 2 calls migrated
  - `tests/behavior/test_account_management_real_behavior.py` - 7 calls migrated
  - `tests/behavior/test_ai_chatbot_behavior.py` - 1 call migrated
  - `tests/behavior/test_conversation_behavior.py` - 1 call migrated
  - `tests/behavior/test_discord_bot_behavior.py` - 9 calls migrated
  - `tests/behavior/test_interaction_handlers_behavior.py` - 2 calls migrated
  - `tests/behavior/test_user_context_behavior.py` - 1 call migrated
  - `tests/behavior/test_utilities_demo.py` - 15 calls migrated
  - `tests/integration/test_account_lifecycle.py` - 2 calls migrated
  - `tests/integration/test_user_creation.py` - 3 calls migrated
  - `tests/unit/test_user_management.py` - 2 calls migrated
  - `ui/dialogs/account_creator_dialog.py` - 1 call migrated
- **Next Steps**: ✅ **COMPLETED** - All legacy code cleanup and helper function renaming complete

#### Synchronous Interface Methods ✅ **DOCUMENTED**
- **Location**: `communication/communication_channels/discord/bot.py` line 1282
- **Purpose**: Synchronous interface for testing and backward compatibility
- **Status**: ✅ **PROPERLY DOCUMENTED** - Added removal plan and usage tracking
- **Removal Criteria**: All tests migrated to use async initialize() method
- **Usage Tracking**: Monitor for calls to start() and stop() methods

## Removal Process

### Step 1: **Document and Track**
- Add proper `LEGACY COMPATIBILITY` documentation
- Implement usage tracking (logs, monitoring)
- Define clear removal criteria

### Step 2: **Monitor Usage**
- Track actual usage over time
- Identify external dependencies
- Document migration needs

### Step 3: **Plan Migration**
- Create migration plan for external dependencies
- Update internal callers
- Test thoroughly

### Step 4: **Remove Safely**
- Remove only when criteria are met
- Update documentation
- Monitor for issues

## Examples of Proper Legacy Documentation

### Functional Legacy Code
```python
# LEGACY COMPATIBILITY: Synchronous interface for testing and backward compatibility
# TODO: Remove after migrating all tests to use async initialize() method
# REMOVAL PLAN:
# 1. Update behavior tests to use async initialize() instead of start()
# 2. Update communication manager to use shutdown() instead of stop()
# 3. Monitor usage for 1 week after migration
# 4. Remove legacy methods if no usage detected
```

### Configuration Legacy Code
```python
# LEGACY COMPATIBILITY: LOG_FILE_PATH env is deprecated. We now always derive
# the main log file path from LOGS_DIR/LOG_MAIN_FILE to ensure consistent
# component-based logging without noisy warnings.
# TODO: Remove after confirming no external scripts or configs depend on LOG_FILE_PATH env var
# REMOVAL PLAN:
# 1. Search for any external usage of LOG_FILE_PATH environment variable
# 2. Update any external scripts/configs to use LOG_MAIN_FILE directly
# 3. Remove this line and the env var handling on line 50
# 4. Update core/logger.py to import LOG_MAIN_FILE from config instead of defining LOG_FILE_PATH
# USAGE TRACKING: Monitor for any environment variable LOG_FILE_PATH usage in external scripts
```

## Success Metrics

- **Zero arbitrary removals**: Every removal has clear justification
- **Complete documentation**: All legacy code properly documented
- **Usage tracking**: All legacy code usage is monitored
- **Safe removals**: No breaking changes from legacy code removal
- **Clear criteria**: Every piece of legacy code has defined removal criteria

## Next Steps

1. **Audit current legacy code**: Identify all legacy code sections
2. **Document properly**: Add proper documentation to all legacy code
3. **Implement tracking**: Add usage tracking where appropriate
4. **Create removal plans**: Define specific removal criteria for each item
5. **Monitor and remove**: Follow the process to safely remove legacy code
