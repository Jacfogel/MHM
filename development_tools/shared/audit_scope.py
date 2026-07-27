# TOOL_TIER: core
"""Arbitrary audit-scope helpers (V6 B-016 thin MVP).

Custom scopes are path-derived storage slugs (``scope_<slug>``) plus a
``get_scan_directories()`` override. Tier 3 and tools that ignore scan dirs
are unsupported in the MVP.
"""

from __future__ import annotations

import re
from pathlib import Path

STORAGE_SCOPE_FULL = "full"
STORAGE_SCOPE_DEV_TOOLS = "dev_tools"

# Path-derived scopes: scope_communication, scope_ui_widgets, etc.
_SCOPE_SLUG_RE = re.compile(r"^scope_[a-z0-9]+(?:_[a-z0-9]+)*$")

# Tools known to honor get_scan_directories() (MVP allow-list).
AUDIT_SCOPE_MVP_SUPPORTED_TOOLS: frozenset[str] = frozenset(
    {
        "analyze_functions",
        "analyze_error_handling",
        "analyze_duplicate_functions",
        "analyze_unused_functions",
        "analyze_facade_shims",
        "analyze_module_refactor_candidates",
        "analyze_module_imports",
        "analyze_dependency_patterns",
        "analyze_module_dependencies",
        "analyze_function_registry",
        "analyze_config",
        "analyze_package_exports",
    }
)


class AuditScopeError(ValueError):
    """Invalid ``--audit-scope`` path or slug."""


def normalize_audit_scope_rel_path(raw: str) -> str:
    """Normalize a user-supplied relative path to posix without trailing slash."""
    if raw is None:
        raise AuditScopeError("audit scope path is required")
    text = str(raw).strip().replace("\\", "/")
    if not text or text in {".", "./"}:
        raise AuditScopeError("audit scope path must be a non-empty relative directory")
    if text.startswith("/") or re.match(r"^[A-Za-z]:/", text):
        raise AuditScopeError("audit scope path must be relative to the project root")
    parts = [p for p in text.split("/") if p and p != "."]
    if not parts:
        raise AuditScopeError("audit scope path must be a non-empty relative directory")
    if any(p == ".." for p in parts):
        raise AuditScopeError("audit scope path must not contain '..'")
    return "/".join(parts)


def storage_slug_for_rel_path(rel_posix: str) -> str:
    """Build a filesystem-safe storage slug from a normalized relative path."""
    normalized = normalize_audit_scope_rel_path(rel_posix)
    slug_body = re.sub(r"[^a-z0-9]+", "_", normalized.lower()).strip("_")
    if not slug_body:
        raise AuditScopeError(f"cannot derive storage slug from path: {rel_posix!r}")
    slug = f"scope_{slug_body}"
    if not _SCOPE_SLUG_RE.match(slug):
        raise AuditScopeError(f"invalid derived storage slug: {slug!r}")
    return slug


def is_path_derived_storage_scope(scope: str) -> bool:
    """True when scope is a ``scope_*`` path-derived slug (not full/dev_tools)."""
    return bool(scope and _SCOPE_SLUG_RE.match(str(scope)))


def is_known_storage_scope(scope: str) -> bool:
    """True for full, dev_tools, or a valid path-derived slug."""
    if scope in {STORAGE_SCOPE_FULL, STORAGE_SCOPE_DEV_TOOLS}:
        return True
    return is_path_derived_storage_scope(scope)


def resolve_audit_scope(
    project_root: Path, raw_path: str
) -> tuple[str, str]:
    """Validate path under project_root; return (rel_posix, storage_slug)."""
    rel = normalize_audit_scope_rel_path(raw_path)
    root = Path(project_root).resolve()
    target = (root / rel).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise AuditScopeError(
            f"audit scope path escapes project root: {raw_path!r}"
        ) from exc
    if not target.exists():
        raise AuditScopeError(f"audit scope path does not exist: {rel}")
    if not target.is_dir():
        raise AuditScopeError(f"audit scope path must be a directory: {rel}")
    return rel, storage_slug_for_rel_path(rel)


def filter_tools_for_audit_scope_mvp(
    tool_names: list[str],
) -> tuple[list[str], list[str]]:
    """Split tool names into (supported, skipped) for custom-scope MVP runs."""
    supported = [n for n in tool_names if n in AUDIT_SCOPE_MVP_SUPPORTED_TOOLS]
    skipped = [n for n in tool_names if n not in AUDIT_SCOPE_MVP_SUPPORTED_TOOLS]
    return supported, skipped
