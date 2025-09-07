#!/usr/bin/env python3
"""
Systematic Dialog Testing Script for MHM
Tests all dialogs to see what works and what's broken
READ-ONLY - Does not modify any user data
"""

import sys
import os
import time
import logging
import pytest
from pathlib import Path

# Do not modify sys.path; rely on package imports

@pytest.mark.ui
@pytest.mark.critical
@pytest.mark.regression
@pytest.mark.slow
def test_dialog_imports():
    """Test that all dialog modules can be imported without errors"""
    # logging via mhm_tests logger preferred over print
    
    dialogs_to_test = [
        ("Account Creator", "ui.dialogs.account_creator_dialog", "AccountCreatorDialog"),
        ("Channel Management", "ui.dialogs.channel_management_dialog", "ChannelManagementDialog"),
        ("Category Management", "ui.dialogs.category_management_dialog", "CategoryManagementDialog"),
        ("Check-in Management", "ui.dialogs.checkin_management_dialog", "CheckinManagementDialog"),
        ("Task Management", "ui.dialogs.task_management_dialog", "TaskManagementDialog"),
        ("User Profile", "ui.dialogs.user_profile_dialog", "UserProfileDialog"),
        ("Schedule Editor", "ui.dialogs.schedule_editor_dialog", "open_schedule_editor"),
        ("Main UI", "ui.ui_app_qt", "MHMManagerUI"),
    ]
    
    for dialog_name, module_path, class_name in dialogs_to_test:
        try:
            module = __import__(module_path, fromlist=[class_name])
            dialog_class = getattr(module, class_name)
            # logging via mhm_tests logger preferred over print
            assert callable(dialog_class), f"{dialog_name}: Class is not callable"
        except ImportError as e:
            # logging via mhm_tests logger preferred over print
            assert False, f"{dialog_name}: Import failed - {e}"
        except AttributeError as e:
            # logging via mhm_tests logger preferred over print
            assert False, f"{dialog_name}: Class not found - {e}"
        except Exception as e:
            # logging via mhm_tests logger preferred over print
            assert False, f"{dialog_name}: Unexpected error - {e}"

@pytest.mark.ui
@pytest.mark.critical
@pytest.mark.regression
@pytest.mark.slow
def test_widget_imports():
    """Test that all widget modules can be imported without errors"""
    # logging via mhm_tests logger preferred over print
    
    widgets_to_test = [
        ("Category Selection", "ui.widgets.category_selection_widget", "CategorySelectionWidget"),
        ("Channel Selection", "ui.widgets.channel_selection_widget", "ChannelSelectionWidget"),
        ("Check-in Settings", "ui.widgets.checkin_settings_widget", "CheckinSettingsWidget"),
        ("Task Settings", "ui.widgets.task_settings_widget", "TaskSettingsWidget"),
        ("User Profile Settings", "ui.widgets.user_profile_settings_widget", "UserProfileSettingsWidget"),
        ("Period Row", "ui.widgets.period_row_widget", "PeriodRowWidget"),
    ]
    
    for widget_name, module_path, class_name in widgets_to_test:
        try:
            module = __import__(module_path, fromlist=[class_name])
            widget_class = getattr(module, class_name)
            # logging via mhm_tests logger preferred over print
            assert callable(widget_class), f"{widget_name}: Class is not callable"
        except ImportError as e:
            # logging via mhm_tests logger preferred over print
            assert False, f"{widget_name}: Import failed - {e}"
        except AttributeError as e:
            # logging via mhm_tests logger preferred over print
            assert False, f"{widget_name}: Class not found - {e}"
        except Exception as e:
            # logging via mhm_tests logger preferred over print
            assert False, f"{widget_name}: Unexpected error - {e}"

@pytest.mark.ui
@pytest.mark.critical
@pytest.mark.regression
@pytest.mark.slow
def test_ui_files_exist():
    """Test that all required UI files exist"""
    # logging via mhm_tests logger preferred over print
    
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
    
    for ui_name, file_path in ui_files_to_test:
        if os.path.exists(file_path):
            # logging via mhm_tests logger preferred over print
            assert True, f"{ui_name}: UI file should exist"
        else:
            # logging via mhm_tests logger preferred over print
            assert False, f"{ui_name}: UI file missing - {file_path}"

@pytest.mark.ui
@pytest.mark.critical
@pytest.mark.regression
@pytest.mark.slow
def test_generated_files_exist():
    """Test that all generated Python UI files exist"""
    # logging via mhm_tests logger preferred over print
    
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
    
    for file_name, file_path in generated_files_to_test:
        if os.path.exists(file_path):
            # logging via mhm_tests logger preferred over print
            assert True, f"{file_name}: Generated file should exist"
        else:
            # logging via mhm_tests logger preferred over print
            assert False, f"{file_name}: Generated file missing - {file_path}"

