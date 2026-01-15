"""AI development tools package.

Contains development and analysis tools for AI-assisted development,
including function discovery, module dependency analysis, coverage metrics,
documentation generation, and code quality assessments.
"""

# Main public API - package-level exports for easier refactoring
# Note: Most tools are scripts (run directly), but we export utilities
# that might be imported programmatically

# Configuration module
from . import config

# Shared utilities (re-exported from subpackage for convenience)
from .shared import (
    should_exclude_file,
    get_exclusions,
    is_local_module,
    is_standard_library_module,
)

__all__ = [
    # Configuration
    "config",
    # Shared (re-exported from shared subpackage)
    "should_exclude_file",
    "get_exclusions",
    "is_local_module",
    "is_standard_library_module",
]
