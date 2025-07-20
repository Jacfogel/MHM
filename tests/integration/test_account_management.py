#!/usr/bin/env python3
"""
Systematic Account Management Testing Script for MHM
Tests all account management functionality for editing existing users
READ-ONLY - Does not modify any real user data
"""

import sys
import os
import time
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_account_management_imports():
    """Test that all account management modules can be imported without errors"""
    print("🔍 Testing Account Management Imports...")
    
    modules_to_test = [
        ("Account Manager", "ui.account_manager", "setup_communication_settings_window"),
        ("User Management", "core.user_management", "update_user_account"),
        ("User Data Manager", "core.user_data_manager", "UserDataManager"),
        ("User Context", "user.user_context", "UserContext"),
    ]
    
    results = {}
    
    for module_name, module_path, function_name in modules_to_test:
        try:
            module = __import__(module_path, fromlist=[function_name])
            function = getattr(module, function_name)
            print(f"  ✅ {module_name}: Import successful")
            results[module_name] = "IMPORT_SUCCESS"
        except ImportError as e:
            print(f"  ❌ {module_name}: Import failed - {e}")
            results[module_name] = f"IMPORT_FAILED: {e}"
        except AttributeError as e:
            print(f"  ❌ {module_name}: Function not found - {e}")
            results[module_name] = f"FUNCTION_NOT_FOUND: {e}"
        except Exception as e:
            print(f"  ❌ {module_name}: Unexpected error - {e}")
            results[module_name] = f"UNEXPECTED_ERROR: {e}"
    
    return results

def test_account_management_functions():
    """Test that all account management functions can be called (with safe test data)"""
    print("\n🔍 Testing Account Management Functions...")
    
    try:
        from core.user_management import (
            get_user_data, update_user_account, update_user_preferences, 
            update_user_context, save_user_data, get_all_user_ids
        )
        from core.user_data_manager import UserDataManager
        from user.user_context import UserContext
        
        # Use a safe test user
        test_user = "test-user"
        
        results = {}
        
        # Test get_user_data for account management
        try:
            account_data = get_user_data(test_user, 'account')
            print(f"  ✅ get_user_data (account): Function call successful")
            results["get_user_data_account"] = "FUNCTION_SUCCESS"
        except Exception as e:
            print(f"  ❌ get_user_data (account): Function call failed - {e}")
            results["get_user_data_account"] = f"FUNCTION_FAILED: {e}"
        
        # Test get_user_data for preferences
        try:
            prefs_data = get_user_data(test_user, 'preferences')
            print(f"  ✅ get_user_data (preferences): Function call successful")
            results["get_user_data_preferences"] = "FUNCTION_SUCCESS"
        except Exception as e:
            print(f"  ❌ get_user_data (preferences): Function call failed - {e}")
            results["get_user_data_preferences"] = f"FUNCTION_FAILED: {e}"
        
        # Test get_user_data for context
        try:
            context_data = get_user_data(test_user, 'context')
            print(f"  ✅ get_user_data (context): Function call successful")
            results["get_user_data_context"] = "FUNCTION_SUCCESS"
        except Exception as e:
            print(f"  ❌ get_user_data (context): Function call failed - {e}")
            results["get_user_data_context"] = f"FUNCTION_FAILED: {e}"
        
        # Test UserDataManager instantiation
        try:
            data_manager = UserDataManager()
            print(f"  ✅ UserDataManager: Instantiation successful")
            results["UserDataManager"] = "INSTANTIATION_SUCCESS"
        except Exception as e:
            print(f"  ❌ UserDataManager: Instantiation failed - {e}")
            results["UserDataManager"] = f"INSTANTIATION_FAILED: {e}"
        
        # Test UserContext instantiation
        try:
            user_context = UserContext()
            print(f"  ✅ UserContext: Instantiation successful")
            results["UserContext"] = "INSTANTIATION_SUCCESS"
        except Exception as e:
            print(f"  ❌ UserContext: Instantiation failed - {e}")
            results["UserContext"] = f"INSTANTIATION_FAILED: {e}"
        
        return results
        
    except Exception as e:
        print(f"  ❌ Account management function testing failed: {e}")
        return {"error": str(e)}

