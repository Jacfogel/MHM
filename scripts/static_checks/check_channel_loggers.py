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
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
LOG_METHODS = {"debug", "info", "warning", "error", "exception", "critical"}

EXCLUDED_DIRS = {"tests", "scripts", "ai_tools", "development_tools"}
ALLOWED_LOGGING_IMPORT_PATHS = {
    Path("core/logger.py"),
    Path("core/error_handling.py"),
    Path("core/service.py"),
    Path("run_tests.py"),
}


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
        tree = ast.parse(path.read_text())
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


def main() -> int:
    python_files = [p for p in REPO_ROOT.rglob("*.py") if p.is_file()]
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
