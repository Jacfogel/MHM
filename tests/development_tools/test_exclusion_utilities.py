#!/usr/bin/env python3
"""
Tests for shared exclusion utilities.

Tests the function-level exclusion logic used across analysis tools.
"""

import pytest
from pathlib import Path

from tests.development_tools.conftest import load_development_tools_module

# Load exclusion utilities module
exclusion_utilities = load_development_tools_module("shared.exclusion_utilities")
is_generated_file = exclusion_utilities.is_generated_file
is_generated_function = exclusion_utilities.is_generated_function
is_special_python_method = exclusion_utilities.is_special_python_method
is_test_function = exclusion_utilities.is_test_function


class TestGeneratedCode:
    """Test generated file/function detection."""

    @pytest.mark.unit
    def test_pyqt_generated_file(self):
        """Test PyQt generated file detection."""
        assert is_generated_file("ui/generated/main_window_pyqt.py")
        assert is_generated_file("ui\\generated\\main_window_pyqt.py")

    @pytest.mark.unit
    def test_generated_directory(self):
        """Test generated directory detection."""
        assert is_generated_file("ui/generated/widget.py")
        assert is_generated_file("ui\\generated\\widget.py")

    @pytest.mark.unit
    def test_generated_file_patterns(self):
        """Test generated file name patterns."""
        assert is_generated_file("widget_pyqt.py")
        assert is_generated_file("widget_ui.py")
        assert is_generated_file("widget_generated.py")
        assert is_generated_file("widget_auto.py")

    @pytest.mark.unit
    def test_generated_function_patterns(self):
        """Test generated function name patterns."""
        assert is_generated_function("setupUi")
        assert is_generated_function("retranslateUi")
        assert is_generated_function("setup_ui")
        assert is_generated_function("retranslate_ui")
        assert is_generated_function("setup_ui_main")  # contains "setup_ui_"
        assert is_generated_function(
            "retranslate_ui_main"
        )  # contains "retranslate_ui_"
        assert is_generated_function("func_generated_helper")  # contains "_generated_"
        assert is_generated_function("func_auto_helper")  # contains "_auto_"

    @pytest.mark.unit
    def test_normal_code_not_excluded(self):
        """Test that normal code is not excluded."""
        assert not (
            is_generated_file("core/service.py")
            or is_generated_function("handle_message")
        )
        assert not (
            is_generated_file("communication/channel.py")
            or is_generated_function("process_request")
        )
        assert not (
            is_generated_file("ui/main_window.py")
            or is_generated_function("show_dialog")
        )


class TestSpecialPythonMethods:
    """Test special Python method detection."""

    @pytest.mark.unit
    def test_special_methods_excluded(self):
        """Test that special methods are excluded."""
        assert is_special_python_method("__repr__")
        assert is_special_python_method("__str__")
        assert is_special_python_method("__eq__")
        assert is_special_python_method("__hash__")
        assert is_special_python_method("__len__")
        assert is_special_python_method("__call__")
        assert is_special_python_method("__getitem__")
        assert is_special_python_method("__iter__")
        assert is_special_python_method("__add__")

    @pytest.mark.unit
    def test_context_managers_not_excluded(self):
        """Test that context managers are not excluded (should be documented)."""
        assert not is_special_python_method("__enter__")
        assert not is_special_python_method("__exit__")

    @pytest.mark.unit
    def test_simple_init_excluded(self):
        """Test that simple __init__ methods are excluded."""
        assert is_special_python_method("__init__", complexity=10)
        assert is_special_python_method("__init__", complexity=19)

    @pytest.mark.unit
    def test_complex_init_not_excluded(self):
        """Test that complex __init__ methods are not excluded."""
        assert not is_special_python_method("__init__", complexity=20)
        assert not is_special_python_method("__init__", complexity=50)

    @pytest.mark.unit
    def test_normal_methods_not_excluded(self):
        """Test that normal methods are not excluded."""
        assert not is_special_python_method("handle_message")
        assert not is_special_python_method("process_request")
        assert not is_special_python_method("validate_input")


class TestTestFunction:
    """Test test function detection."""

    @pytest.mark.unit
    def test_test_prefix(self):
        """Test functions starting with test_."""
        assert is_test_function("test_something")
        assert is_test_function("test_handle_message")

    @pytest.mark.unit
    def test_test_in_name(self):
        """Test functions with test in name."""
        assert is_test_function("test_something")
        assert is_test_function("unit_test_helper")
        assert is_test_function("integration_test")

    @pytest.mark.unit
    def test_test_file_path(self):
        """Test functions in test files."""
        assert is_test_function("some_function", file_path="tests/test_service.py")
        assert is_test_function("some_function", file_path="tests\\test_service.py")
        assert is_test_function("some_function", file_path="test_helper.py")

    @pytest.mark.unit
    def test_normal_functions_not_excluded(self):
        """Test that normal functions are not excluded."""
        assert not is_test_function("handle_message")
        assert not is_test_function("process_request")
        assert not is_test_function("validate_input")
        assert not is_test_function("handle_message", file_path="core/service.py")

    @pytest.mark.unit
    def test_test_function_in_normal_file(self):
        """Test that test functions in normal files are still detected."""
        # Function name takes precedence
        assert is_test_function("test_helper", file_path="core/service.py")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