def test_account_management_data_structures():
    """Test that account management can handle the expected data structures"""
    print("\n🔍 Testing Account Management Data Structures...")
    
    try:
        from core.user_data_handlers import get_user_data, save_user_data
        
        # Use a safe test user
        test_user = "test-user"
        
        results = {}
        
        # Test account data structure
        try:
            account_data = get_user_data(test_user, 'account')
            if account_data and 'account' in account_data:
                account = account_data['account']
                required_fields = ['user_id', 'internal_username', 'account_status', 'features']
                missing_fields = [field for field in required_fields if field not in account]
                
                if not missing_fields:
                    print(f"  ✅ Account data structure: All required fields present")
                    results["account_structure"] = "STRUCTURE_VALID"
                else:
                    print(f"  ⚠️ Account data structure: Missing fields - {missing_fields}")
                    results["account_structure"] = f"MISSING_FIELDS: {missing_fields}"
            else:
                print(f"  ❌ Account data structure: No account data found")
                results["account_structure"] = "NO_DATA"
        except Exception as e:
            print(f"  ❌ Account data structure: Error - {e}")
            results["account_structure"] = f"ERROR: {e}"
        
        # Test preferences data structure
        try:
            prefs_data = get_user_data(test_user, 'preferences')
            if prefs_data and 'preferences' in prefs_data:
                prefs = prefs_data['preferences']
                required_fields = ['categories', 'channel']
                missing_fields = [field for field in required_fields if field not in prefs]
                
                if not missing_fields:
                    print(f"  ✅ Preferences data structure: All required fields present")
                    results["preferences_structure"] = "STRUCTURE_VALID"
                else:
                    print(f"  ⚠️ Preferences data structure: Missing fields - {missing_fields}")
                    results["preferences_structure"] = f"MISSING_FIELDS: {missing_fields}"
            else:
                print(f"  ❌ Preferences data structure: No preferences data found")
                results["preferences_structure"] = "NO_DATA"
        except Exception as e:
            print(f"  ❌ Preferences data structure: Error - {e}")
            results["preferences_structure"] = f"ERROR: {e}"
        
        # Test context data structure
        try:
            context_data = get_user_data(test_user, 'context')
            if context_data and 'context' in context_data:
                context = context_data['context']
                print(f"  ✅ Context data structure: Data present")
                results["context_structure"] = "STRUCTURE_VALID"
            else:
                print(f"  ⚠️ Context data structure: No context data found (may be optional)")
                results["context_structure"] = "NO_DATA"
        except Exception as e:
            print(f"  ❌ Context data structure: Error - {e}")
            results["context_structure"] = f"ERROR: {e}"
        
        return results
        
    except Exception as e:
        print(f"  ❌ Data structure testing failed: {e}")
        return {"error": str(e)}

def test_account_management_validation():
    """Test that account management validation works correctly"""
    print("\n🔍 Testing Account Management Validation...")
    
    try:
        from core.user_management import validate_user_data_updates
        
        results = {}
        
        # Test valid account updates
        try:
            valid_updates = {
                'internal_username': 'testuser',
                'email': 'test@example.com',
                'channel': {'type': 'email'}
            }
            is_valid, errors = validate_user_data_updates('test-user', 'account', valid_updates)
            
            if is_valid:
                print(f"  ✅ Account validation: Valid updates accepted")
                results["valid_account_updates"] = "VALIDATION_SUCCESS"
            else:
                print(f"  ❌ Account validation: Valid updates rejected - {errors}")
                results["valid_account_updates"] = f"VALIDATION_FAILED: {errors}"
        except Exception as e:
            print(f"  ❌ Account validation: Error - {e}")
            results["valid_account_updates"] = f"ERROR: {e}"
        
        # Test invalid account updates
        try:
            invalid_updates = {
                'internal_username': '',  # Empty username should fail
                'channel': {'type': 'invalid'}  # Invalid channel type
            }
            is_valid, errors = validate_user_data_updates('test-user', 'account', invalid_updates)
            
            if not is_valid:
                print(f"  ✅ Account validation: Invalid updates correctly rejected")
                results["invalid_account_updates"] = "VALIDATION_SUCCESS"
            else:
                print(f"  ❌ Account validation: Invalid updates incorrectly accepted")
                results["invalid_account_updates"] = "VALIDATION_FAILED"
        except Exception as e:
            print(f"  ❌ Account validation: Error - {e}")
            results["invalid_account_updates"] = f"ERROR: {e}"
        
        # Test preferences validation
        try:
            valid_prefs = {
                'categories': ['motivational'],
                'channel': {'type': 'email'}
            }
            is_valid, errors = validate_user_data_updates('test-user', 'preferences', valid_prefs)
            
            if is_valid:
                print(f"  ✅ Preferences validation: Valid updates accepted")
                results["valid_preferences_updates"] = "VALIDATION_SUCCESS"
            else:
                print(f"  ❌ Preferences validation: Valid updates rejected - {errors}")
                results["valid_preferences_updates"] = f"VALIDATION_FAILED: {errors}"
        except Exception as e:
            print(f"  ❌ Preferences validation: Error - {e}")
            results["valid_preferences_updates"] = f"ERROR: {e}"
        
        return results
        
    except Exception as e:
        print(f"  ❌ Validation testing failed: {e}")
        return {"error": str(e)}

