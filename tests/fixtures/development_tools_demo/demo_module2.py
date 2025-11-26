"""
Second demo module that imports from demo_module.

This module tests dependency tracking and import extraction.
"""

try:
    from demo_module import simple_function, DemoClass
except ImportError:
    # Handle case where running as standalone
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from demo_module import simple_function, DemoClass

import json
from pathlib import Path


def uses_demo_module(x: int) -> int:
    """Use a function from demo_module."""
    return simple_function(x, 10)


def uses_standard_library() -> dict:
    """Use standard library modules."""
    return json.loads('{"test": "value"}')


def uses_pathlib() -> Path:
    """Use pathlib from standard library."""
    return Path("test.txt")


class ImportsDemoClass:
    """A class that imports and uses DemoClass."""
    
    def __init__(self):
        """Initialize with a DemoClass instance."""
        self.demo = DemoClass("test")
    
    def get_demo_name(self) -> str:
        """Get the name from the demo instance."""
        return self.demo.get_name()

