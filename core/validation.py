"""Deprecated.  Use core.user_data_validation instead."""

import warnings
warnings.warn(
    "core.validation is deprecated.  Import from core.user_data_validation",
    DeprecationWarning,
    stacklevel=2,
)

from core.user_data_validation import *  # re-export all symbols for backward compatibility 