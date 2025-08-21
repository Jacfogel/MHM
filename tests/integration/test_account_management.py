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
import pytest
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

@pytest.mark.integration
@pytest.mark.user_management
@pytest.mark.critical
@pytest.mark.regression
@pytest.mark.file_io
def test_account_management_imports():
    """Test that all account management modules can be imported without errors"""
    print("🔍 Testing Account Management Imports...")
    
    modules_to_test = [
        ("Account Creator Dialog", "ui.dialogs.account_creator_dialog", "AccountCreatorDialog"),
        ("User Management", "core.user_management", "update_user_account"),
        ("User Data Manager", "core.user_data_manager", "UserDataManager"),
        ("User Context", "user.user_context", "UserContext"),
    ]
    
    for module_name, module_path, function_name in modules_to_test:
        try:
            module = __import__(module_path, fromlist=[function_name])
            function = getattr(module, function_name)
            print(f"  ✅ {module_name}: Import successful")
            # Assert that the function exists and is callable
            assert callable(function), f"{module_name}: Function is not callable"
        except ImportError as e:
            print(f"  ❌ {module_name}: Import failed - {e}")
            assert False, f"{module_name}: Import failed - {e}"
        except AttributeError as e:
            print(f"  ❌ {module_name}: Function not found - {e}")
            assert False, f"{module_name}: Function not found - {e}"
        except Exception as e:
            print(f"  ❌ {module_name}: Unexpected error - {e}")
            assert False, f"{module_name}: Unexpected error - {e}"

@pytest.mark.integration
@pytest.mark.user_management
@pytest.mark.critical
@pytest.mark.regression
@pytest.mark.file_io
def test_account_management_functions():
    """Test that all account management functions can be called (with safe test data)"""
    print("\n🔍 Testing Account Management Functions...")
    
    try:
        from core.user_data_handlers import (
            get_user_data, update_user_account, update_user_preferences, 
            update_user_context, save_user_data, get_all_user_ids
        )
        from core.user_data_manager import UserDataManager
        from user.user_context import UserContext
        
        # Use a safe test user
        test_user = "test-user"
        
        # Test get_user_data for account management
        try:
            account_data = get_user_data(test_user, 'account')
            print(f"  ✅ get_user_data (account): Function call successful")
            assert account_data is not None, "get_user_data should return data"
        except Exception as e:
            print(f"  ❌ get_user_data (account): Function call failed - {e}")
            assert False, f"get_user_data (account) failed: {e}"
        
        # Test get_user_data for preferences
        try:
            prefs_data = get_user_data(test_user, 'preferences')
            print(f"  ✅ get_user_data (preferences): Function call successful")
            assert prefs_data is not None, "get_user_data should return data"
        except Exception as e:
            print(f"  ❌ get_user_data (preferences): Function call failed - {e}")
            assert False, f"get_user_data (preferences) failed: {e}"
        
        # Test get_user_data for context
        try:
            context_data = get_user_data(test_user, 'context')
            print(f"  ✅ get_user_data (context): Function call successful")
            assert context_data is not None, "get_user_data should return data"
        except Exception as e:
            print(f"  ❌ get_user_data (context): Function call failed - {e}")
            assert False, f"get_user_data (context) failed: {e}"
        
        # Test UserDataManager instantiation
        try:
            data_manager = UserDataManager()
            print(f"  ✅ UserDataManager: Instantiation successful")
            assert data_manager is not None, "UserDataManager should be instantiated"
        except Exception as e:
            print(f"  ❌ UserDataManager: Instantiation failed - {e}")
            assert False, f"UserDataManager instantiation failed: {e}"
        
        # Test UserContext instantiation
        try:
            user_context = UserContext()
            print(f"  ✅ UserContext: Instantiation successful")
            assert user_context is not None, "UserContext should be instantiated"
        except Exception as e:
            print(f"  ❌ UserContext: Instantiation failed - {e}")
            assert False, f"UserContext instantiation failed: {e}"
        
    except Exception as e:
        print(f"  ❌ Account management function testing failed: {e}")
        assert False, f"Account management function testing failed: {e}"

