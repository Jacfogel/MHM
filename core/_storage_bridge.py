"""Temporary helpers for legacy ``core`` storage module import bridges."""

from importlib import import_module
import sys

from core.error_handling import handle_errors


@handle_errors("logging storage bridge import", default_return=None)
def _log_bridge_import(legacy_name: str, storage_name: str) -> None:
    """Log bridge use without depending on logging availability."""
    from core.logger import get_component_logger

    get_component_logger("main").debug(
        f"LEGACY COMPATIBILITY: imported {legacy_name} bridge; use {storage_name}"
    )


@handle_errors("bridging storage module import", re_raise=True)
def bridge_storage_module(legacy_name: str, storage_name: str):
    """Alias a legacy ``core`` storage module name to its ``storage`` module."""
    module = import_module(storage_name)
    _log_bridge_import(legacy_name, storage_name)
    sys.modules[legacy_name] = module
    parent_name, _, child_name = legacy_name.rpartition(".")
    parent = sys.modules.get(parent_name)
    if parent is not None and child_name:
        setattr(parent, child_name, module)
    return module