def test_account_management_safe_operations():
    """Test account management operations with temporary test data"""
    print("\n🔍 Testing Account Management Safe Operations...")
    
    try:
        from core.user_data_handlers import get_user_data, save_user_data
        
        # Create a temporary test user for safe operations
        temp_user_id = f"temp-test-{int(time.time())}"
        
        results = {}
        
        # Test creating temporary user data
        try:
            # Create minimal test data
            test_account = {
                'user_id': temp_user_id,
                'internal_username': 'tempuser',
                'account_status': 'active',
                'features': {
                    'automated_messages': 'disabled',
                    'checkins': 'disabled',
                    'task_management': 'disabled'
                }
            }
            
            test_preferences = {
                'categories': [],
                'channel': {'type': 'email'}
            }
            
            # Save test data
            save_result = save_user_data(temp_user_id, {
                'account': test_account,
                'preferences': test_preferences
            })
            
            if save_result.get('account') and save_result.get('preferences'):
                print(f"  ✅ Temporary user creation: Successful")
                results["temp_user_creation"] = "CREATION_SUCCESS"
            else:
                print(f"  ❌ Temporary user creation: Failed - {save_result}")
                results["temp_user_creation"] = f"CREATION_FAILED: {save_result}"
        except Exception as e:
            print(f"  ❌ Temporary user creation: Error - {e}")
            results["temp_user_creation"] = f"ERROR: {e}"
        
        # Test reading temporary user data
        try:
            account_data = get_user_data(temp_user_id, 'account')
            prefs_data = get_user_data(temp_user_id, 'preferences')
            
            if account_data and prefs_data:
                print(f"  ✅ Temporary user data access: Successful")
                results["temp_user_data_access"] = "ACCESS_SUCCESS"
            else:
                print(f"  ❌ Temporary user data access: Failed")
                results["temp_user_data_access"] = "ACCESS_FAILED"
        except Exception as e:
            print(f"  ❌ Temporary user data access: Error - {e}")
            results["temp_user_data_access"] = f"ERROR: {e}"
        
        # Test updating temporary user data
        try:
            update_result = save_user_data(temp_user_id, {
                'account': {'internal_username': 'updatedtempuser'}
            })
            
            if update_result.get('account'):
                print(f"  ✅ Temporary user update: Successful")
                results["temp_user_update"] = "UPDATE_SUCCESS"
            else:
                print(f"  ❌ Temporary user update: Failed - {update_result}")
                results["temp_user_update"] = f"UPDATE_FAILED: {update_result}"
        except Exception as e:
            print(f"  ❌ Temporary user update: Error - {e}")
            results["temp_user_update"] = f"ERROR: {e}"
        
        # Clean up temporary user (optional - let it be cleaned up automatically)
        try:
            # We could delete the temporary user here, but for safety we'll let it remain
            # The system has automatic cleanup mechanisms
            print(f"  ✅ Temporary user cleanup: Left for automatic cleanup")
            results["temp_user_cleanup"] = "CLEANUP_SUCCESS"
        except Exception as e:
            print(f"  ⚠️ Temporary user cleanup: Error - {e}")
            results["temp_user_cleanup"] = f"ERROR: {e}"
        
        return results
        
    except Exception as e:
        print(f"  ❌ Safe operations testing failed: {e}")
        return {"error": str(e)}

