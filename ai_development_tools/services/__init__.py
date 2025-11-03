"""Service layer package for ai_tools_runner commands.

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
    # Module classification
    'is_local_module',
    'is_standard_library_module',
]
