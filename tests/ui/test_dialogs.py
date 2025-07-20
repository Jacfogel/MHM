#!/usr/bin/env python3
"""
Systematic Dialog Testing Script for MHM
Tests all dialogs to see what works and what's broken
READ-ONLY - Does not modify any user data
"""

import sys
import os
import time
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_dialog_imports():
    """Test that all dialog modules can be imported without errors"""
    print("🔍 Testing Dialog Imports...")
    
    dialogs_to_test = [
        ("Account Creator", "ui.dialogs.account_creator_dialog", "AccountCreatorDialog"),
        ("Channel Management", "ui.dialogs.channel_management_dialog", "ChannelManagementDialog"),
        ("Category Management", "ui.dialogs.category_management_dialog", "CategoryManagementDialog"),
        ("Check-in Management", "ui.dialogs.checkin_management_dialog", "CheckinManagementDialog"),
        ("Task Management", "ui.dialogs.task_management_dialog", "TaskManagementDialog"),
        ("User Profile", "ui.dialogs.user_profile_dialog", "UserProfileDialog"),
        ("Schedule Editor", "ui.dialogs.schedule_editor_dialog", "open_schedule_editor"),
        ("Admin Panel", "ui.dialogs.admin_panel", "AdminPanel"),
    ]
    
    results = {}
    
    for dialog_name, module_path, class_name in dialogs_to_test:
        try:
            module = __import__(module_path, fromlist=[class_name])
            dialog_class = getattr(module, class_name)
            print(f"  ✅ {dialog_name}: Import successful")
            results[dialog_name] = "IMPORT_SUCCESS"
        except ImportError as e:
            print(f"  ❌ {dialog_name}: Import failed - {e}")
            results[dialog_name] = f"IMPORT_FAILED: {e}"
        except AttributeError as e:
            print(f"  ❌ {dialog_name}: Class not found - {e}")
            results[dialog_name] = f"CLASS_NOT_FOUND: {e}"
        except Exception as e:
            print(f"  ❌ {dialog_name}: Unexpected error - {e}")
            results[dialog_name] = f"UNEXPECTED_ERROR: {e}"
    
    return results

def test_widget_imports():
    """Test that all widget modules can be imported without errors"""
    print("\n🔍 Testing Widget Imports...")
    
    widgets_to_test = [
        ("Category Selection", "ui.widgets.category_selection_widget", "CategorySelectionWidget"),
        ("Channel Selection", "ui.widgets.channel_selection_widget", "ChannelSelectionWidget"),
        ("Check-in Settings", "ui.widgets.checkin_settings_widget", "CheckinSettingsWidget"),
        ("Task Settings", "ui.widgets.task_settings_widget", "TaskSettingsWidget"),
        ("User Profile Settings", "ui.widgets.user_profile_settings_widget", "UserProfileSettingsWidget"),
        ("Period Row", "ui.widgets.period_row_widget", "PeriodRowWidget"),
    ]
    
    results = {}
    
    for widget_name, module_path, class_name in widgets_to_test:
        try:
            module = __import__(module_path, fromlist=[class_name])
            widget_class = getattr(module, class_name)
            print(f"  ✅ {widget_name}: Import successful")
            results[widget_name] = "IMPORT_SUCCESS"
        except ImportError as e:
            print(f"  ❌ {widget_name}: Import failed - {e}")
            results[widget_name] = f"IMPORT_FAILED: {e}"
        except AttributeError as e:
            print(f"  ❌ {widget_name}: Class not found - {e}")
            results[widget_name] = f"CLASS_NOT_FOUND: {e}"
        except Exception as e:
            print(f"  ❌ {widget_name}: Unexpected error - {e}")
            results[widget_name] = f"UNEXPECTED_ERROR: {e}"
    
    return results

def test_ui_files_exist():
    """Test that all required UI files exist"""
    print("\n🔍 Testing UI Files...")
    
    ui_files_to_test = [
        ("Admin Panel", "ui/designs/admin_panel.ui"),
        ("Account Creator", "ui/designs/account_creator_dialog.ui"),
        ("Channel Management", "ui/designs/channel_management_dialog.ui"),
        ("Category Management", "ui/designs/category_management_dialog.ui"),
        ("Check-in Management", "ui/designs/checkin_management_dialog.ui"),
        ("Task Management", "ui/designs/task_management_dialog.ui"),
        ("User Profile", "ui/designs/user_profile_management_dialog.ui"),
        ("Schedule Editor", "ui/designs/schedule_editor_dialog.ui"),
    ]
    
    results = {}
    
    for ui_name, file_path in ui_files_to_test:
        if os.path.exists(file_path):
            print(f"  ✅ {ui_name}: UI file exists")
            results[ui_name] = "FILE_EXISTS"
        else:
            print(f"  ❌ {ui_name}: UI file missing - {file_path}")
            results[ui_name] = "FILE_MISSING"
    
    return results