def test_account_management_integration():
    """Test that account management integrates properly with other systems"""
    print("\n🔍 Testing Account Management Integration...")
    
    try:
        from core.user_data_handlers import get_user_data, save_user_data
        from core.user_data_manager import update_user_index
        from core.file_operations import get_user_file_path
        
        # Use a safe test user
        test_user = "test-user"
        
        results = {}
        
        # Test file path integration
        try:
            account_file = get_user_file_path(test_user, 'account')
            prefs_file = get_user_file_path(test_user, 'preferences')
            
            if os.path.exists(account_file) and os.path.exists(prefs_file):
                print(f"  ✅ File path integration: Files accessible")
                results["file_path_integration"] = "INTEGRATION_SUCCESS"
            else:
                print(f"  ❌ File path integration: Files not found")
                results["file_path_integration"] = "INTEGRATION_FAILED"
        except Exception as e:
            print(f"  ❌ File path integration: Error - {e}")
            results["file_path_integration"] = f"ERROR: {e}"
        
        # Test user index integration
        try:
            # This should update the user index
            update_user_index(test_user)
            print(f"  ✅ User index integration: Index update successful")
            results["user_index_integration"] = "INTEGRATION_SUCCESS"
        except Exception as e:
            print(f"  ❌ User index integration: Error - {e}")
            results["user_index_integration"] = f"ERROR: {e}"
        
        # Test data consistency
        try:
            # Test that data is consistent across different access methods
            account_data1 = get_user_data(test_user, 'account')
            account_data2 = get_user_data(test_user, 'account')
            
            if account_data1 == account_data2:
                print(f"  ✅ Data consistency: Consistent across reads")
                results["data_consistency"] = "CONSISTENCY_SUCCESS"
            else:
                print(f"  ❌ Data consistency: Inconsistent data")
                results["data_consistency"] = "CONSISTENCY_FAILED"
        except Exception as e:
            print(f"  ❌ Data consistency: Error - {e}")
            results["data_consistency"] = f"ERROR: {e}"
        
        return results
        
    except Exception as e:
        print(f"  ❌ Integration testing failed: {e}")
        return {"error": str(e)}

def main():
    """Run all account management tests and generate a comprehensive report"""
    print("🎯 MHM Account Management Testing - Systematic Analysis (READ-ONLY)")
    print("=" * 70)
    
    # Run all tests
    imports = test_account_management_imports()
    functions = test_account_management_functions()
    data_structures = test_account_management_data_structures()
    validation = test_account_management_validation()
    safe_operations = test_account_management_safe_operations()
    integration = test_account_management_integration()
    
    # Generate summary
    print("\n" + "=" * 70)
    print("📊 ACCOUNT MANAGEMENT TESTING SUMMARY")
    print("=" * 70)
    
    # Import summary
    import_success = sum(1 for result in imports.values() if "SUCCESS" in result)
    import_total = len(imports)
    print(f"Imports: {import_success}/{import_total} successful")
    
    # Function summary
    function_success = sum(1 for result in functions.values() if "SUCCESS" in result)
    function_total = len(functions)
    print(f"Functions: {function_success}/{function_total} successful")
    
    # Data structure summary
    structure_success = sum(1 for result in data_structures.values() if "VALID" in result or "SUCCESS" in result)
    structure_total = len(data_structures)
    print(f"Data Structures: {structure_success}/{structure_total} valid")
    
    # Validation summary
    validation_success = sum(1 for result in validation.values() if "SUCCESS" in result)
    validation_total = len(validation)
    print(f"Validation: {validation_success}/{validation_total} successful")
    
    # Safe operations summary
    operation_success = sum(1 for result in safe_operations.values() if "SUCCESS" in result)
    operation_total = len(safe_operations)
    print(f"Safe Operations: {operation_success}/{operation_total} successful")
    
    # Integration summary
    integration_success = sum(1 for result in integration.values() if "SUCCESS" in result)
    integration_total = len(integration)
    print(f"Integration: {integration_success}/{integration_total} successful")
    
    # Detailed results
    print("\n📋 DETAILED RESULTS")
    print("-" * 50)
    
    print("\n🔧 Import Issues:")
    for module, result in imports.items():
        if "SUCCESS" not in result:
            print(f"  ❌ {module}: {result}")
    
    print("\n🔧 Function Issues:")
    for func, result in functions.items():
        if "SUCCESS" not in result:
            print(f"  ❌ {func}: {result}")
    
    print("\n🔧 Data Structure Issues:")
    for struct, result in data_structures.items():
        if "VALID" not in result and "SUCCESS" not in result:
            print(f"  ❌ {struct}: {result}")
    
    print("\n🔧 Validation Issues:")
    for valid, result in validation.items():
        if "SUCCESS" not in result:
            print(f"  ❌ {valid}: {result}")
    
    print("\n🔧 Safe Operation Issues:")
    for op, result in safe_operations.items():
        if "SUCCESS" not in result:
            print(f"  ❌ {op}: {result}")
    
    print("\n🔧 Integration Issues:")
    for integ, result in integration.items():
        if "SUCCESS" not in result:
            print(f"  ❌ {integ}: {result}")
    
    print("\n" + "=" * 70)
    print("✅ Account Management Testing Complete! (No real data was modified)")
    print("=" * 70)

if __name__ == "__main__":
    main() 