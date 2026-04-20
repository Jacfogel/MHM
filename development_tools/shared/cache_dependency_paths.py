# TOOL_TIER: core

"""Canonical repo-relative paths that participate in dev-tools cache invalidation.

``STATIC_CHECK_CONFIG_RELATIVE_PATHS`` is hashed by
:class:`~development_tools.shared.service.tool_wrappers.ToolWrappersMixin` static-check
caching (Ruff / Pyright / Bandit) in addition to the full ``*.py`` tree. Coverage
tooling aligns its invalidation hash with the same paths so
``development_tools_config.json`` and analysis toggles cannot drift between
subsystems.

``PIP_AUDIT_DEPENDENCY_RELATIVE_PATHS`` / :func:`requirements_lock_signature` feed
pip-audit JSON cache invalidation in ``tool_wrappers`` (same digest as historical
wrapper logic).

Paths use forward slashes; resolve with ``Path(project_root) / rel``.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

# pyproject.toml: root Pyright/Bandit and merged tool settings.
# development_tools/config/development_tools_config.json: exclusions, domains, analyzer toggles.
# development_tools/config/pyrightconfig.json: audit Pyright --project baseline.
# development_tools/config/ruff.toml: primary Ruff config passed via --config.
# .ruff.toml: optional root compatibility mirror (e.g. sync_ruff_toml); include when present.
STATIC_CHECK_CONFIG_RELATIVE_PATHS: tuple[str, ...] = (
    "pyproject.toml",
    "development_tools/config/development_tools_config.json",
    "development_tools/config/pyrightconfig.json",
    "development_tools/config/ruff.toml",
    ".ruff.toml",
)


def static_check_config_paths(project_root: Path) -> tuple[Path, ...]:
    """Return absolute paths for each static-check config entry (may be missing)."""
    root = Path(project_root).resolve()
    return tuple(root / rel for rel in STATIC_CHECK_CONFIG_RELATIVE_PATHS)


# Pip-audit cache (tool_wrappers._try_pip_audit_cache) invalidates when these change.
PIP_AUDIT_DEPENDENCY_RELATIVE_PATHS: tuple[str, ...] = ("requirements.txt", "pyproject.toml")


def requirements_lock_signature(project_root: Path) -> str | None:
    """SHA-256 of dependency files used for pip-audit JSON cache invalidation.

    Same algorithm as historical ``tool_wrappers._compute_requirements_lock_signature``:
    for each present file in order, update the digest with
    ``name.encode() + NUL + file_bytes``.
    Returns ``None`` if no listed file exists.
    """
    try:
        root = Path(project_root).resolve()
        h = hashlib.sha256()
        found = False
        for name in PIP_AUDIT_DEPENDENCY_RELATIVE_PATHS:
            p = root / name
            if p.is_file():
                found = True
                h.update(name.encode("utf-8"))
                h.update(b"\0")
                with open(p, "rb") as handle:
                    h.update(handle.read())
        return h.hexdigest() if found else None
    except Exception:
        return None
