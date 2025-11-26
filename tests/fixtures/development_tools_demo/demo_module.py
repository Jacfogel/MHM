"""
Demo module for testing function registry generation.

This module contains various types of functions and classes to test
the function registry generation tool.
"""

import os
from typing import List, Dict


def simple_function(x: int, y: int) -> int:
    """Add two numbers together.
    
    Args:
        x: First number
        y: Second number
    
    Returns:
        Sum of x and y
    """
    return x + y


def function_without_docstring(value: str) -> str:
    return value.upper()


def test_function_example():
    """This is a test function for testing."""
    pass


class DemoClass:
    """A demo class for testing."""
    
    def __init__(self, name: str):
        """Initialize the demo class.
        
        Args:
            name: Name of the instance
        """
        self.name = name
    
    def get_name(self) -> str:
        """Get the name of this instance."""
        return self.name
    
    def set_name(self, name: str) -> None:
        """Set the name of this instance."""
        self.name = name
    
    def _private_method(self) -> None:
        """Private method that should still be captured."""
        pass


class HandlerClass:
    """A handler class for testing handler detection."""
    
    def can_handle(self, intent: str) -> bool:
        """Check if this handler can handle the intent."""
        return intent == "demo"
    
    def handle(self, user_id: str, command: Dict) -> str:
        """Handle a command."""
        return "handled"


def main():
    """Main entry point."""
    # Entry point for demo module - no output needed for fixture
    pass