def test_generated_files_exist():
    """Test that all generated Python UI files exist"""
    print("\n🔍 Testing Generated UI Files...")
    
    generated_files_to_test = [
        ("Admin Panel", "ui/generated/admin_panel_pyqt.py"),
        ("Account Creator", "ui/generated/account_creator_dialog_pyqt.py"),
        ("Channel Management", "ui/generated/channel_management_dialog_pyqt.py"),
        ("Category Management", "ui/generated/category_management_dialog_pyqt.py"),
        ("Check-in Management", "ui/generated/checkin_management_dialog_pyqt.py"),
        ("Task Management", "ui/generated/task_management_dialog_pyqt.py"),
        ("User Profile", "ui/generated/user_profile_management_dialog_pyqt.py"),
        ("Schedule Editor", "ui/generated/schedule_editor_dialog_pyqt.py"),
    ]
    
    results = {}
    
    for file_name, file_path in generated_files_to_test:
        if os.path.exists(file_path):
            print(f"  ✅ {file_name}: Generated file exists")
            results[file_name] = "FILE_EXISTS"
        else:
            print(f"  ❌ {file_name}: Generated file missing - {file_path}")
            results[file_name] = "FILE_MISSING"
    
    return results

def test_user_data_access():
    """Test that we can access user data for testing - READ ONLY"""
    print("\n🔍 Testing User Data Access (Read-Only)...")
    
    try:
        from core.user_data_handlers import get_user_data
        from core.user_management import get_all_user_ids
        
        # Get all user IDs
        user_ids = get_all_user_ids()
        print(f"  ✅ Found {len(user_ids)} users total")
        
        # Only test with custom_data users (test users)
        test_users = []
        custom_data_users = []
        
        for user_id in user_ids:
            if user_id.startswith('test-'):
                test_users.append(user_id)
            elif os.path.exists(f"custom_data/users/{user_id}"):
                custom_data_users.append(user_id)
        
        print(f"  ✅ Found {len(test_users)} test users: {test_users}")
        print(f"  ✅ Found {len(custom_data_users)} custom data users: {custom_data_users}")
        
        # Test with a safe test user
        if test_users:
            test_user = test_users[0]  # Use first test user
        elif custom_data_users:
            test_user = custom_data_users[0]  # Use first custom data user
        else:
            print("  ⚠️ No safe test users found")
            return {"error": "No safe test users available"}
        
        print(f"  🔍 Testing with user: {test_user}")
        
        # Test account data (read-only)
        try:
            account_data = get_user_data(test_user, 'account')
            print(f"  ✅ Account data accessible for {test_user}")
            account_accessible = True
        except Exception as e:
            print(f"  ❌ Account data failed for {test_user}: {e}")
            account_accessible = False
        
        # Test preferences data (read-only)
        try:
            prefs_data = get_user_data(test_user, 'preferences')
            print(f"  ✅ Preferences data accessible for {test_user}")
            preferences_accessible = True
        except Exception as e:
            print(f"  ❌ Preferences data failed for {test_user}: {e}")
            preferences_accessible = False
        
        # Test context data (read-only)
        try:
            context_data = get_user_data(test_user, 'context')
            print(f"  ✅ Context data accessible for {test_user}")
            context_accessible = True
        except Exception as e:
            print(f"  ❌ Context data failed for {test_user}: {e}")
            context_accessible = False
        
        return {
            "total_users": len(user_ids),
            "test_users": len(test_users),
            "custom_data_users": len(custom_data_users),
            "test_user": test_user,
            "account_accessible": account_accessible,
            "preferences_accessible": preferences_accessible,
            "context_accessible": context_accessible
        }
        
    except Exception as e:
        print(f"  ❌ User data access failed: {e}")
        return {"error": str(e)}

