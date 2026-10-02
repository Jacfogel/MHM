"""
Direct tests for AccountCreatorDialog validation methods.

These tests focus on the validation logic without UI dependencies.
"""
from tests.conftest import ensure_qt_runtime

ensure_qt_runtime()


import pytest


@pytest.mark.ui
class TestAccountCreatorDialogValidation:
    """Test AccountCreatorDialog validation methods directly."""
    
    def test_preferred_name_validation_accepts_display_names(self):
        """Test preferred-name validation with valid display names."""
        from ui.dialogs.account_creator_dialog import AccountCreatorDialog
        
        valid_names = ["Test User", "Jean-Pierre", "José", "李小明", "a", "a" * 100]
        
        for name in valid_names:
            result = AccountCreatorDialog.validate_preferred_name_static(name)
            assert result, f"Preferred name '{name}' should be valid"
    
    def test_preferred_name_validation_rejects_invalid_names(self):
        """Test preferred-name validation with invalid names."""
        from ui.dialogs.account_creator_dialog import AccountCreatorDialog
        
        invalid_names = ["", "   ", "a" * 101, "John@Doe", "John/Doe", "John\\Doe"]
        
        for name in invalid_names:
            result = AccountCreatorDialog.validate_preferred_name_static(name)
            assert not result, f"Preferred name '{name}' should be invalid"

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
        
        result = AccountCreatorDialog.validate_all_fields_static("Test User")
        assert result, "All valid fields should pass validation"

    def test_validate_all_fields_static_invalid_preferred_name(self):
        """Test static validation when preferred name is invalid."""
        from ui.dialogs.account_creator_dialog import AccountCreatorDialog

        result = AccountCreatorDialog.validate_all_fields_static("")
        assert not result, "Invalid preferred name should fail validation"
