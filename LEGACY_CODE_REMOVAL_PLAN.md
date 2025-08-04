# Legacy Code Removal Plan

> **Purpose**: Remove all legacy/compatibility code with clear marking and removal plans  
> **Status**: **ACTIVE** - All legacy code must be marked and have removal plans  
> **Version**: 1.0.0  
> **Last Updated**: 2025-07-28

## 🎯 **Core Principle**

**No legacy/compatibility code should exist without:**
1. **Clear marking** as legacy compatibility code
2. **Documented removal plan** with specific steps
3. **Timeline** for removal
4. **Verification process** to ensure safe removal

## 🚨 **Current Legacy Code Inventory**

### **1. Schedule Management Legacy Keys** ⚠️ **HIGH PRIORITY**

**Location**: `core/schedule_management.py`
**Issue**: Support for legacy `'start'`/`'end'` keys alongside canonical `'start_time'`/`'end_time'`

**Legacy Code Found:**
- `get_schedule_time_periods()` - Lines 70-75: Legacy key support
- `migrate_legacy_schedule_keys()` - Lines 573-614: Migration function

**Current Status**: ✅ **MARKED** - Clear comments and removal plan added

**Removal Plan:**
1. **Run Migration Script**: Execute `migrate_legacy_schedule_keys()` on all users
2. **Verify Data**: Check that no legacy keys remain in any user data
3. **Remove Legacy Support**: Remove `start`/`end` key handling from `get_schedule_time_periods()`
4. **Remove Migration Function**: Delete `migrate_legacy_schedule_keys()` entirely
5. **Update Tests**: Ensure all tests use canonical keys only

**Timeline**: Complete by 2025-08-01

### **1a. Schedule Management Legacy Format** ⚠️ **HIGH PRIORITY**

**Location**: `core/schedule_management.py`
**Issue**: Support for legacy format without periods wrapper (direct period data vs `{'enabled': true, 'periods': {...}}`)

**Legacy Code Found:**
- `get_schedule_time_periods()` - Lines 52-58: Legacy format handling
- `set_schedule_periods()` - Lines 475-491: Legacy format migration

**Current Status**: ✅ **MARKED** - Clear comments and removal plan added
**Data Status**: ✅ **VERIFIED** - All users already use periods wrapper format

**Removal Plan:**
1. **Verify Data**: Check that no legacy format remains in any user data (✅ COMPLETE)
2. **Remove Legacy Handling**: Remove legacy format handling from `get_schedule_time_periods()`
3. **Remove Legacy Migration**: Remove legacy format migration from `set_schedule_periods()`
4. **Update Tests**: Ensure all tests use periods wrapper format only

**Timeline**: Complete by 2025-08-01

### **2. User Data Access Legacy Wrappers** ⚠️ **MEDIUM PRIORITY**

**Location**: `core/user_data_handlers.py`
**Issue**: Legacy wrapper functions for backward compatibility

**Current Status**: ⚠️ **MONITORING** - Check `app.log` for "LEGACY" warnings

**Removal Plan:**
1. **Monitor Logs**: Watch for any remaining "LEGACY" warnings in `app.log`
2. **Update Call Sites**: Replace any remaining legacy calls with modern equivalents
3. **Remove Wrappers**: Delete legacy wrapper functions once no warnings appear

**Timeline**: Complete when no legacy warnings appear for 1 week

### **3. Account Creator Dialog Compatibility Methods** ⚠️ **LOW PRIORITY**

**Location**: `ui/dialogs/account_creator_dialog.py`
**Issue**: Methods marked as "kept for compatibility but no longer needed"

**Legacy Code Found:**
- Lines 326-347: Multiple compatibility methods

**Removal Plan:**
1. **Verify Unused**: Confirm these methods are not called anywhere
2. **Remove Methods**: Delete the compatibility methods
3. **Update Documentation**: Remove references to these methods

**Timeline**: Complete by 2025-08-15

### **4. User Profile Settings Widget Legacy Fallbacks** ⚠️ **LOW PRIORITY**

**Location**: `ui/widgets/user_profile_settings_widget.py`
**Issue**: Legacy fallback code for data loading

**Legacy Code Found:**
- Lines 395, 402, 426, 450, 462: Legacy fallback comments

**Removal Plan:**
1. **Verify Modern Path**: Ensure modern data loading works correctly
2. **Remove Fallbacks**: Delete legacy fallback code
3. **Test Thoroughly**: Verify widget still works without fallbacks

**Timeline**: Complete by 2025-08-15

### **5. Discord Bot Legacy Methods** ⚠️ **LOW PRIORITY**

**Location**: `bot/discord_bot.py`
**Issue**: Legacy methods for backward compatibility

**Legacy Code Found:**
- Lines 518-564: Legacy start/stop methods

**Removal Plan:**
1. **Verify Unused**: Confirm no code calls these legacy methods
2. **Remove Methods**: Delete legacy compatibility methods
3. **Update Documentation**: Remove references to legacy methods

**Timeline**: Complete by 2025-08-15

