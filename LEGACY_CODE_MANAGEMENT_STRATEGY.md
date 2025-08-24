# Legacy Code Management Strategy

## 🎯 Overview

This document outlines the strategy for managing legacy code in the MHM project, ensuring clean, maintainable code while preserving functionality during transitions.

## 📋 Current Legacy Code Inventory

### Active Legacy Code Items

1. **User Data Function Naming Inconsistency** - Individual loader functions need helper function naming convention
2. **Legacy Wrapper Methods** - UserContext.load_user_data() and UserContext.save_user_data() methods
3. **Mixed Import Patterns** - Some modules still import individual loader functions directly

## 🔄 Refactoring Plans

### Plan 1: User Data Function Cleanup and Standardization

**Objective**: Standardize all user data loading/saving functions to follow consistent naming conventions and architecture patterns.

**Current State Analysis**:
- Primary API: `get_user_data()`, `save_user_data()` (implementation functions)
- Individual loaders: `load_user_*_data()`, `save_user_*_data()` (should be helper functions)
- Legacy wrappers: `UserContext.load_user_data()`, `UserContext.save_user_data()` (redundant)

**Target State**:
- Primary API: `get_user_data()`, `save_user_data()` (implementation functions)
- Helper functions: `_get_user_data__load_*()`, `_save_user_data__save_*()` (helper functions)
- Remove: Legacy wrapper methods

**Step-by-Step Implementation Plan**:

#### Phase 1: Preparation and Backup
1. **Create comprehensive backup**
   ```powershell
   Copy-Item -Path "." -Destination "../backup_user_data_refactor_$(Get-Date -Format 'yyyyMMdd_HHmmss')" -Recurse
   ```

2. **Document current function usage**
   - Audit all imports of user data functions
   - Identify all call sites for individual loader functions
   - Document current function signatures and return types

3. **Create test baseline**
   - Run full test suite to establish baseline
   - Document any failing tests before changes

#### Phase 2: Rename Individual Loader Functions (Helper Function Pattern)
1. **Rename load functions in core/user_management.py**:
   ```python
   # OLD -> NEW
   load_user_account_data() -> _get_user_data__load_account()
   load_user_preferences_data() -> _get_user_data__load_preferences()
   load_user_context_data() -> _get_user_data__load_context()
   load_user_schedules_data() -> _get_user_data__load_schedules()
   ```

2. **Rename save functions in core/user_management.py**:
   ```python
   # OLD -> NEW
   save_user_account_data() -> _save_user_data__save_account()
   save_user_preferences_data() -> _save_user_data__save_preferences()
   save_user_context_data() -> _save_user_data__save_context()
   save_user_schedules_data() -> _save_user_data__save_schedules()
   ```

3. **Update function documentation**:
   - Add helper function headers
   - Update docstrings to reflect helper function status
   - Add `# HELPER FUNCTION` comments

#### Phase 3: Update Data Loader Registry
1. **Update USER_DATA_LOADERS registry**:
   ```python
   # Update loader function references
   'account': {'loader': _get_user_data__load_account, ...}
   'preferences': {'loader': _get_user_data__load_preferences, ...}
   'context': {'loader': _get_user_data__load_context, ...}
   'schedules': {'loader': _get_user_data__load_schedules, ...}
   ```

2. **Update register_data_loader calls**:
   ```python
   register_data_loader('account', _get_user_data__load_account, 'account')
   register_data_loader('preferences', _get_user_data__load_preferences, 'preferences')
   register_data_loader('context', _get_user_data__load_context, 'user_context')
   register_data_loader('schedules', _get_user_data__load_schedules, 'schedules')
   ```

#### Phase 4: Update Internal References
1. **Update all internal calls within core/user_management.py**:
   - Find all calls to old function names
   - Replace with new helper function names
   - Update any function references

2. **Update core/user_data_handlers.py**:
   - Update any direct calls to individual loaders
   - Ensure all calls go through the registry system

#### Phase 5: Remove Legacy Wrapper Methods
1. **Remove UserContext wrapper methods**:
   ```python
   # Remove from user/user_context.py:
   def load_user_data(self, user_id)  # REMOVE
   def save_user_data(self, user_id)  # REMOVE
   ```

2. **Update any code that uses these methods**:
   - Find all callers of UserContext.load_user_data()
   - Find all callers of UserContext.save_user_data()
   - Replace with direct calls to get_user_data() and save_user_data()

#### Phase 6: Update External Module Imports
1. **Audit all external imports**:
   ```bash
   # Find all imports of individual loader functions
   grep -r "from.*import.*load_user_" .
   grep -r "from.*import.*save_user_" .
   ```

2. **Update imports to use primary API**:
   ```python
   # OLD
   from core.user_management import load_user_account_data
   
   # NEW
   from core.user_data_handlers import get_user_data
   ```

3. **Update function calls**:
   ```python
   # OLD
   account_data = load_user_account_data(user_id)
   
   # NEW
   account_result = get_user_data(user_id, 'account')
   account_data = account_result.get('account', {})
   ```

