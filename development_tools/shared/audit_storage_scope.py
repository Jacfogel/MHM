# TOOL_TIER: core
"""Audit artifact storage scope: full repo, dev-tools-only, or path-derived scopes.

Layouts live under parallel trees:

- ``development_tools/<domain>/jsons/scopes/full/`` — full-repo audits (default)
- ``development_tools/<domain>/jsons/scopes/dev_tools/`` — ``--dev-tools-only``
- ``development_tools/<domain>/jsons/scopes/scope_<slug>/`` — ``--audit-scope <path>`` (B-016 MVP)
- ``development_tools/reports/scopes/<scope>/...`` — aggregated JSON and timings

**Reads:** tool JSON under ``jsons/scopes/<scope>/``; Tier 3 aggregates and
``tool_timings.json`` under ``reports/scopes/<scope>/`` (V5 §7.16). ``--clear-cache`` may
still remove orphan unscoped files left from older runs.
"""

from __future__ import annotations

from contextvars import ContextVar, Token
from pathlib import Path
from typing import Any

from development_tools.shared.audit_scope import (
    STORAGE_SCOPE_DEV_TOOLS as STORAGE_SCOPE_DEV_TOOLS,
    STORAGE_SCOPE_FULL as STORAGE_SCOPE_FULL,
    is_known_storage_scope,
)

AUDIT_SCOPE_USE_CONTEXT = object()
_SENTINEL = AUDIT_SCOPE_USE_CONTEXT

_audit_storage_scope: ContextVar[str] = ContextVar(
    "audit_storage_scope", default=STORAGE_SCOPE_FULL
)


def get_audit_storage_scope() -> str:
    return _audit_storage_scope.get()


def set_audit_storage_scope(scope: str) -> Token[Any]:
    if not is_known_storage_scope(str(scope)):
        raise ValueError(f"unsupported audit storage scope: {scope!r}")
    return _audit_storage_scope.set(str(scope))


def reset_audit_storage_scope(token: Token[Any]) -> None:
    _audit_storage_scope.reset(token)


def effective_storage_scope(explicit: str | object = _SENTINEL) -> str:
    if explicit is _SENTINEL:
        return _audit_storage_scope.get()
    scope = str(explicit)
    if is_known_storage_scope(scope):
        return scope
    return STORAGE_SCOPE_FULL


def jsons_dir_for_scope(
    project_root: Path,
    domain: str,
    *,
    audit_scope: str | object = AUDIT_SCOPE_USE_CONTEXT,
) -> Path:
    scope = effective_storage_scope(audit_scope)  # type: ignore[arg-type]
    base = Path(project_root).resolve() / "development_tools" / domain / "jsons"
    return base / "scopes" / scope


def legacy_flat_jsons_dir(project_root: Path, domain: str) -> Path:
    """Path to pre-scopes flat ``development_tools/<domain>/jsons`` (no longer read by tool loaders).

    Retained for cleanup helpers and inventory search terms; see V5 §7.16.
    """
    return Path(project_root).resolve() / "development_tools" / domain / "jsons"


def scoped_analysis_detailed_path(
    project_root: Path,
    *,
    configured_relative: str | None = None,
    audit_scope: str | object = AUDIT_SCOPE_USE_CONTEXT,
) -> Path:
    """Resolve the host's aggregate file without mixing results from different scopes."""
    from development_tools.config import QUICK_AUDIT, get_quick_audit_config

    scope = effective_storage_scope(audit_scope)
    if configured_relative is None:
        configured = get_quick_audit_config().get("results_file")
        default = str(QUICK_AUDIT["results_file"])
        configured_relative = configured if isinstance(configured, str) and configured.strip() else default

    root = Path(project_root).resolve()
    path = (root / configured_relative).resolve()
    # Only consider directories inside the selected host. A parent of the host
    # named "reports" must not redirect output outside that host.
    layout = path.relative_to(root) if path.is_relative_to(root) else Path(configured_relative)
    directories = layout.parts[:-1]
    if "reports" in directories:
        parts_after_reports = len(directories) - directories.index("reports") - 1
        base = path.parents[parts_after_reports]
        return base / "scopes" / scope / path.relative_to(base)
    if scope == STORAGE_SCOPE_FULL:
        return path
    return path.parent / "scopes" / scope / path.name


def scoped_tool_timings_path(
    project_root: Path,
    *,
    audit_scope: str | object = AUDIT_SCOPE_USE_CONTEXT,
) -> Path:
    scope = effective_storage_scope(audit_scope)  # type: ignore[arg-type]
    base = Path(project_root).resolve() / "development_tools" / "reports"
    return base / "scopes" / scope / "jsons" / "tool_timings.json"
