#!/usr/bin/env python3
# TOOL_TIER: supporting
# TOOL_PORTABILITY: portable

"""
Development-tools import boundary checker.

Ensures modules under development_tools/** do not import core.* (or other business packages).
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from development_tools.shared.logging import get_dev_tools_logger

try:
    from .. import config
    from ..shared.standard_exclusions import should_exclude_file
except ImportError:
    from development_tools import config  # type: ignore
    from development_tools.shared.standard_exclusions import (  # type: ignore
        should_exclude_file,
    )


logger = get_dev_tools_logger("development_tools")


class DevToolsImportBoundaryChecker:
    """Analyze imports inside development_tools for boundary violations."""

    def __init__(self, project_root_path: str | None = None) -> None:
        if project_root_path:
            self.project_root = Path(project_root_path).resolve()
        else:
            self.project_root = Path(config.get_project_root()).resolve()

        self.dev_tools_root = self.project_root / "development_tools"

    def _iter_dev_tools_files(self) -> list[Path]:
        """Yield Python files under development_tools respecting exclusions."""
        if not self.dev_tools_root.exists():
            return []

        results: list[Path] = []
        for py_file in self.dev_tools_root.rglob("*.py"):
            rel = py_file.relative_to(self.project_root)
            rel_str = str(rel).replace("\\", "/")
            if should_exclude_file(rel_str, tool_type="analysis", context="development"):
                continue
            results.append(py_file)
        return results

    def _extract_import_modules(self, file_path: Path) -> list[str]:
        """Return fully qualified modules imported in file."""
        modules: list[str] = []
        try:
            text = file_path.read_text(encoding="utf-8")
            tree = ast.parse(text, filename=str(file_path))
        except Exception as exc:
            logger.debug(f"Skipping {file_path} due to parse error: {exc}", exc_info=True)
            return modules

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name:
                        modules.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    modules.append(node.module)
        return modules

    def _is_dev_tools_file(self, rel_path: str) -> bool:
        return rel_path.startswith("development_tools/")

    def analyze(self) -> dict[str, Any]:
        """Return standard-format result with import-boundary violations."""
        violations: list[dict[str, str]] = []

        files = self._iter_dev_tools_files()
        for file_path in files:
            rel = file_path.relative_to(self.project_root)
            rel_str = str(rel).replace("\\", "/")

            imported_modules = self._extract_import_modules(file_path)
            for module_name in imported_modules:
                if module_name.startswith("core."):
                    violations.append(
                        {
                            "file": rel_str,
                            "module": module_name,
                            "reason": "core package import inside development_tools",
                        }
                    )

        summary = {
            "total_violations": len(violations),
            "files_with_violations": len({v["file"] for v in violations}),
        }

        result: dict[str, Any] = {
            "summary": {
                "total_issues": summary["total_violations"],
                "files_affected": summary["files_with_violations"],
            },
            "details": {
                "violations": violations,
                "summary": summary,
            },
        }
        return result


def main() -> int:
    """CLI entry point."""
    checker = DevToolsImportBoundaryChecker()
    result = checker.analyze()

    total = result["summary"]["total_issues"]
    files = result["summary"]["files_affected"]

    logger.debug(
        f"Development-tools import boundary check: {total} violation(s) across {files} file(s)"
    )

    for violation in result["details"]["violations"]:
        logger.warning(
            f"[IMPORT-BOUNDARY] {violation['file']} imports {violation['module']}: {violation['reason']}"
        )

    # Print JSON to stdout for audit orchestration if needed
    import json as _json

    print(_json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
