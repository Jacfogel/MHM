"""
Legacy code module for testing legacy reference cleanup.

This module contains legacy patterns that should be detected and cleaned up.
"""

# LEGACY COMPATIBILITY: This function is kept for backward compatibility
def legacy_function():
    """Legacy function that should be detected."""
    pass


# LEGACY COMPATIBILITY: Old import pattern
# Note: This is commented out to avoid import errors, but the pattern is still detectable
# from bot.communication import old_module  # noqa: F401


def uses_legacy_pattern():
    """Function that uses legacy patterns."""
    # Reference to old bot directory
    old_path = "bot/communication/old_file.py"
    return old_path


class LegacyChannelWrapper:
    """Legacy wrapper class."""
    pass


def _create_legacy_channel_access():
    """Legacy channel access function."""
    pass

