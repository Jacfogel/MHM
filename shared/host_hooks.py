# TOOL_TIER: core
# TOOL_PORTABILITY: portable

"""Optional host-project adapters for development_tools.

The tool suite must not import product packages. When a host project exposes
optional services (currently backup), load them from ``host.*`` config.
"""

from __future__ import annotations

import importlib
import os
from pathlib import Path
from typing import Any, Protocol

from development_tools.shared.logging import get_dev_tools_logger

logger = get_dev_tools_logger("development_tools")

TOOLS_PACKAGE_NAME = "development_tools"


class HostBackupLoadError(Exception):
    """Host backup manager is configured but could not be loaded."""


class HostBackupManager(Protocol):
    """Duck-typed contract for a host project's backup manager."""

    def list_backups(self) -> list[dict[str, Any]]:
        """Return backup records, newest first when the host supports ordering."""
        ...

    def validate_backup(self, backup_path: str) -> tuple[bool, list[str]]:
        """Return ``(ok, errors)`` for one backup path."""
        ...

    def restore_backup_to_path(
        self,
        backup_path: str,
        destination: str,
        restore_users: bool = True,
        restore_config: bool = False,
    ) -> bool:
        """Restore into an isolated destination. Must not touch live host data."""
        ...


def get_forbidden_host_import_prefixes() -> tuple[str, ...]:
    """Host package prefixes that development_tools must not import.

    Derived from ``constants.local_module_prefixes``, minus this tools package.
    """
    try:
        from development_tools import config

        constants = config.get_constants_config()
        prefixes = constants.get("local_module_prefixes") or []
        if isinstance(prefixes, (list, tuple)) and prefixes:
            return tuple(
                str(p).strip()
                for p in prefixes
                if str(p).strip() and str(p).strip() != TOOLS_PACKAGE_NAME
            )
    except Exception as exc:
        logger.debug(f"Falling back to portable host-import prefixes: {exc}", exc_info=True)
    return ("core", "tests")


def _module_file_is_inside_project(module: Any, project_root: Path) -> bool:
    """Return True when the imported module's file lives under project_root."""
    candidates: list[str] = []
    mod_file = getattr(module, "__file__", None)
    if isinstance(mod_file, str) and mod_file:
        candidates.append(mod_file)
    spec = getattr(module, "__spec__", None)
    origin = getattr(spec, "origin", None) if spec is not None else None
    if isinstance(origin, str) and origin:
        candidates.append(origin)
    if not candidates:
        return False
    root_key = os.path.normcase(str(Path(project_root).resolve()))
    for raw in candidates:
        try:
            resolved_key = os.path.normcase(str(Path(raw).resolve()))
        except OSError:
            continue
        if resolved_key == root_key or resolved_key.startswith(root_key + os.sep):
            return True
    return False


def load_host_backup_manager(
    project_root: Path | str | None = None,
) -> HostBackupManager | None:
    """Load the configured host backup manager, or None when not configured.

    Raises:
        HostBackupLoadError: module is configured but missing, has no attribute,
            or (when project_root is set) lives outside that project tree.
    """
    try:
        from development_tools import config

        host_config = config.get_host_config()
    except Exception as exc:
        logger.debug(f"Host config unavailable: {exc}", exc_info=True)
        return None

    module_name = str(host_config.get("backup_manager_module") or "").strip()
    if not module_name:
        return None
    attr_name = str(host_config.get("backup_manager_attr") or "backup_manager").strip()
    if not attr_name:
        attr_name = "backup_manager"

    try:
        module = importlib.import_module(module_name)
    except Exception as exc:
        raise HostBackupLoadError(
            f"Host backup manager module {module_name!r} could not be imported: {exc}"
        ) from exc

    if project_root is not None and not _module_file_is_inside_project(
        module, Path(project_root)
    ):
        raise HostBackupLoadError(
            f"Host backup manager {module_name!r} is not inside project_root "
            f"({Path(project_root).resolve()})"
        )

    manager = getattr(module, attr_name, None)
    if manager is None:
        raise HostBackupLoadError(
            f"Host backup manager {module_name!r} has no attribute {attr_name!r}"
        )
    return manager