#### Phase 7: Update Tests
1. **Update test imports**:
   - Update all test files to import from primary API
   - Remove direct imports of individual loader functions

2. **Update test function calls**:
   - Replace direct calls to individual loaders
   - Use primary API with appropriate data type parameters

3. **Update test utilities**:
   - Update test_utilities.py helper functions
   - Ensure test data creation uses primary API

#### Phase 8: Documentation Updates
1. **Update function documentation**:
   - Update docstrings for renamed functions
   - Add helper function classification headers
   - Update parameter and return type documentation

2. **Update API documentation**:
   - Update AI_FUNCTION_REGISTRY.md
   - Update AI_MODULE_DEPENDENCIES.md
   - Update any other documentation files

#### Phase 9: Validation and Testing
1. **Run comprehensive tests**:
   ```bash
   python run_tests.py
   ```

2. **Test system functionality**:
   ```bash
   python run_mhm.py
   ```

3. **Verify data integrity**:
   - Test user data loading/saving
   - Verify all data types work correctly
   - Check that no data is lost or corrupted

#### Phase 10: Cleanup and Finalization
1. **Remove any remaining legacy comments**:
   - Clean up any temporary comments
   - Remove any debugging code

2. **Update changelog**:
   - Document all changes in CHANGELOG_DETAIL.md
   - Update AI_CHANGELOG.md

3. **Final validation**:
   - Run full test suite one more time
   - Verify system starts and runs correctly
   - Check that all user interactions work

**Success Criteria**:
- ✅ All individual loader functions follow `_main_function__helper_name` pattern
- ✅ All external modules use primary API only
- ✅ Legacy wrapper methods removed
- ✅ All tests pass
- ✅ System functionality preserved
- ✅ Documentation updated
- ✅ No data loss or corruption

**Rollback Plan**:
If issues arise, restore from backup:
```powershell
Copy-Item -Path "../backup_user_data_refactor_YYYYMMDD_HHMMSS/*" -Destination "." -Recurse
```

## 📝 Legacy Code Standards Compliance

### Required for All Legacy Code
1. **Necessary**: Must serve an actual purpose, not just defensive programming
2. **Clearly Marked**: Must have explicit `LEGACY COMPATIBILITY` comments
3. **Usage Logged**: Must log warnings when legacy code paths are accessed
4. **Removal Plan**: Must have documented removal plan with timeline
5. **Monitoring**: Must monitor usage and remove when no longer needed

### Legacy Code Documentation Format
```python
# LEGACY COMPATIBILITY: [Brief description]
# TODO: Remove after [specific condition]
# REMOVAL PLAN:
# 1. [Step 1]
# 2. [Step 2]
# 3. [Step 3]
```

## 🔍 Monitoring and Maintenance

### Usage Tracking
- Monitor for any remaining calls to old function names
- Track usage of legacy wrapper methods
- Log warnings when legacy code paths are accessed

### Regular Review
- Monthly review of legacy code usage
- Quarterly assessment of removal readiness
- Annual cleanup of obsolete legacy code

### Documentation Maintenance
- Keep removal plans updated
- Update timelines based on usage patterns
- Document any new legacy code that emerges

## 📊 Progress Tracking

### Plan 1: User Data Function Cleanup and Standardization

**Status**: ✅ **COMPLETED**

**Phase-by-Phase Progress**:
- ✅ **Phase 1**: Preparation and Backup - COMPLETED
- ✅ **Phase 2**: Function Renaming - COMPLETED
- ✅ **Phase 3**: Registry Updates - COMPLETED
- ✅ **Phase 4**: Internal Call Updates - COMPLETED
- ✅ **Phase 5**: External Call Updates - COMPLETED
- ✅ **Phase 6**: Import Statement Updates - COMPLETED
- ✅ **Phase 7**: Test Updates - COMPLETED
- ✅ **Phase 8**: Documentation Updates - COMPLETED
- ✅ **Phase 9**: System Testing - COMPLETED
- ✅ **Phase 10**: Legacy Function Search and Cleanup - COMPLETED

**Final Status**: All legacy user data functions have been successfully refactored and standardized. The codebase now uses consistent naming conventions with helper functions following the `_main_function__helper_name` pattern and implementation functions using standard `snake_case`. All imports and calls have been updated to use the primary API functions (`get_user_data()` and `save_user_data()`).

**Legacy Function Search Results**:
- ✅ Removed legacy imports from `tests/behavior/test_interaction_handlers_behavior.py`
- ✅ Removed legacy imports from `tests/behavior/test_interaction_handlers_coverage_expansion.py`
- ✅ Removed legacy imports from `tests/behavior/test_discord_bot_behavior.py`
- ✅ Removed legacy import from `tests/integration/test_account_lifecycle.py`
- ✅ Confirmed no remaining direct calls to legacy functions in codebase
- ✅ All remaining references are in documentation files (expected)

**Testing Results**:
- ✅ User management unit tests: 25/25 passed
- ✅ Integration tests: Working correctly
- ✅ System functionality: Confirmed working
- ⚠️ Known unrelated test failures: 2 tests failing due to pre-existing `@handle_errors` decorator issue (not related to refactoring)