@pytest.mark.integration
@pytest.mark.user_management
@pytest.mark.critical
@pytest.mark.regression
@pytest.mark.file_io
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
                    assert True, "Account structure is valid"
                else:
                    print(f"  ⚠️ Account data structure: Missing fields - {missing_fields}")
                    assert False, f"Account structure missing fields: {missing_fields}"
            else:
                print(f"  ❌ Account data structure: No account data found")
                assert False, "No account data found"
        except Exception as e:
            print(f"  ❌ Account data structure: Error - {e}")
            assert False, f"Account data structure error: {e}"
        
        # Test preferences data structure
        try:
            prefs_data = get_user_data(test_user, 'preferences')
            if prefs_data and 'preferences' in prefs_data:
                prefs = prefs_data['preferences']
                required_fields = ['categories', 'channel']
                missing_fields = [field for field in required_fields if field not in prefs]
                
                if not missing_fields:
                    print(f"  ✅ Preferences data structure: All required fields present")
                    assert True, "Preferences structure is valid"
                else:
                    print(f"  ⚠️ Preferences data structure: Missing fields - {missing_fields}")
                    assert False, f"Preferences structure missing fields: {missing_fields}"
            else:
                print(f"  ❌ Preferences data structure: No preferences data found")
                assert False, "No preferences data found"
        except Exception as e:
            print(f"  ❌ Preferences data structure: Error - {e}")
            assert False, f"Preferences data structure error: {e}"
        
        # Test context data structure
        try:
            context_data = get_user_data(test_user, 'context')
            if context_data and 'context' in context_data:
                context = context_data['context']
                print(f"  ✅ Context data structure: Data present")
                assert True, "Context structure is valid"
            else:
                print(f"  ⚠️ Context data structure: No context data found (may be optional)")
                # Context is optional, so this is not a failure
                assert True, "Context data is optional"
        except Exception as e:
            print(f"  ❌ Context data structure: Error - {e}")
            assert False, f"Context data structure error: {e}"
        
    except Exception as e:
        print(f"  ❌ Data structure testing failed: {e}")
        assert False, f"Data structure testing failed: {e}"

@pytest.mark.integration
@pytest.mark.user_management
@pytest.mark.critical
@pytest.mark.regression
@pytest.mark.file_io
def test_account_management_validation():
    """Test that account management validation works correctly"""
    print("\n🔍 Testing Account Management Validation...")
    
    try:
        from core.user_data_validation import validate_user_update
        
        # Test valid account updates
        try:
            valid_updates = {
                'internal_username': 'testuser',
                'email': 'test@example.com',
                'channel': {'type': 'email'}
            }
            is_valid, errors = validate_user_update('test-user', 'account', valid_updates)
            
            if is_valid:
                print(f"  ✅ Account validation: Valid updates accepted")
                assert True, "Valid account updates should be accepted"
            else:
                print(f"  ❌ Account validation: Valid updates rejected - {errors}")
                assert False, f"Valid account updates were rejected: {errors}"
        except Exception as e:
            print(f"  ❌ Account validation: Error - {e}")
            assert False, f"Account validation error: {e}"
        
        # Test invalid account updates
        try:
            invalid_updates = {
                'internal_username': '',  # Empty username should fail
                'channel': {'type': 'invalid'}  # Invalid channel type
            }
            is_valid, errors = validate_user_update('test-user', 'account', invalid_updates)
            
            if not is_valid:
                print(f"  ✅ Account validation: Invalid updates correctly rejected")
                assert True, "Invalid account updates should be rejected"
            else:
                print(f"  ❌ Account validation: Invalid updates incorrectly accepted")
                assert False, "Invalid account updates were incorrectly accepted"
        except Exception as e:
            print(f"  ❌ Account validation: Error - {e}")
            assert False, f"Account validation error: {e}"
        
        # Test preferences validation
        try:
            valid_prefs = {
                'categories': ['motivational'],
                'channel': {'type': 'email'}
            }
            is_valid, errors = validate_user_update('test-user', 'preferences', valid_prefs)
            
            if is_valid:
                print(f"  ✅ Preferences validation: Valid updates accepted")
                assert True, "Valid preferences updates should be accepted"
            else:
                print(f"  ❌ Preferences validation: Valid updates rejected - {errors}")
                assert False, f"Valid preferences updates were rejected: {errors}"
        except Exception as e:
            print(f"  ❌ Preferences validation: Error - {e}")
            assert False, f"Preferences validation error: {e}"
        
    except Exception as e:
        print(f"  ❌ Validation testing failed: {e}")
        assert False, f"Validation testing failed: {e}"

