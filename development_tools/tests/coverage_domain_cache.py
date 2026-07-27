"""Dev-tools domain/coverage cache mtime helpers (V6 B-015).

Extracted from ``run_test_coverage.CoverageMetricsRegenerator`` so cache
invalidation logic can be tested without the full regenerator graph.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from development_tools.shared.standard_exclusions import should_exclude_file


def get_dev_tools_source_mtimes(project_root: Path) -> dict[str, float]:
    """Get modification times for Python files under ``development_tools/``."""
    mtimes: dict[str, float] = {}
    root = Path(project_root).resolve()
    dev_tools_dir = root / "development_tools"
    if not dev_tools_dir.exists():
        return mtimes

    for py_file in dev_tools_dir.rglob("*.py"):
        # Skip actual test files (files with test_ prefix) and cache directories.
        # But DO include tool files like run_test_coverage.py even if under tests/.
        if py_file.name.startswith("test_") or ".coverage_cache" in py_file.parts:
            continue
        try:
            rel_path = str(py_file.relative_to(root))
            if should_exclude_file(
                rel_path.replace("\\", "/"),
                tool_type="analysis",
                context="development",
            ):
                continue
            mtimes[rel_path] = py_file.stat().st_mtime
        except OSError:
            continue

    return mtimes


def get_dev_tools_test_mtimes(project_root: Path) -> dict[str, float]:
    """Get current mtimes for development_tools test files."""
    mtimes: dict[str, float] = {}
    root = Path(project_root).resolve()
    tests_dir = root / "tests" / "development_tools"
    if not tests_dir.exists():
        return mtimes
    for test_file in tests_dir.rglob("test_*.py"):
        try:
            rel_path = str(test_file.relative_to(root))
            if should_exclude_file(
                rel_path.replace("\\", "/"),
                tool_type="analysis",
                context="development",
            ):
                continue
            mtimes[rel_path] = test_file.stat().st_mtime
        except OSError:
            continue
    return mtimes


def get_config_mtime(project_root: Path) -> float | None:
    """Get current development_tools_config.json mtime if available."""
    root = Path(project_root).resolve()
    try:
        import development_tools.config.config as config_module

        if (
            hasattr(config_module, "_config_file_path")
            and config_module._config_file_path
        ):
            config_path = Path(config_module._config_file_path)
        else:
            config_path = (
                root
                / "development_tools"
                / "config"
                / "development_tools_config.json"
            )
        if config_path.exists():
            return config_path.stat().st_mtime
    except Exception:
        return None
    return None


def check_dev_tools_changed(
    *,
    use_domain_cache: bool,
    dev_tools_cache: Any | None,
    project_root: Path,
    log: Any | None = None,
) -> bool:
    """Return True when development_tools sources/tests/config invalidate the cache."""
    if not use_domain_cache or not dev_tools_cache:
        return True  # If caching disabled, always consider changed

    tool_change_reason = dev_tools_cache.get_tool_change_reason()
    if tool_change_reason:
        if log:
            log.info(f"Dev tools coverage cache invalidation: {tool_change_reason}")
        return True

    current_config_mtime = get_config_mtime(project_root)
    cached_config_mtime = dev_tools_cache.get_cached_config_mtime()
    if current_config_mtime is not None:
        if cached_config_mtime is None:
            if log:
                log.info(
                    "Config mtime missing from dev tools coverage cache - invalidating cache"
                )
            return True
        if current_config_mtime != cached_config_mtime:
            if log:
                log.info(
                    "Config file changed - invalidating dev tools coverage cache"
                )
            return True

    last_run_ok = dev_tools_cache.get_last_run_ok()
    if last_run_ok is False:
        if log:
            log.info(
                "Previous dev tools coverage run failed - invalidating dev tools coverage cache"
            )
        return True

    current_mtimes = get_dev_tools_source_mtimes(project_root)
    cached_mtimes = dev_tools_cache.get_cached_mtimes()
    if not cached_mtimes:
        return True  # No cache exists - consider it changed

    for file_path, current_mtime in current_mtimes.items():
        cached_mtime = cached_mtimes.get(file_path)
        if cached_mtime is None or current_mtime != cached_mtime:
            return True

    for file_path in cached_mtimes:
        if file_path not in current_mtimes:
            return True

    current_test_mtimes = get_dev_tools_test_mtimes(project_root)
    cached_test_mtimes = dev_tools_cache.get_cached_test_mtimes()
    if not cached_test_mtimes:
        return True
    for file_path, current_mtime in current_test_mtimes.items():
        cached_mtime = cached_test_mtimes.get(file_path)
        if cached_mtime is None or current_mtime != cached_mtime:
            return True
    return any(file_path not in current_test_mtimes for file_path in cached_test_mtimes)
