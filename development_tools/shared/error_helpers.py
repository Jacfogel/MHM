#!/usr/bin/env python3
# TOOL_TIER: core

"""
Dev-tools-local error handling helpers.

Provides a thin handle_errors-like decorator using development_tools.shared.logging,
so development_tools remains portable and does not import from core.error_handling.
"""

from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any

from development_tools.shared.logging import get_dev_tools_logger

logger = get_dev_tools_logger("development_tools")


def handle_errors(
    operation: str | None = None,
    context: dict[str, Any] | None = None,
    user_friendly: bool = True,
    default_return: Any = None,
    re_raise: bool = False,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator to catch exceptions, log them, and return default_return.

    Compatible subset of core.error_handling.handle_errors for dev-tools use.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            op_name = operation or func.__name__
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                logger.debug(f"{op_name} failed: {exc}", exc_info=True)
                if re_raise:
                    raise
                return default_return

        return wrapper

    return decorator
