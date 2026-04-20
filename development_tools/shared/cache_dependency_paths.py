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
from collections.abc import Sequence
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


def static_check_config_digest(project_root: Path) -> str | None:
    """SHA-256 over static-check config file bytes (same inputs as tool wrapper config loop).

    Returns ``None`` if no file in :data:`STATIC_CHECK_CONFIG_RELATIVE_PATHS` exists.
    """
    try:
        root = Path(project_root).resolve()
        sig = hashlib.sha256()
        found = False
        for rel in STATIC_CHECK_CONFIG_RELATIVE_PATHS:
            cfg = root / rel
            if cfg.is_file():
                found = True
                sig.update(rel.encode("utf-8"))
                sig.update(b"\0")
                sig.update(cfg.read_bytes())
        return sig.hexdigest() if found else None
    except Exception:
        return None


def _update_sig_with_py_file(sig, root: Path, p: Path) -> None:
    """Update *sig* with one ``*.py`` file using the same algorithm as legacy static-check cache."""
    rel = str(p.relative_to(root)).replace("\\", "/")
    stat = p.stat()
    mtime_ns = getattr(stat, "st_mtime_ns", int(stat.st_mtime * 1_000_000_000))
    sig.update(f"{rel}:{mtime_ns}:{stat.st_size}".encode())
    file_hash = hashlib.sha256()
    with open(p, "rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            file_hash.update(chunk)
    sig.update(file_hash.digest())


def compute_scoped_py_source_signature(
    project_root: Path, rel_roots: Sequence[str], *, tool_type: str = "analysis"
) -> str | None:
    """SHA-256 over ``*.py`` sources under repo-relative *rel_roots* (dirs and/or ``.py`` files).

    Uses :func:`development_tools.shared.standard_exclusions.should_exclude_file` with
    *tool_type*. Empty scope yields ``None``.
    """
    try:
        from .standard_exclusions import should_exclude_file

        root = Path(project_root).resolve()
        sig = hashlib.sha256()
        paths: list[Path] = []
        seen: set[str] = set()
        for raw in rel_roots:
            s = str(raw).strip().replace("\\", "/")
            if not s or s.startswith("/") or ".." in s.split("/"):
                continue
            p = (root / s).resolve()
            try:
                rel_check = str(p.relative_to(root)).replace("\\", "/")
            except ValueError:
                continue
            if p.is_file():
                if p.suffix != ".py":
                    continue
                if should_exclude_file(rel_check, tool_type=tool_type):
                    continue
                if rel_check not in seen:
                    seen.add(rel_check)
                    paths.append(p)
            elif p.is_dir():
                for f in sorted(p.rglob("*.py")):
                    r = str(f.relative_to(root)).replace("\\", "/")
                    if should_exclude_file(r, tool_type=tool_type):
                        continue
                    if r not in seen:
                        seen.add(r)
                        paths.append(f)
        paths.sort(key=lambda x: str(x))
        if not paths:
            return None
        for p in paths:
            _update_sig_with_py_file(sig, root, p)
        return sig.hexdigest()
    except Exception:
        return None


def compute_full_repo_py_source_signature(
    project_root: Path, *, tool_type: str = "analysis"
) -> str | None:
    """SHA-256 over all non-excluded ``*.py`` files under *project_root* (Python half only)."""
    try:
        from .standard_exclusions import should_exclude_file

        root = Path(project_root).resolve()
        sig = hashlib.sha256()
        py_files = sorted(root.rglob("*.py"))
        any_file = False
        for p in py_files:
            try:
                rel = str(p.relative_to(root)).replace("\\", "/")
                if should_exclude_file(rel, tool_type=tool_type):
                    continue
                any_file = True
                _update_sig_with_py_file(sig, root, p)
            except (OSError, ValueError):
                continue
        return sig.hexdigest() if any_file else None
    except Exception:
        return None


def compute_full_static_check_source_signature(project_root: Path) -> str | None:
    """Full static-check invalidation hash (all non-excluded ``*.py`` + config files).

    Matches historical :meth:`ToolWrappersMixin._compute_source_signature` output.
    """
    try:
        from .standard_exclusions import should_exclude_file

        sig = hashlib.sha256()
        root = Path(project_root).resolve()
        py_files = sorted(root.rglob("*.py"))
        for p in py_files:
            try:
                rel = str(p.relative_to(root)).replace("\\", "/")
                if should_exclude_file(rel, tool_type="analysis"):
                    continue
                _update_sig_with_py_file(sig, root, p)
            except (OSError, ValueError):
                continue
        for rel in STATIC_CHECK_CONFIG_RELATIVE_PATHS:
            cfg = root / rel
            if cfg.is_file():
                sig.update(rel.encode("utf-8"))
                sig.update(b"\0")
                sig.update(cfg.read_bytes())
        return sig.hexdigest()
    except Exception:
        return None
