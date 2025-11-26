"""
Test file for coverage runs.

This file contains test functions to test coverage metric generation.
"""

try:
    import pytest
except ImportError:
    # pytest may not be available in fixture project
    pass

try:
    from demo_module import simple_function, DemoClass
except ImportError:
    # Handle case where running as standalone
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from demo_module import simple_function, DemoClass


def test_simple_function():
    """Test the simple_function."""
    assert simple_function(2, 3) == 5
    assert simple_function(0, 0) == 0
    assert simple_function(-1, 1) == 0


def test_demo_class():
    """Test the DemoClass."""
    instance = DemoClass("test_name")
    assert instance.get_name() == "test_name"
    
    instance.set_name("new_name")
    assert instance.get_name() == "new_name"


def test_integration():
    """Integration test."""
    instance = DemoClass("integration_test")
    result = simple_function(10, 20)
    assert result == 30
    assert instance.get_name() == "integration_test"

