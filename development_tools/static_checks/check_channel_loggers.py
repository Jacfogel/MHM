"""
Static logging style enforcement for MHM.

Rules enforced (fail on violation):
- Application code must not import `logging` directly or call `logging.getLogger(...)`.
  Allowed: tests/, scripts/, ai_tools/, development_tools/, and explicit allowlist files.
- Logger calls must use a single positional argument (favor f-strings instead of printf-style formatting).

This script is intended for CI/automation usage and is idempotent.
"""
from __future__ import annotations

import ast
import sys
import os
import importlib.util
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
LOG_METHODS = {"debug", "info", "warning", "error", "exception", "critical"}

EXCLUDED_DIRS = {"tests", "scripts", "ai_tools", "development_tools"}
IGNORED_DIR_NAMES = {
    ".git",
    ".venv",
    "venv",
    ".pytest_runtime",
    "tmp_pytest_runtime",
    ".pytest_cache",
    ".pytest_profile_cache",
    ".pytest_profile_tmp",
    ".pytest_tmp_cache",
    ".tmp_pytest_runner",
    ".tmp_pytest",
    ".tmp_devtools_pyfiles",
    "htmlcov",
    "mhm.egg-info",
}
ALLOWED_LOGGING_IMPORT_PATHS = {
    Path("core/logger.py"),
    Path("core/error_handling.py"),
    Path("core/service.py"),
    Path("run_tests.py"),
}


def _load_should_exclude_file():
    """Load standard exclusions helper without importing development_tools package."""
    module_path = REPO_ROOT / "development_tools" / "shared" / "standard_exclusions.py"
    try:
        spec = importlib.util.spec_from_file_location(
            "_mhm_standard_exclusions", module_path
        )
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Unable to load exclusions helper from {module_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return getattr(module, "should_exclude_file")
    except Exception:
        # Keep logging enforcement runnable in isolated CI environments where
        # optional runtime dependencies for full dev-tools config are unavailable.
        def _fallback_should_exclude_file(
            file_path: str, tool_type: str | None = None, context: str = "development"
        ) -> bool:
            normalized = str(file_path).replace("\\", "/")
            fallback_fragments = (
                "__pycache__",
                ".git/",
                ".venv/",
                "venv/",
                ".pytest_cache/",
                ".pytest_runtime/",
                ".tmp_pytest",
                ".tmp_devtools_pyfiles",
                "htmlcov/",
                "mhm.egg-info/",
            )
            return any(fragment in normalized for fragment in fallback_fragments)

        return _fallback_should_exclude_file


should_exclude_file = _load_should_exclude_file()


def is_excluded(path: Path) -> bool:
    return any(part in EXCLUDED_DIRS for part in path.parts)


def has_logger_name(node: ast.AST) -> bool:
    current = node
    while isinstance(current, ast.Attribute):
        if current.attr.lower().endswith("logger"):
            return True
        current = current.value
    return isinstance(current, ast.Name) and current.id.lower().endswith("logger")


def format_issue(rel_path: Path, lineno: int, message: str) -> str:
    return f"{rel_path}:{lineno}: {message}"


def check_file(path: Path) -> Iterable[str]:
    rel_path = path.relative_to(REPO_ROOT)
    if is_excluded(rel_path):
        return []

    allow_logging_imports = rel_path in ALLOWED_LOGGING_IMPORT_PATHS

    try:
        tree = ast.parse(path.read_text(encoding='utf-8'))
    except SyntaxError as exc:  # pragma: no cover - script should fail loudly
        return [format_issue(rel_path, exc.lineno or 0, f"Failed to parse file: {exc}")]

    issues = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "logging" and not allow_logging_imports:
                    issues.append(format_issue(rel_path, node.lineno, "Direct logging import is forbidden; use core.logger"))
        elif isinstance(node, ast.ImportFrom):
            if node.module == "logging" and not allow_logging_imports:
                issues.append(format_issue(rel_path, node.lineno, "Direct logging import is forbidden; use core.logger"))
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute):
                # logging.getLogger(...)
                if (
                    isinstance(func.value, ast.Name)
                    and func.value.id == "logging"
                    and func.attr == "getLogger"
                    and not allow_logging_imports
                ):
                    issues.append(format_issue(rel_path, node.lineno, "Use core.logger.get_component_logger instead of logging.getLogger"))
                # logger.info/debug/etc positional arg enforcement
                elif func.attr in LOG_METHODS and has_logger_name(func.value) and len(node.args) > 1:
                    issues.append(
                        format_issue(
                            rel_path,
                            node.lineno,
                            "Logger calls should use a single positional argument (prefer f-strings over printf formatting)",
                        )
                    )
    return issues


def iter_python_files(root: Path) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = Path(dirpath).relative_to(root)
        dirnames[:] = [
            name
            for name in dirnames
            if name not in IGNORED_DIR_NAMES
            and not is_excluded(rel_dir / name)
            and not should_exclude_file(
                str((rel_dir / name).as_posix()),
                tool_type="analysis",
                context="development",
            )
        ]
        for filename in filenames:
            if filename.endswith(".py"):
                rel_file = (rel_dir / filename).as_posix()
                if should_exclude_file(
                    rel_file, tool_type="analysis", context="development"
                ):
                    continue
                yield Path(dirpath) / filename


def main() -> int:
    python_files = [p for p in iter_python_files(REPO_ROOT) if p.is_file()]
    violations = []

    for file_path in sorted(python_files):
        violations.extend(check_file(file_path))

    if violations:
        print("Static logging check failed. Resolve the issues below:\n")
        for violation in violations:
            print(f"- {violation}")
        return 1

    print("Static check passed: no forbidden logger usage detected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