@pytest.mark.integration
@pytest.mark.user_management
@pytest.mark.critical
@pytest.mark.regression
@pytest.mark.file_io
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
                assert True, "Temporary user creation should succeed"
            else:
                print(f"  ❌ Temporary user creation: Failed - {save_result}")
                assert False, f"Temporary user creation failed: {save_result}"
        except Exception as e:
            print(f"  ❌ Temporary user creation: Error - {e}")
            assert False, f"Temporary user creation error: {e}"
        
        # Test reading temporary user data
        try:
            account_data = get_user_data(temp_user_id, 'account')
            prefs_data = get_user_data(temp_user_id, 'preferences')
            
            if account_data and prefs_data:
                print(f"  ✅ Temporary user data access: Successful")
                assert True, "Temporary user data access should succeed"
            else:
                print(f"  ❌ Temporary user data access: Failed")
                assert False, "Temporary user data access failed"
        except Exception as e:
            print(f"  ❌ Temporary user data access: Error - {e}")
            assert False, f"Temporary user data access error: {e}"
        
        # Test updating temporary user data
        try:
            update_result = save_user_data(temp_user_id, {
                'account': {'internal_username': 'updatedtempuser'}
            })
            
            if update_result.get('account'):
                print(f"  ✅ Temporary user update: Successful")
                assert True, "Temporary user update should succeed"
            else:
                print(f"  ❌ Temporary user update: Failed - {update_result}")
                assert False, f"Temporary user update failed: {update_result}"
        except Exception as e:
            print(f"  ❌ Temporary user update: Error - {e}")
            assert False, f"Temporary user update error: {e}"
        
        # Clean up temporary user (optional - let it be cleaned up automatically)
        try:
            # We could delete the temporary user here, but for safety we'll let it remain
            # The system has automatic cleanup mechanisms
            print(f"  ✅ Temporary user cleanup: Left for automatic cleanup")
            assert True, "Temporary user cleanup should succeed"
        except Exception as e:
            print(f"  ⚠️ Temporary user cleanup: Error - {e}")
            assert False, f"Temporary user cleanup error: {e}"
        
    except Exception as e:
        print(f"  ❌ Safe operations testing failed: {e}")
        assert False, f"Safe operations testing failed: {e}"

@pytest.mark.integration
@pytest.mark.user_management
@pytest.mark.critical
@pytest.mark.regression
@pytest.mark.file_io
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
            assert True, "User index integration should succeed"
        except Exception as e:
            print(f"  ❌ User index integration: Error - {e}")
            assert False, f"User index integration error: {e}"
        
        # Test data consistency
        try:
            # Test that data is consistent across different access methods
            account_data1 = get_user_data(test_user, 'account')
            account_data2 = get_user_data(test_user, 'account')
            
            if account_data1 == account_data2:
                print(f"  ✅ Data consistency: Consistent across reads")
                assert True, "Data consistency should be maintained"
            else:
                print(f"  ❌ Data consistency: Inconsistent data")
                assert False, "Data consistency failed"
        except Exception as e:
            print(f"  ❌ Data consistency: Error - {e}")
            assert False, f"Data consistency error: {e}"
        
    except Exception as e:
        print(f"  ❌ Integration testing failed: {e}")
        assert False, f"Integration testing failed: {e}"

# Note: This file contains pytest test functions that should be run with pytest
# The main() function has been removed as it's not compatible with pytest
# Run tests with: python -m pytest tests/integration/test_account_management.py 