@pytest.mark.ui
@pytest.mark.critical
@pytest.mark.regression
@pytest.mark.slow
def test_user_data_access(test_data_dir, mock_config, mock_user_data):
    """Test that we can access user data for testing - READ ONLY"""
    logger = logging.getLogger("mhm_tests")
    
    try:
        from core.user_data_handlers import get_user_data
        from core.user_data_handlers import get_all_user_ids
        
        # Get all user IDs
        user_ids = get_all_user_ids()
        logger.debug(f"Total users found: {len(user_ids)}")
        
        # Use the mock user data that was created by the fixture
        test_user = mock_user_data['user_id']
        logger.debug(f"Testing with user: {test_user}")
        
        # Test account data (read-only)
        try:
            from tests.conftest import materialize_user_minimal_via_public_apis
            materialize_user_minimal_via_public_apis(test_user)
            account_data = get_user_data(test_user, 'account')
            logger.debug(f"Account data accessible for {test_user}")
            assert account_data is not None, f"Account data should be accessible for {test_user}"
            assert 'account' in account_data, f"Account data should contain 'account' key for {test_user}"
        except Exception as e:
            logger.error(f"Account data failed for {test_user}: {e}")
            assert False, f"Account data failed for {test_user}: {e}"
        
        # Test preferences data (read-only)
        try:
            from tests.conftest import materialize_user_minimal_via_public_apis
            materialize_user_minimal_via_public_apis(test_user)
            prefs_data = get_user_data(test_user, 'preferences')
            logger.debug(f"Preferences data accessible for {test_user}")
            assert prefs_data is not None, f"Preferences data should be accessible for {test_user}"
            assert 'preferences' in prefs_data, f"Preferences data should contain 'preferences' key for {test_user}"
        except Exception as e:
            logger.error(f"Preferences data failed for {test_user}: {e}")
            assert False, f"Preferences data failed for {test_user}: {e}"
        
        # Test context data (read-only)
        try:
            from tests.conftest import materialize_user_minimal_via_public_apis
            materialize_user_minimal_via_public_apis(test_user)
            context_data = get_user_data(test_user, 'context')
            logger.debug(f"Context data accessible for {test_user}")
            assert context_data is not None, f"Context data should be accessible for {test_user}"
            assert 'context' in context_data, f"Context data should contain 'context' key for {test_user}"
        except Exception as e:
            logger.error(f"Context data failed for {test_user}: {e}")
            assert False, f"Context data failed for {test_user}: {e}"
        
    except Exception as e:
        logger.error(f"User data access failed: {e}")
        assert False, f"User data access failed: {e}"

@pytest.mark.ui
@pytest.mark.critical
@pytest.mark.regression
@pytest.mark.slow
def test_dialog_instantiation(monkeypatch):
    """Test that dialogs can be instantiated (without showing them)"""
    logger = logging.getLogger("mhm_tests")
    
    # We'll test this with a mock parent and test user
    try:
        from PySide6.QtWidgets import QApplication
        import sys
        
        # Create a minimal QApplication if one doesn't exist
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Set up test environment
        monkeypatch.setenv('MHM_TESTING', '1')
        monkeypatch.setenv('CATEGORIES', '["motivational", "health", "quotes_to_ponder", "word_of_the_day", "fun_facts"]')
        
        # Import and set up communication manager for testing
        from communication.core.channel_orchestrator import CommunicationManager
        comm_manager = CommunicationManager()
        
        # Test with a safe test user
        test_user = "test-user"  # Use the basic test user
        
        # Test Account Creator Dialog
        try:
            from ui.dialogs.account_creator_dialog import AccountCreatorDialog
            
            dialog = AccountCreatorDialog(None, comm_manager)
            logger.debug("Account Creator: Instantiation successful")
            assert dialog is not None, "Account Creator dialog should be instantiated"
            dialog.close()
            comm_manager.stop_all()
        except Exception as e:
            logger.error(f"Account Creator instantiation failed: {e}")
            assert False, f"Account Creator instantiation failed: {e}"
        
        # Test User Profile Dialog
        try:
            from ui.dialogs.user_profile_dialog import UserProfileDialog
            
            def mock_save(data):
                pass  # Do nothing
            
            dialog = UserProfileDialog(None, test_user, mock_save)
            logger.debug("User Profile: Instantiation successful")
            assert dialog is not None, "User Profile dialog should be instantiated"
            dialog.close()
        except Exception as e:
            logger.error(f"User Profile instantiation failed: {e}")
            assert False, f"User Profile instantiation failed: {e}"
        
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
                # logging via mhm_tests logger preferred over print
                assert dialog is not None, f"{dialog_name} dialog should be instantiated"
                dialog.close()
            except Exception as e:
                # logging via mhm_tests logger preferred over print
                assert False, f"{dialog_name} instantiation failed: {e}"
        
    except Exception as e:
        # logging via mhm_tests logger preferred over print
        assert False, f"Dialog instantiation testing failed: {e}"
    finally:
        pass

# Note: This file contains pytest test functions that should be run with pytest
# The main() function has been removed as it's not compatible with pytest
# Run tests with: python -m pytest tests/ui/test_dialogs.py 