def test_dialog_instantiation():
    """Test that dialogs can be instantiated (without showing them)"""
    print("\n🔍 Testing Dialog Instantiation...")
    
    # We'll test this with a mock parent and test user
    try:
        from PySide6.QtWidgets import QApplication
        import sys
        
        # Create a minimal QApplication if one doesn't exist
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Test with a safe test user
        test_user = "test-user"  # Use the basic test user
        
        results = {}
        
        # Test Account Creator Dialog
        try:
            from ui.dialogs.account_creator_dialog import AccountCreatorDialog
            from bot.communication_manager import CommunicationManager
            from bot.channel_registry import register_all_channels
            
            register_all_channels()
            comm_manager = CommunicationManager()
            dialog = AccountCreatorDialog(None, comm_manager)
            print(f"  ✅ Account Creator: Instantiation successful")
            results["Account Creator"] = "INSTANTIATION_SUCCESS"
            dialog.close()
            comm_manager.stop_all()
        except Exception as e:
            print(f"  ❌ Account Creator: Instantiation failed - {e}")
            results["Account Creator"] = f"INSTANTIATION_FAILED: {e}"
        
        # Test User Profile Dialog
        try:
            from ui.dialogs.user_profile_dialog import UserProfileDialog
            
            def mock_save(data):
                pass  # Do nothing
            
            dialog = UserProfileDialog(None, test_user, mock_save)
            print(f"  ✅ User Profile: Instantiation successful")
            results["User Profile"] = "INSTANTIATION_SUCCESS"
            dialog.close()
        except Exception as e:
            print(f"  ❌ User Profile: Instantiation failed - {e}")
            results["User Profile"] = f"INSTANTIATION_FAILED: {e}"
        
        # Test other dialogs that don't require complex setup
        simple_dialogs = [
            ("Channel Management", "ui.dialogs.channel_management_dialog", "ChannelManagementDialog"),
            ("Category Management", "ui.dialogs.category_management_dialog", "CategoryManagementDialog"),
            ("Check-in Management", "ui.dialogs.checkin_management_dialog", "CheckinManagementDialog"),
            ("Task Management", "ui.dialogs.task_management_dialog", "TaskManagementDialog"),
        ]
        
        for dialog_name, module_path, class_name in simple_dialogs:
            try:
                module = __import__(module_path, fromlist=[class_name])
                dialog_class = getattr(module, class_name)
                dialog = dialog_class(None, user_id=test_user)
                print(f"  ✅ {dialog_name}: Instantiation successful")
                results[dialog_name] = "INSTANTIATION_SUCCESS"
                dialog.close()
            except Exception as e:
                print(f"  ❌ {dialog_name}: Instantiation failed - {e}")
                results[dialog_name] = f"INSTANTIATION_FAILED: {e}"
        
        return results
        
    except Exception as e:
        print(f"  ❌ Dialog instantiation testing failed: {e}")
        return {"error": str(e)}

def main():
    """Run all tests and generate a comprehensive report"""
    print("🎯 MHM Dialog Testing - Systematic Analysis (READ-ONLY)")
    print("=" * 60)
    
    # Run all tests
    dialog_imports = test_dialog_imports()
    widget_imports = test_widget_imports()
    ui_files = test_ui_files_exist()
    generated_files = test_generated_files_exist()
    user_data = test_user_data_access()
    dialog_instantiation = test_dialog_instantiation()
    
    # Generate summary
    print("\n" + "=" * 60)
    print("📊 TESTING SUMMARY")
    print("=" * 60)
    
    # Dialog import summary
    dialog_success = sum(1 for result in dialog_imports.values() if "SUCCESS" in result)
    dialog_total = len(dialog_imports)
    print(f"Dialogs: {dialog_success}/{dialog_total} import successfully")
    
    # Widget import summary
    widget_success = sum(1 for result in widget_imports.values() if "SUCCESS" in result)
    widget_total = len(widget_imports)
    print(f"Widgets: {widget_success}/{widget_total} import successfully")
    
    # UI files summary
    ui_success = sum(1 for result in ui_files.values() if "EXISTS" in result)
    ui_total = len(ui_files)
    print(f"UI Files: {ui_success}/{ui_total} exist")
    
    # Generated files summary
    gen_success = sum(1 for result in generated_files.values() if "EXISTS" in result)
    gen_total = len(generated_files)
    print(f"Generated Files: {gen_success}/{gen_total} exist")
    
    # User data summary
    if "error" not in user_data:
        print(f"User Data: ✅ Accessible ({user_data['total_users']} total users)")
    else:
        print(f"User Data: ❌ {user_data['error']}")
    
    # Dialog instantiation summary
    if "error" not in dialog_instantiation:
        inst_success = sum(1 for result in dialog_instantiation.values() if "SUCCESS" in result)
        inst_total = len(dialog_instantiation)
        print(f"Dialog Instantiation: {inst_success}/{inst_total} successful")
    else:
        print(f"Dialog Instantiation: ❌ {dialog_instantiation['error']}")
    
    # Detailed results
    print("\n📋 DETAILED RESULTS")
    print("-" * 40)
    
    print("\n🔧 Dialog Import Issues:")
    for dialog, result in dialog_imports.items():
        if "SUCCESS" not in result:
            print(f"  ❌ {dialog}: {result}")
    
    print("\n🔧 Widget Import Issues:")
    for widget, result in widget_imports.items():
        if "SUCCESS" not in result:
            print(f"  ❌ {widget}: {result}")
    
    print("\n🔧 Missing UI Files:")
    for ui, result in ui_files.items():
        if "MISSING" in result:
            print(f"  ❌ {ui}: {result}")
    
    print("\n🔧 Missing Generated Files:")
    for gen, result in generated_files.items():
        if "MISSING" in result:
            print(f"  ❌ {gen}: {result}")
    
    print("\n🔧 Dialog Instantiation Issues:")
    if "error" not in dialog_instantiation:
        for dialog, result in dialog_instantiation.items():
            if "SUCCESS" not in result:
                print(f"  ❌ {dialog}: {result}")
    else:
        print(f"  ❌ {dialog_instantiation['error']}")
    
    print("\n" + "=" * 60)
    print("✅ Testing Complete! (No data was modified)")
    print("=" * 60)

if __name__ == "__main__":
    main() 