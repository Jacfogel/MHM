# TOOL_TIER: core
"""Audit artifact storage scope: full repo vs dev-tools-only.

Both layouts live under parallel trees:

- ``development_tools/<domain>/jsons/scopes/full/`` — full-repo audits (default)
- ``development_tools/<domain>/jsons/scopes/dev_tools/`` — ``--dev-tools-only``
- ``development_tools/reports/scopes/<full|dev_tools>/...`` — aggregated JSON and timings

**Reads:** tool JSON only under ``jsons/scopes/<full|dev_tools>/``; Tier 3 aggregates and
``tool_timings.json`` only under ``reports/scopes/<scope>/`` (V5 §7.16). ``--clear-cache`` may
still remove orphan unscoped files left from older runs.
"""

from __future__ import annotations

from contextvars import ContextVar, Token
from pathlib import Path
from typing import Any

AUDIT_SCOPE_USE_CONTEXT = object()
_SENTINEL = AUDIT_SCOPE_USE_CONTEXT

STORAGE_SCOPE_FULL = "full"
STORAGE_SCOPE_DEV_TOOLS = "dev_tools"

_audit_storage_scope: ContextVar[str] = ContextVar(
    "audit_storage_scope", default=STORAGE_SCOPE_FULL
)


def get_audit_storage_scope() -> str:
    return _audit_storage_scope.get()


def set_audit_storage_scope(scope: str) -> Token[Any]:
    return _audit_storage_scope.set(scope)


def reset_audit_storage_scope(token: Token[Any]) -> None:
    _audit_storage_scope.reset(token)


def effective_storage_scope(explicit: str | object = _SENTINEL) -> str:
    if explicit is _SENTINEL:
        return _audit_storage_scope.get()
    if explicit == STORAGE_SCOPE_DEV_TOOLS:
        return STORAGE_SCOPE_DEV_TOOLS
    if explicit == STORAGE_SCOPE_FULL:
        return STORAGE_SCOPE_FULL
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
    configured_relative: str,
    audit_scope: str | object = AUDIT_SCOPE_USE_CONTEXT,
) -> Path:
    scope = effective_storage_scope(audit_scope)  # type: ignore[arg-type]
    path = (Path(project_root).resolve() / configured_relative).resolve()
    parts = path.parts
    reports_idx: int | None = None
    for i, part in enumerate(parts):
        if part == "reports":
            reports_idx = i
            break
    if reports_idx is None:
        return path
    tail = Path(*parts[reports_idx + 1 :])
    prefix = Path(*parts[: reports_idx + 1])
    return (prefix / "scopes" / scope / tail).resolve()


def scoped_tool_timings_path(
    project_root: Path,
    *,
    audit_scope: str | object = AUDIT_SCOPE_USE_CONTEXT,
) -> Path:
    scope = effective_storage_scope(audit_scope)  # type: ignore[arg-type]
    base = Path(project_root).resolve() / "development_tools" / "reports"
    return base / "scopes" / scope / "jsons" / "tool_timings.json"