### **6. Communication Manager Legacy Wrappers** ⚠️ **HIGH PRIORITY**

**Location**: `bot/communication_manager.py`
**Issue**: LegacyChannelWrapper and legacy channel access for backward compatibility

**Legacy Code Found:**
- `LegacyChannelWrapper` class (Lines 1064-1216): Complete legacy wrapper
- `_create_legacy_channel_access()` method (Lines 390-398): Creates legacy wrappers
- `channels` property (Lines 410-420): Returns legacy wrappers when available
- Legacy method calls: `is_initialized()`, `start()`, `stop()`, `send_message()`, `receive_messages()`

**Current Status**: ✅ **MARKED** - Clear comments and removal plan added with usage logging

**Removal Plan:**
1. **Monitor Logs**: Watch for "LEGACY" warnings in `app.log` for 1 week
2. **Verify Unused**: Confirm no code actually uses legacy interface
3. **Remove LegacyChannelWrapper**: Delete entire class if unused
4. **Remove Legacy Access**: Remove `_create_legacy_channel_access()` method
5. **Update Channels Property**: Return `_channels_dict` directly
6. **Update Tests**: Remove legacy wrapper tests

**Timeline**: Complete after 1 week of monitoring (no legacy usage detected)

### **7. Account Creator Dialog Compatibility Methods** ⚠️ **HIGH PRIORITY**

**Location**: `ui/dialogs/account_creator_dialog.py`
**Issue**: Multiple methods kept for compatibility but no longer needed

**Legacy Code Found:**
- `on_category_changed()` method (Lines 326-340): Legacy signal-based category handling
- `on_service_changed()` method (Lines 342-356): Legacy signal-based service handling
- `on_contact_info_changed()` method (Lines 358-372): Legacy signal-based contact handling
- `on_task_group_toggled()` method (Lines 374-388): Legacy group toggle approach
- `on_checkin_group_toggled()` method (Lines 390-404): Legacy group toggle approach

**Current Status**: ✅ **MARKED** - Clear comments and removal plan added with usage logging

**Removal Plan:**
1. **Monitor Logs**: Watch for "LEGACY" warnings in `app.log` for 1 week
2. **Verify Unused**: Confirm no code actually uses legacy signal-based methods
3. **Remove Methods**: Delete all 5 compatibility methods if unused
4. **Update Documentation**: Remove references to legacy signal-based approach

**Timeline**: Complete after 1 week of monitoring (no legacy usage detected)

### **8. User Profile Settings Widget Legacy Fallbacks** ⚠️ **HIGH PRIORITY**

**Location**: `ui/widgets/user_profile_settings_widget.py`
**Issue**: Multiple legacy fallbacks for dynamic list containers

**Legacy Code Found:**
- Health conditions fallback (Lines 395-402): Legacy checkbox group approach
- Medications fallback (Lines 404-426): Legacy checkbox and text field approach
- Allergies fallback (Lines 428-450): Legacy checkbox and text field approach
- Interests fallback (Lines 452-462): Legacy checkbox group approach
- Goals fallback (Lines 464-486): Legacy checkbox and text field approach

**Current Status**: ✅ **MARKED** - Clear comments and removal plan added with usage logging

**Removal Plan:**
1. **Monitor Logs**: Watch for "LEGACY" warnings in `app.log` for 1 week
2. **Verify Unused**: Confirm all UI uses dynamic list containers
3. **Remove Fallbacks**: Delete all 5 legacy fallback blocks if unused
4. **Update UI**: Ensure all dialogs use dynamic list containers

**Timeline**: Complete after 1 week of monitoring (no legacy usage detected)

### **9. User Context Legacy Format Conversion** ⚠️ **MEDIUM PRIORITY**

**Location**: `user/user_context.py`
**Issue**: Converting between legacy and new data formats

**Legacy Code Found:**
- Legacy format conversion (Lines 50-65): Converting new data structure to legacy format
- Legacy format extraction (Lines 81-95): Converting legacy format to new data structure

**Current Status**: ✅ **MARKED** - Clear comments and removal plan added with usage logging

**Removal Plan:**
1. **Monitor Logs**: Watch for "LEGACY" warnings in `app.log` for 1 week
2. **Verify Unused**: Confirm no code uses legacy data format
3. **Remove Conversion**: Delete format conversion and extraction code
4. **Update Code**: Ensure all code uses new data structure directly

**Timeline**: Complete after 1 week of monitoring (no legacy usage detected)

### **10. Test Utilities Backward Compatibility** ⚠️ **LOW PRIORITY**

**Location**: `tests/test_utilities.py`
**Issue**: Multiple backward compatibility paths for test data directories

**Legacy Code Found:**
- Multiple "Use real user directory (for backward compatibility)" comments throughout file
- Legacy test user creation paths that don't use test_data_dir parameter

**Current Status**: ✅ **MARKED** - Clear comments and removal plan added with usage logging

