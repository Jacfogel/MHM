"""
Direct tests for AccountCreatorDialog validation methods.

These tests focus on the validation logic without UI dependencies.
"""
from tests.conftest import ensure_qt_runtime

ensure_qt_runtime()


import pytest

from unittest.mock import patch


@pytest.mark.ui
class TestAccountCreatorDialogValidation:
    """Test AccountCreatorDialog validation methods directly."""
    
    def test_username_validation_valid(self):
        """Test username validation with valid usernames."""
        from ui.dialogs.account_creator_dialog import AccountCreatorDialog
        
        # Test various valid usernames
        valid_usernames = [
            "testuser",
            "user123", 
            "test_user",
            "user-test",
            "a",  # minimum length
            "a" * 50,  # maximum length
        ]
        
        for username in valid_usernames:
            # Test the validation method directly without instantiating the dialog
            result = AccountCreatorDialog.validate_username_static(username)
            assert result, f"Username '{username}' should be valid"
    
    def test_username_validation_invalid(self):
        """Test username validation with invalid usernames."""
        from ui.dialogs.account_creator_dialog import AccountCreatorDialog
        
        invalid_usernames = [
            "",  # empty
            "a" * 51,  # too long
            "user@test",  # invalid character
            "user space",  # space
            "user.name",  # dot
            "user/name",  # slash
            "user\\name",  # backslash
        ]
        
        for username in invalid_usernames:
            result = AccountCreatorDialog.validate_username_static(username)
            assert not result, f"Username '{username}' should be invalid"
    
    def test_preferred_name_validation_valid(self):
        """Test preferred name validation with valid names."""
        from ui.dialogs.account_creator_dialog import AccountCreatorDialog
        
        valid_names = [
            "John",
            "Mary Jane",
            "O'Connor",
            "Jean-Pierre",
            "José",
            "李小明",
            "a",  # minimum length
            "a" * 100,  # maximum length
        ]
        
        for name in valid_names:
            result = AccountCreatorDialog.validate_preferred_name_static(name)
            assert result, f"Preferred name '{name}' should be valid"
    
    def test_preferred_name_validation_invalid(self):
        """Test preferred name validation with invalid names."""
        from ui.dialogs.account_creator_dialog import AccountCreatorDialog
        
        invalid_names = [
            "",  # empty
            "a" * 101,  # too long
            "John@Doe",  # invalid character
            "John/Doe",  # slash
            "John\\Doe",  # backslash
        ]
        
        for name in invalid_names:
            result = AccountCreatorDialog.validate_preferred_name_static(name)
            assert not result, f"Preferred name '{name}' should be invalid"
    
    def test_validate_all_fields_static_valid(self):
        """Test static validation when all fields are valid."""
        from ui.dialogs.account_creator_dialog import AccountCreatorDialog
        
        result = AccountCreatorDialog.validate_all_fields_static("testuser", "Test User")
        assert result, "All valid fields should pass validation"
    
    def test_validate_all_fields_static_invalid_username(self):
        """Test static validation when username is invalid."""
        from ui.dialogs.account_creator_dialog import AccountCreatorDialog
        
        result = AccountCreatorDialog.validate_all_fields_static("", "Test User")
        assert not result, "Invalid username should fail validation"
    
    def test_validate_all_fields_static_invalid_preferred_name(self):
        """Test static validation when preferred name is invalid."""
        from ui.dialogs.account_creator_dialog import AccountCreatorDialog
        
        result = AccountCreatorDialog.validate_all_fields_static("testuser", "")
        assert not result, "Invalid preferred name should fail validation"

