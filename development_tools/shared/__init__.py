"""Service layer package for run_development_tools commands.

Contains shared services and utilities used by AI development tools,
including file exclusion logic, common operations, and configuration management.
"""

# Main public API - package-level exports for easier refactoring
from .standard_exclusions import (
    should_exclude_file,
    get_exclusions,
    get_coverage_exclusions,
    get_analysis_exclusions,
    get_documentation_exclusions,
)
from .exclusion_utilities import (
    is_auto_generated_code,
    is_special_python_method,
    is_test_function,
)
from .constants import (
    is_local_module,
    is_standard_library_module,
)

__all__ = [
    # File exclusion
    'should_exclude_file',
    'get_exclusions',
    'get_coverage_exclusions',
    'get_analysis_exclusions',
    'get_documentation_exclusions',
    # Function/code exclusion utilities
    'is_auto_generated_code',
    'is_special_python_method',
    'is_test_function',
    # Module classification
    'is_local_module',
    'is_standard_library_module',
]