**Removal Plan:**
1. **Monitor Logs**: Watch for "LEGACY" warnings in `app.log` for 1 week
2. **Verify Unused**: Confirm all tests use test_data_dir parameter
3. **Remove Paths**: Delete legacy test user creation paths
4. **Update Tests**: Ensure all tests use modern test data directory approach

**Timeline**: Complete after 1 week of monitoring (no legacy usage detected)

### **11. UI App Legacy Communication Manager** ⚠️ **LOW PRIORITY**

**Location**: `ui/ui_app_qt.py`
**Issue**: Legacy communication manager instance handling

**Legacy Code Found:**
- Legacy communication manager shutdown (Line 1496): Handling UI-created communication manager instances

**Current Status**: ✅ **MARKED** - Clear comments and removal plan added with usage logging

**Removal Plan:**
1. **Monitor Logs**: Watch for "LEGACY" warnings in `app.log` for 1 week
2. **Verify Unused**: Confirm no UI creates communication manager instances
3. **Remove Handling**: Delete legacy communication manager shutdown code
4. **Update Code**: Ensure all code uses service-based communication

**Timeline**: Complete after 1 week of monitoring (no legacy usage detected)

## 📋 **Legacy Code Marking Standards**

### **Required Comments for All Legacy Code:**

```python
# LEGACY COMPATIBILITY: [Brief description of what this supports]
# TODO: Remove after [specific condition]
# REMOVAL PLAN: 
# 1. [Step 1]
# 2. [Step 2]
# 3. [Step 3]
# 4. [Step 4]
```

### **Required Function Documentation:**

```python
def legacy_function():
    """
    [Description]
    
    LEGACY COMPATIBILITY FUNCTION - REMOVE AFTER [condition]
    """
```

## 🔍 **Verification Process**

### **Before Removing Any Legacy Code:**

1. **Run Full Test Suite**: `python run_tests.py`
2. **Check Application Logs**: Look for any "LEGACY" warnings
3. **Test User Data**: Verify all user data uses modern format
4. **Manual Testing**: Test affected functionality thoroughly
5. **Documentation Update**: Update all relevant documentation

### **After Removing Legacy Code:**

1. **Run Full Test Suite**: Ensure all tests pass
2. **Check Application Logs**: Verify no new errors
3. **Manual Testing**: Test affected functionality
4. **Update Documentation**: Remove references to removed code
5. **Update TODO.md**: Mark task as completed

## 📊 **Progress Tracking**

### **Completed Tasks:**
- [x] **Schedule Management Legacy Keys**: Marked with removal plan
- [x] **Migration Function**: Marked with removal plan
- [x] **Schedule Management Legacy Format**: Marked with removal plan
- [x] **Legacy Format Verification**: Confirmed all users use periods wrapper

### **Pending Tasks:**
- [ ] **Run Schedule Migration**: Execute migration script
- [ ] **Remove Schedule Legacy Support**: Remove legacy key handling
- [ ] **Remove Schedule Legacy Format**: Remove legacy format handling
- [ ] **Remove Migration Function**: Delete migration function
- [ ] **Monitor User Data Wrappers**: Watch for legacy warnings
- [ ] **Monitor Communication Manager Legacy**: Watch for legacy warnings (1 week)
- [ ] **Remove Communication Manager Legacy**: Remove wrappers if unused
- [ ] **Monitor Account Creator Dialog Legacy**: Watch for legacy warnings (1 week)
- [ ] **Remove Account Creator Dialog Legacy**: Remove unused methods if no usage detected
- [ ] **Monitor User Profile Widget Legacy**: Watch for legacy warnings (1 week)
- [ ] **Remove User Profile Widget Legacy**: Remove fallbacks if no usage detected
- [ ] **Monitor User Context Legacy**: Watch for legacy warnings (1 week)
- [ ] **Remove User Context Legacy**: Remove format conversion if no usage detected
- [ ] **Monitor Test Utilities Legacy**: Watch for legacy warnings (1 week)
- [ ] **Remove Test Utilities Legacy**: Remove backward compatibility paths if no usage detected
- [ ] **Monitor UI App Legacy**: Watch for legacy warnings (1 week)
- [ ] **Remove UI App Legacy**: Remove communication manager handling if no usage detected
- [ ] **Remove Discord Bot Legacy**: Remove unused methods

## 🎯 **Success Criteria**

**Legacy code removal is complete when:**
1. ✅ No legacy compatibility code exists in the codebase
2. ✅ All data uses modern, consistent formats
3. ✅ No "LEGACY" warnings appear in application logs
4. ✅ All tests pass with modern code only
5. ✅ Documentation reflects current state only
6. ✅ No backward compatibility functions remain

## 📝 **Notes**

- **Conservative Approach**: Only remove legacy code when 100% certain it's safe
- **Documentation First**: Always update documentation before removing code
- **Test Thoroughly**: Run comprehensive tests before and after removal
- **Monitor Logs**: Watch application logs for any issues after removal

---

**Remember**: Legacy code removal is about maintaining code quality and reducing complexity. Take the time to do it right! 